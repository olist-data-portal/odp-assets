import io

import pandas as pd
from dagster import Config, EnvVar, asset, get_dagster_logger
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound

from olist_data_portal.assets.file_config import (
    ALL_OLIST_FILES,
    FILE_CONFIGS,
    FileConfig,
)
from olist_data_portal.assets.kaggle_api_to_gcs import get_kaggle_asset_by_filename
from olist_data_portal.assets.utils import (
    get_asset_name_from_filename,
    get_bigquery_asset_metadata,
    get_table_name,
    get_variable_name_from_filename,
)
from olist_data_portal.resources import BigQueryResource, GcsResource


class GcsToBigqueryConfig(Config):
    """GCSからBigQueryへのデータロード設定"""

    gcs_bucket_name: str = "odp-data-lake"
    gcs_prefix: str = "olist-brazilian-ecommerce"
    bigquery_dataset_name: str = "data_lake"
    execution_date: str = "2016-10-01"
    gcp_project_id: str = EnvVar("GCP_PROJECT_ID")


def _load_file_to_bigquery(
    bigquery_client: bigquery.Client,
    bucket: storage.Bucket,
    filename: str,
    gcs_blob_name: str,
    table_id: str,
    table_name: str,
    target_date: pd.Timestamp | None,
    file_config: FileConfig,
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

        if file_config.is_incremental and target_date is not None:
            df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
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
                bigquery_client.get_table(table_id)
                table_exists = True
                delete_query = f"""
                DELETE FROM `{table_id}`
                WHERE SAFE_CAST(order_purchase_timestamp AS TIMESTAMP) <= TIMESTAMP('{target_date.isoformat()}')
                """
                bigquery_client.query(delete_query).result()
                logger.info(f"Deleted existing data before {target_date.date()} from {table_name}")
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
            logger.info(f"{filename} (Incremental): Loaded {len(df_filtered)} rows to {table_name}")
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

            job = bigquery_client.load_table_from_dataframe(df, table_id, job_config=job_config)
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


def _create_gcs_to_bigquery_asset(filename: str):
    """GCSからBigQueryへのアセットを生成"""
    file_config = FILE_CONFIGS[filename]
    asset_name = get_asset_name_from_filename(filename, "raw")
    kaggle_asset = get_kaggle_asset_by_filename(filename)
    table_name = get_table_name(filename)
    # table_idは実行時に決定されるため、プレースホルダーを使用
    table_id_placeholder = "{project_id}.{dataset}.{table_name}"

    @asset(
        name=asset_name,
        group_name="gcs_to_bigquery",
        description=file_config.description,
        deps=[kaggle_asset],
        metadata=get_bigquery_asset_metadata(file_config, table_name, table_id_placeholder),
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
            if file_config.is_incremental
            else None
        )

        gcs_blob_name = f"{config.gcs_prefix}/raw/{filename}"
        table_id = f"{config.gcp_project_id}.{config.bigquery_dataset_name}.{table_name}"

        result = _load_file_to_bigquery(
            bigquery_client,
            bucket,
            filename,
            gcs_blob_name,
            table_id,
            table_name,
            target_date,
            file_config,
            logger,
        )
        result["execution_date"] = config.execution_date
        return result

    return asset_func


for filename in ALL_OLIST_FILES:
    variable_name = get_variable_name_from_filename(filename, "gcs")
    globals()[variable_name] = _create_gcs_to_bigquery_asset(filename)
