import kagglehub
import pandas as pd
from dagster import EnvVar, asset, Config, get_dagster_logger
from google.cloud import storage


class KaggleToGcsConfig(Config):
    """Kaggle APIからGCSへのデータ取得設定"""

    dataset_name: str = "olistbr/brazilian-ecommerce"
    gcs_bucket_name: str = "odp-data-lake"
    gcs_prefix: str = "olist-brazilian-ecommerce"
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


@asset(name="kaggle_to_gcs")
def kaggle_to_gcs(config: KaggleToGcsConfig):
    logger = get_dagster_logger()

    # 1. データセットのダウンロード
    dataset_path = kagglehub.dataset_download(config.dataset_name)
    logger.info(f"Successfully downloaded dataset to {dataset_path}")

    # 2. GCSクライアントの準備
    storage_client = storage.Client(project=config.gcp_project_id)
    bucket = storage_client.bucket(config.gcs_bucket_name)
    # execution_dateの日付の終了時刻（23:59:59.999999）まで含める
    target_date = pd.to_datetime(config.execution_date) + pd.Timedelta(days=1)

    # 3. 全てのファイルをループで処理
    for filename in ALL_OLIST_FILES:
        file_path = f"{dataset_path}/{filename}"

        df = pd.read_csv(file_path)
        gcs_blob_name = f"{config.gcs_prefix}/raw/{filename}"

        if filename == "olist_orders_dataset.csv":
            # 注文データ: インクリメンタル処理を適用
            df["order_purchase_timestamp"] = pd.to_datetime(
                df["order_purchase_timestamp"]
            )
            # 実行日以前のデータを全てフィルタリング（timestamp型のまま比較）
            df_filtered = df[df["order_purchase_timestamp"] <= target_date]

            # GCSにアップロード
            temp_upload_path = f"{dataset_path}/filtered_{filename}"
            df_filtered.to_csv(temp_upload_path, index=False)
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_filename(temp_upload_path)
            logger.info(
                f"ORDERS (Incremental): Uploaded {len(df_filtered)} rows to {gcs_blob_name}"
            )

        else:
            # 補助データ: フィルタリングせず全件アップロード（毎回上書き）
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_filename(file_path)
            logger.info(
                f"AUXILIARY: Uploaded all data for {filename} to {gcs_blob_name}"
            )

    logger.info("Dataset download completed")

    return config.execution_date
