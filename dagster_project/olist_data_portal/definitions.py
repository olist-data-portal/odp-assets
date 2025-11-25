from dagster import Definitions, define_asset_job

from olist_data_portal.assets import ALL_OLIST_FILES
from olist_data_portal.assets.utils import get_variable_name_from_filename
from olist_data_portal.resources import BigQueryResource, GcsResource

# 動的にアセットをインポート
import olist_data_portal.assets as assets_module

all_assets = []
for filename in ALL_OLIST_FILES:
    kaggle_var_name = get_variable_name_from_filename(filename, "kaggle")
    gcs_var_name = get_variable_name_from_filename(filename, "gcs")

    if hasattr(assets_module, kaggle_var_name):
        all_assets.append(getattr(assets_module, kaggle_var_name))
    if hasattr(assets_module, gcs_var_name):
        all_assets.append(getattr(assets_module, gcs_var_name))

olist_data_portal_job = define_asset_job(
    name="olist_data_portal_job",
    selection=all_assets,
    description="Kaggle APIからデータを取得し、GCSにアップロードし、BigQueryにロードするジョブ",
)

defs = Definitions(
    assets=all_assets,
    jobs=[olist_data_portal_job],
    schedules=[],
    resources={
        "bigquery": BigQueryResource(),
        "gcs": GcsResource(),
    },
)
