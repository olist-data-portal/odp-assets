from dagster import Definitions, define_asset_job

from olist_data_portal.assets import kaggle_to_gcs

olist_data_portal_job = define_asset_job(
    name="olist_data_portal_job",
    selection=[kaggle_to_gcs],
    description="Kaggle APIからデータを取得し、GCSにアップロードするジョブ",
)

defs = Definitions(
    assets=[kaggle_to_gcs],
    jobs=[olist_data_portal_job],
    schedules=[],
    resources={},
)
