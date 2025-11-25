"""アセットの動的インポート"""

from olist_data_portal.assets.file_config import ALL_OLIST_FILES
from olist_data_portal.assets.utils import get_variable_name_from_filename

# モジュールをインポート（アセット生成をトリガー）
# 循環インポートを避けるため、相対インポートを使用
from . import gcs_to_bigquery, kaggle_api_to_gcs

# 動的にアセットを公開
for filename in ALL_OLIST_FILES:
    kaggle_var_name = get_variable_name_from_filename(filename, "kaggle")
    gcs_var_name = get_variable_name_from_filename(filename, "gcs")

    if hasattr(kaggle_api_to_gcs, kaggle_var_name):
        globals()[kaggle_var_name] = getattr(kaggle_api_to_gcs, kaggle_var_name)
    if hasattr(gcs_to_bigquery, gcs_var_name):
        globals()[gcs_var_name] = getattr(gcs_to_bigquery, gcs_var_name)

# __all__を動的に生成
__all__ = [get_variable_name_from_filename(filename, "kaggle") for filename in ALL_OLIST_FILES] + [
    get_variable_name_from_filename(filename, "gcs") for filename in ALL_OLIST_FILES
]
