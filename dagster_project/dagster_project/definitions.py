from dagster import Definitions

from dagster_project.assets import kaggle_to_gcs

defs = Definitions(
    assets=[kaggle_to_gcs],
    schedules=[],
    resources={},
)
