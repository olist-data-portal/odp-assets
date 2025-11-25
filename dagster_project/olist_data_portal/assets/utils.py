"""アセット生成用の共通ユーティリティ"""

from olist_data_portal.assets.file_config import FileConfig


def get_asset_name_from_filename(filename: str, prefix: str = "") -> str:
    """ファイル名からアセット名を生成"""
    file_basename = filename.replace(".csv", "")
    if file_basename.endswith("_dataset"):
        file_basename = file_basename[:-8]
    if prefix:
        return f"{prefix}__{file_basename}"
    return file_basename


def get_variable_name_from_filename(filename: str, prefix: str) -> str:
    """ファイル名から変数名を生成"""
    file_basename = filename.replace(".csv", "")
    if file_basename.endswith("_dataset"):
        file_basename = file_basename[:-8]
    if file_basename.startswith("olist_"):
        file_basename = file_basename[6:]
    return f"{prefix}_{file_basename}"


def get_table_name(filename: str) -> str:
    """ファイル名からBigQueryテーブル名を生成"""
    file_basename = filename.replace(".csv", "")
    return f"raw__{file_basename}"


def get_kaggle_asset_metadata(file_config: FileConfig) -> dict:
    """Kaggleアセット用のメタデータを生成"""
    return {
        "data_domain": file_config.domain,
        "data_type": file_config.data_type,
        "data_layer": "raw",
        "data_format": "csv",
        "data_source": "kaggle",
        "source_dataset": "olistbr/brazilian-ecommerce",
        "processing_type": "incremental" if file_config.is_incremental else "full_load",
        "update_frequency": "daily" if file_config.is_incremental else "on_demand",
        "data_quality": "raw",
        "schema_evolution": "allowed",
        "business_domain": "ecommerce",
        "business_unit": "olist",
        "country": "brazil",
        "storage_location": "gcs",
        "storage_format": "csv",
        "compression": "none",
        "filename": file_config.filename,
        "asset_version": "1.0",
    }


def get_bigquery_asset_metadata(
    file_config: FileConfig, table_name: str, table_id: str
) -> dict:
    """BigQueryアセット用のメタデータを生成"""
    return {
        "data_domain": file_config.domain,
        "data_type": file_config.data_type,
        "data_layer": "raw",
        "data_format": "bigquery_table",
        "data_source": "gcs",
        "source_format": "csv",
        "processing_type": "incremental" if file_config.is_incremental else "full_load",
        "update_frequency": "daily" if file_config.is_incremental else "on_demand",
        "write_disposition": "append" if file_config.is_incremental else "truncate",
        "data_quality": "raw",
        "schema_evolution": "allowed",
        "schema_autodetect": True,
        "business_domain": "ecommerce",
        "business_unit": "olist",
        "country": "brazil",
        "storage_location": "bigquery",
        "storage_format": "table",
        "table_name": table_name,
        "table_id": table_id,
        "database": "bigquery",
        "filename": file_config.filename,
        "asset_version": "1.0",
    }
