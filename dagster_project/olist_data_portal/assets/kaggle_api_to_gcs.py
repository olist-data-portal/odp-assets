import kagglehub
import pandas as pd
from dagster import EnvVar, asset, Config, get_dagster_logger
from google.cloud import storage

from olist_data_portal.assets.file_config import (
    ALL_OLIST_FILES,
    FILE_CONFIGS,
    FileConfig,
    ORDERS_FILE,
)
from olist_data_portal.assets.utils import (
    get_asset_name_from_filename,
    get_kaggle_asset_metadata,
    get_variable_name_from_filename,
)
from olist_data_portal.resources import GcsResource


class KaggleToGcsConfig(Config):
    """Kaggle APIからGCSへのデータ取得設定"""

    dataset_name: str = "olistbr/brazilian-ecommerce"
    gcs_bucket_name: str = "odp-data-lake"
    gcs_prefix: str = "olist-brazilian-ecommerce"
    execution_date: str = "2016-10-01"
    gcp_project_id: str = EnvVar("GCP_PROJECT_ID")


def _upload_file_to_gcs(
    dataset_path: str,
    filename: str,
    bucket: storage.Bucket,
    gcs_blob_name: str,
    target_date: pd.Timestamp | None,
    file_config: FileConfig,
    logger,
) -> dict:
    """ファイルをGCSにアップロード"""
    try:
        if file_config.is_incremental and target_date is not None:
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


def _create_kaggle_to_gcs_asset(filename: str):
    """KaggleからGCSへのアセットを生成"""
    file_config = FILE_CONFIGS[filename]
    asset_name = get_asset_name_from_filename(filename, "csv")
    metadata = get_kaggle_asset_metadata(file_config)

    @asset(
        name=asset_name,
        group_name="kaggle_to_gcs",
        description=file_config.description,
        metadata=metadata,
    )
    def asset_func(
        config: KaggleToGcsConfig,
        gcs: GcsResource,
    ):
        logger = get_dagster_logger()
        try:
            dataset_path = kagglehub.dataset_download(config.dataset_name)
            logger.info(f"Downloaded dataset to {dataset_path}")
        except (FileNotFoundError, OSError, ValueError) as e:
            logger.warning(
                f"Failed to download dataset (cache issue or unsupported archive), "
                f"retrying with force_download: {e}"
            )
            try:
                dataset_path = kagglehub.dataset_download(
                    config.dataset_name, force_download=True
                )
                logger.info(f"Downloaded dataset to {dataset_path} (force download)")
            except Exception as retry_error:
                logger.error(
                    f"Failed to download dataset even with force_download: {retry_error}"
                )
                raise

        bucket = gcs.get_bucket(config.gcs_bucket_name)
        target_date = (
            pd.to_datetime(config.execution_date) + pd.Timedelta(days=1)
            if file_config.is_incremental
            else None
        )

        gcs_blob_name = f"{config.gcs_prefix}/raw/{filename}"
        result = _upload_file_to_gcs(
            dataset_path,
            filename,
            bucket,
            gcs_blob_name,
            target_date,
            file_config,
            logger,
        )
        result["execution_date"] = config.execution_date
        return result

    return asset_func


for filename in ALL_OLIST_FILES:
    variable_name = get_variable_name_from_filename(filename, "kaggle")
    globals()[variable_name] = _create_kaggle_to_gcs_asset(filename)


def get_kaggle_asset_by_filename(filename: str):
    """ファイル名からKaggleアセットを取得"""
    variable_name = get_variable_name_from_filename(filename, "kaggle")
    return globals()[variable_name]
