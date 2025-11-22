import os
import logging
import shutil
from pathlib import Path
from typing import Any

from dagster import asset, Config
from google.cloud import storage
from kaggle.api.kaggle_api_extended import KaggleApi

logger = logging.getLogger(__name__)


class KaggleToGcsConfig(Config):
    """Kaggle APIからGCSへのデータ取得設定"""

    dataset_name: str = "olist/brazilian-ecommerce"
    gcs_bucket_name: str
    gcs_prefix: str = "kaggle/olist-brazilian-ecommerce"


@asset(name="kaggle_to_gcs")
def kaggle_to_gcs(config: KaggleToGcsConfig) -> dict[str, Any]:
    """
    Kaggle APIからデータセットをダウンロードし、GCSにアップロードする。

    Args:
        config: KaggleToGcsConfig設定オブジェクト

    Returns:
        アップロードされたファイルの情報を含む辞書
    """
    kaggle_username = os.getenv("KAGGLE_USERNAME")
    kaggle_key = os.getenv("KAGGLE_KEY")

    if not kaggle_username or not kaggle_key:
        raise ValueError(
            "KAGGLE_USERNAME and KAGGLE_KEY environment variables must be set"
        )

    api = KaggleApi()
    api.authenticate()

    temp_dir = Path("/tmp/kaggle_download")
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Downloading dataset: {config.dataset_name}")
        api.dataset_download_files(config.dataset_name, path=str(temp_dir), unzip=True)

        storage_client = storage.Client()
        bucket = storage_client.bucket(config.gcs_bucket_name)

        uploaded_files = []
        csv_files = list(temp_dir.glob("*.csv"))

        if not csv_files:
            raise ValueError(f"No CSV files found in dataset: {config.dataset_name}")

        for csv_file in csv_files:
            blob_name = f"{config.gcs_prefix}/{csv_file.name}"
            blob = bucket.blob(blob_name)

            logger.info(
                f"Uploading {csv_file.name} to gs://{config.gcs_bucket_name}/{blob_name}"
            )
            blob.upload_from_filename(str(csv_file))

            uploaded_files.append(
                {
                    "file_name": csv_file.name,
                    "gcs_path": f"gs://{config.gcs_bucket_name}/{blob_name}",
                    "size": csv_file.stat().st_size,
                }
            )

        logger.info(f"Successfully uploaded {len(uploaded_files)} files to GCS")

        return {
            "dataset_name": config.dataset_name,
            "uploaded_files": uploaded_files,
            "total_files": len(uploaded_files),
        }

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
