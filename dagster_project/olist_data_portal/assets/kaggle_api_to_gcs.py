import kagglehub
import pandas as pd
from dagster import EnvVar, asset, Config, get_dagster_logger
from google.cloud import storage

from olist_data_portal.resources import GcsResource


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

ORDERS_FILE = "olist_orders_dataset.csv"


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
    return f"kaggle_{file_basename}_to_gcs"


@asset(
    name="kaggle_dataset_download",
    group_name="kaggle_to_gcs",
    description="Kaggleデータセットをダウンロード",
    metadata={
        # データ資産の基本情報
        "data_source": "kaggle",
        "source_dataset": "olistbr/brazilian-ecommerce",
        "data_layer": "source",
        "data_format": "csv",
        # ビジネス情報
        "business_domain": "ecommerce",
        "business_unit": "olist",
        "country": "brazil",
        # 技術情報
        "download_method": "kagglehub",
        "asset_version": "1.0",
    },
)
def kaggle_dataset_download(config: KaggleToGcsConfig) -> dict:
    """Kaggleデータセットをダウンロード"""
    logger = get_dagster_logger()
    dataset_path = kagglehub.dataset_download(config.dataset_name)
    logger.info(f"Successfully downloaded dataset to {dataset_path}")
    return {
        "dataset_path": dataset_path,
        "dataset_name": config.dataset_name,
        "execution_date": config.execution_date,
    }


def _upload_file_to_gcs(
    dataset_path: str,
    filename: str,
    bucket: storage.Bucket,
    gcs_blob_name: str,
    target_date: pd.Timestamp | None,
    logger,
) -> dict:
    """ファイルをGCSにアップロード"""
    try:
        if filename == ORDERS_FILE and target_date is not None:
            df = pd.read_csv(f"{dataset_path}/{filename}")
            df["order_purchase_timestamp"] = pd.to_datetime(
                df["order_purchase_timestamp"]
            )
            df_filtered = df[df["order_purchase_timestamp"] <= target_date]

            temp_upload_path = f"{dataset_path}/filtered_{filename}"
            df_filtered.to_csv(temp_upload_path, index=False)
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_filename(temp_upload_path)
            logger.info(
                f"ORDERS (Incremental): Uploaded {len(df_filtered)} rows to {gcs_blob_name}"
            )
            return {
                "filename": filename,
                "rows_uploaded": len(df_filtered),
                "gcs_path": gcs_blob_name,
                "processing_type": "incremental",
            }
        else:
            file_path = f"{dataset_path}/{filename}"
            df = pd.read_csv(file_path)
            blob = bucket.blob(gcs_blob_name)
            blob.upload_from_filename(file_path)
            logger.info(
                f"AUXILIARY: Uploaded all data for {filename} to {gcs_blob_name}"
            )
            return {
                "filename": filename,
                "rows_uploaded": len(df),
                "gcs_path": gcs_blob_name,
                "processing_type": "full_load",
            }
    except Exception as e:
        logger.error(f"Failed to upload {filename} to GCS: {e}")
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


def _get_asset_metadata(filename: str) -> dict:
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
        "data_format": "csv",
        "data_source": "kaggle",
        "source_dataset": "olistbr/brazilian-ecommerce",
        # 処理情報
        "processing_type": "incremental" if is_incremental else "full_load",
        "update_frequency": "daily" if is_incremental else "on_demand",
        # データ品質
        "data_quality": "raw",
        "schema_evolution": "allowed",
        # ビジネス情報
        "business_domain": "ecommerce",
        "business_unit": "olist",
        "country": "brazil",
        # 技術情報
        "storage_location": "gcs",
        "storage_format": "csv",
        "compression": "none",
        # メタデータ情報
        "filename": filename,
        "asset_version": "1.0",
    }


def _create_kaggle_to_gcs_asset(filename: str):
    """KaggleからGCSへのアセットを生成"""
    asset_name = _get_asset_name_from_filename(filename, "csv")
    description = f"{_get_file_description(filename)}をKaggleからGCSにアップロード"
    metadata = _get_asset_metadata(filename)

    @asset(
        name=asset_name,
        group_name="kaggle_to_gcs",
        description=description,
        deps=[kaggle_dataset_download],
        metadata=metadata,
    )
    def asset_func(
        config: KaggleToGcsConfig,
        kaggle_dataset_download: dict,
        gcs: GcsResource,
    ):
        logger = get_dagster_logger()
        bucket = gcs.get_bucket(config.gcs_bucket_name)
        target_date = (
            pd.to_datetime(config.execution_date) + pd.Timedelta(days=1)
            if filename == ORDERS_FILE
            else None
        )

        gcs_blob_name = f"{config.gcs_prefix}/raw/{filename}"
        result = _upload_file_to_gcs(
            kaggle_dataset_download["dataset_path"],
            filename,
            bucket,
            gcs_blob_name,
            target_date,
            logger,
        )
        result["execution_date"] = config.execution_date
        return result

    return asset_func


for filename in ALL_OLIST_FILES:
    variable_name = _get_variable_name_from_filename(filename)
    globals()[variable_name] = _create_kaggle_to_gcs_asset(filename)


def get_kaggle_asset_by_filename(filename: str):
    """ファイル名からKaggleアセットを取得"""
    variable_name = _get_variable_name_from_filename(filename)
    return globals()[variable_name]
