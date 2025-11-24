import io

import pandas as pd
from dagster import Config, EnvVar, asset, get_dagster_logger
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound

from olist_data_portal.assets.kaggle_api_to_gcs import (
    ALL_OLIST_FILES,
    ORDERS_FILE,
    get_kaggle_asset_by_filename,
)
from olist_data_portal.resources import BigQueryResource, GcsResource


def _get_asset_name_from_filename(filename: str, prefix: str = "") -> str:
    """ファイル名からアセット名を生成"""
    file_basename = filename.replace(".csv", "")
    # _datasetサフィックスを削除
    if file_basename.endswith("_dataset"):
        file_basename = file_basename[:-8]
    if prefix:
        return f"{prefix}__{file_basename}"
    return file_basename


def _get_variable_name_from_filename(filename: str) -> str:
    """ファイル名から変数名を生成"""
    file_basename = filename.replace(".csv", "")
    # _datasetサフィックスを削除
    if file_basename.endswith("_dataset"):
        file_basename = file_basename[:-8]
    # olist_プレフィックスを削除
    if file_basename.startswith("olist_"):
        file_basename = file_basename[6:]
    return f"gcs_{file_basename}_to_bigquery"


class GcsToBigqueryConfig(Config):
    """GCSからBigQueryへのデータロード設定"""

    gcs_bucket_name: str = "odp-data-lake"
    gcs_prefix: str = "olist-brazilian-ecommerce"
    bigquery_dataset_name: str = "data_lake"
    execution_date: str = "2016-10-01"
    gcp_project_id: str = EnvVar("GCP_PROJECT_ID")


def _get_table_name(filename: str) -> str:
    """ファイル名からBigQueryテーブル名を生成"""
    file_basename = filename.replace(".csv", "")
    return f"raw__{file_basename}"


def _load_file_to_bigquery(
    bigquery_client: bigquery.Client,
    bucket: storage.Bucket,
    filename: str,
    gcs_blob_name: str,
    table_id: str,
    table_name: str,
    target_date: pd.Timestamp | None,
    logger,
) -> dict:
    """ファイルをBigQueryにロード"""
    try:
        blob = bucket.blob(gcs_blob_name)
        if not blob.exists():
            logger.warning(f"File not found in GCS: {gcs_blob_name}, skipping...")
            raise FileNotFoundError(f"File not found in GCS: {gcs_blob_name}")

        csv_content = blob.download_as_text()
        df = pd.read_csv(io.StringIO(csv_content))

        if filename == ORDERS_FILE and target_date is not None:
            df["order_purchase_timestamp"] = pd.to_datetime(
                df["order_purchase_timestamp"]
            )
            df_filtered = df[df["order_purchase_timestamp"] <= target_date]

            if len(df_filtered) == 0:
                logger.info(f"No data to load for {filename}, skipping...")
                return {
                    "filename": filename,
                    "table_name": table_name,
                    "rows_loaded": 0,
                    "processing_type": "incremental",
                    "status": "skipped",
                }

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

            if table_exists:
                job_config = bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                    autodetect=False,
                )
            else:
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
            return {
                "filename": filename,
                "table_name": table_name,
                "table_id": table_id,
                "rows_loaded": len(df_filtered),
                "processing_type": "incremental",
                "status": "success",
            }
        else:
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
            return {
                "filename": filename,
                "table_name": table_name,
                "table_id": table_id,
                "rows_loaded": len(df),
                "processing_type": "full_load",
                "status": "success",
            }
    except Exception as e:
        logger.error(f"Failed to load {filename} to BigQuery: {e}")
        raise


def _get_file_description(filename: str) -> str:
    """ファイル名から説明を生成"""
    descriptions = {
        "olist_orders_dataset.csv": "注文データ",
        "olist_customers_dataset.csv": "顧客データ",
        "olist_geolocation_dataset.csv": "地理情報データ",
        "olist_order_items_dataset.csv": "注文アイテムデータ",
        "olist_order_payments_dataset.csv": "注文支払いデータ",
        "olist_order_reviews_dataset.csv": "注文レビューデータ",
        "olist_products_dataset.csv": "商品データ",
        "olist_sellers_dataset.csv": "販売者データ",
        "product_category_name_translation.csv": "商品カテゴリ翻訳データ",
    }
    return descriptions.get(filename, f"{filename}のデータ")


def _get_asset_metadata(filename: str, table_name: str, table_id: str) -> dict:
    """ファイル名からアセット指向のメタデータを生成"""
    # データドメインの抽出
    domain_map = {
        "olist_orders_dataset.csv": "orders",
        "olist_customers_dataset.csv": "customers",
        "olist_geolocation_dataset.csv": "geolocation",
        "olist_order_items_dataset.csv": "order_items",
        "olist_order_payments_dataset.csv": "payments",
        "olist_order_reviews_dataset.csv": "reviews",
        "olist_products_dataset.csv": "products",
        "olist_sellers_dataset.csv": "sellers",
        "product_category_name_translation.csv": "product_categories",
    }

    # データタイプの分類
    data_type_map = {
        "olist_orders_dataset.csv": "transactional",
        "olist_customers_dataset.csv": "master",
        "olist_geolocation_dataset.csv": "reference",
        "olist_order_items_dataset.csv": "transactional",
        "olist_order_payments_dataset.csv": "transactional",
        "olist_order_reviews_dataset.csv": "transactional",
        "olist_products_dataset.csv": "master",
        "olist_sellers_dataset.csv": "master",
        "product_category_name_translation.csv": "reference",
    }

    domain = domain_map.get(filename, "unknown")
    data_type = data_type_map.get(filename, "unknown")
    is_incremental = filename == ORDERS_FILE

    return {
        # データ資産の基本情報
        "data_domain": domain,
        "data_type": data_type,
        "data_layer": "raw",
        "data_format": "bigquery_table",
        "data_source": "gcs",
        "source_format": "csv",
        # 処理情報
        "processing_type": "incremental" if is_incremental else "full_load",
        "update_frequency": "daily" if is_incremental else "on_demand",
        "write_disposition": "append" if is_incremental else "truncate",
        # データ品質
        "data_quality": "raw",
        "schema_evolution": "allowed",
        "schema_autodetect": True,
        # ビジネス情報
        "business_domain": "ecommerce",
        "business_unit": "olist",
        "country": "brazil",
        # 技術情報
        "storage_location": "bigquery",
        "storage_format": "table",
        "table_name": table_name,
        "table_id": table_id,
        "database": "bigquery",
        # メタデータ情報
        "filename": filename,
        "asset_version": "1.0",
    }


def _create_gcs_to_bigquery_asset(filename: str):
    """GCSからBigQueryへのアセットを生成"""
    asset_name = _get_asset_name_from_filename(filename, "raw")
    kaggle_asset = get_kaggle_asset_by_filename(filename)
    description = f"{_get_file_description(filename)}をGCSからBigQueryにロード"
    table_name = _get_table_name(filename)
    # table_idは実行時に決定されるため、プレースホルダーを使用
    table_id_placeholder = "{project_id}.{dataset}.{table_name}"

    @asset(
        name=asset_name,
        group_name="gcs_to_bigquery",
        description=description,
        deps=[kaggle_asset],
        metadata=_get_asset_metadata(filename, table_name, table_id_placeholder),
    )
    def asset_func(
        config: GcsToBigqueryConfig,
        bigquery: BigQueryResource,
        gcs: GcsResource,
    ):
        logger = get_dagster_logger()
        bigquery_client = bigquery.get_client()
        bucket = gcs.get_bucket(config.gcs_bucket_name)
        target_date = (
            pd.to_datetime(config.execution_date) + pd.Timedelta(days=1)
            if filename == ORDERS_FILE
            else None
        )

        gcs_blob_name = f"{config.gcs_prefix}/raw/{filename}"
        table_id = (
            f"{config.gcp_project_id}.{config.bigquery_dataset_name}.{table_name}"
        )

        result = _load_file_to_bigquery(
            bigquery_client,
            bucket,
            filename,
            gcs_blob_name,
            table_id,
            table_name,
            target_date,
            logger,
        )
        result["execution_date"] = config.execution_date
        return result

    return asset_func


for filename in ALL_OLIST_FILES:
    variable_name = _get_variable_name_from_filename(filename)
    globals()[variable_name] = _create_gcs_to_bigquery_asset(filename)
