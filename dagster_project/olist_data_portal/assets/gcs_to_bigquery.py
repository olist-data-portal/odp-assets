import io

import pandas as pd
from dagster import Config, EnvVar, asset, get_dagster_logger
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound

from olist_data_portal.assets.kaggle_api_to_gcs import kaggle_to_gcs


class GcsToBigqueryConfig(Config):
    """GCSからBigQueryへのデータロード設定"""

    gcs_bucket_name: str = "odp-data-lake"
    gcs_prefix: str = "olist-brazilian-ecommerce"
    bigquery_dataset_name: str = "data_lake"
    execution_date: str = "2016-10-01"
    gcp_project_id: str = EnvVar("GCP_PROJECT_ID")


ALL_OLIST_FILES = [
    "olist_orders_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def _get_table_name(filename: str) -> str:
    """ファイル名からBigQueryテーブル名を生成"""
    file_basename = filename.replace(".csv", "")
    return f"raw__{file_basename}"


@asset(name="gcs_to_bigquery", deps=[kaggle_to_gcs])
def gcs_to_bigquery(config: GcsToBigqueryConfig):
    logger = get_dagster_logger()

    # BigQueryクライアントの準備
    bigquery_client = bigquery.Client(project=config.gcp_project_id)
    storage_client = storage.Client(project=config.gcp_project_id)
    bucket = storage_client.bucket(config.gcs_bucket_name)

    # 実行日の終了時刻まで含める
    target_date = pd.to_datetime(config.execution_date) + pd.Timedelta(days=1)

    # 全てのファイルをループで処理
    for filename in ALL_OLIST_FILES:
        gcs_blob_name = f"{config.gcs_prefix}/raw/{filename}"
        table_name = _get_table_name(filename)
        table_id = (
            f"{config.gcp_project_id}.{config.bigquery_dataset_name}.{table_name}"
        )

        # GCSからCSVファイルを読み込む
        blob = bucket.blob(gcs_blob_name)
        if not blob.exists():
            logger.warning(f"File not found in GCS: {gcs_blob_name}, skipping...")
            continue

        # CSVを一時的にメモリに読み込む
        csv_content = blob.download_as_text()
        df = pd.read_csv(io.StringIO(csv_content))

        if filename == "olist_orders_dataset.csv":
            # 注文データ: インクリメンタル処理を適用
            df["order_purchase_timestamp"] = pd.to_datetime(
                df["order_purchase_timestamp"]
            )
            df_filtered = df[df["order_purchase_timestamp"] <= target_date]

            if len(df_filtered) == 0:
                logger.info(f"No data to load for {filename}, skipping...")
                continue

            # 既存テーブルから実行日以前のデータを削除
            table_exists = False
            try:
                existing_table = bigquery_client.get_table(table_id)
                table_exists = True
                delete_query = f"""
                DELETE FROM `{table_id}`
                WHERE SAFE_CAST(order_purchase_timestamp AS TIMESTAMP) <= TIMESTAMP('{target_date.isoformat()}')
                """
                bigquery_client.query(delete_query).result()
                logger.info(
                    f"Deleted existing data before {target_date.date()} from {table_name}"
                )
            except NotFound:
                logger.info(f"Table {table_name} does not exist, will create new table")

            # 新しいデータをロード
            if table_exists:
                # 既存テーブルがある場合は追加
                job_config = bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                    autodetect=False,
                )
            else:
                # 新規テーブルの場合はスキーマ自動検出
                job_config = bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                    autodetect=True,
                )
            job = bigquery_client.load_table_from_dataframe(
                df_filtered, table_id, job_config=job_config
            )
            job.result()
            logger.info(
                f"ORDERS (Incremental): Loaded {len(df_filtered)} rows to {table_name}"
            )

        else:
            # 補助データ: 全件上書き
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                autodetect=True,
            )

            job = bigquery_client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()
            logger.info(
                f"AUXILIARY: Loaded {len(df)} rows to {table_name} (truncated and reloaded)"
            )

    logger.info("GCS to BigQuery loading completed")
    return config.execution_date
