from dagster import Definitions, define_asset_job

from olist_data_portal.assets import gcs_to_bigquery, kaggle_to_gcs

olist_data_portal_job = define_asset_job(
    name="olist_data_portal_job",
    selection=[kaggle_to_gcs, gcs_to_bigquery],
    description="Kaggle APIからデータを取得し、GCSにアップロードし、BigQueryにロードするジョブ",
)

defs = Definitions(
    assets=[kaggle_to_gcs, gcs_to_bigquery],
    jobs=[olist_data_portal_job],
    schedules=[],
    resources={},
)
