import json
import os
import shutil
from pathlib import Path

from dagster import AssetExecutionContext, Definitions, define_asset_job
from dagster_dbt import DbtCliResource, dbt_assets

from olist_data_portal.assets import ALL_OLIST_FILES
from olist_data_portal.assets.utils import get_variable_name_from_filename
from olist_data_portal.resources import BigQueryResource, GcsResource

import olist_data_portal.assets as assets_module

# dbtプロジェクトのパスを取得
dbt_project_dir = Path(__file__).parent.parent.parent / "odp"
if not dbt_project_dir.exists():
    dbt_project_dir = Path("/workspace/odp-assets/odp")

# パスを絶対パスに変換して検証
dbt_project_dir = dbt_project_dir.resolve()
if not dbt_project_dir.exists():
    raise RuntimeError(
        f"dbt project directory does not exist: {dbt_project_dir}. "
        f"Please ensure the 'odp' directory exists in the workspace root."
    )

# 環境変数からdbt targetとenvを取得
dbt_target = os.getenv("DBT_TARGET", "local")
dbt_env = os.getenv("DBT_ENV")

# local環境でDBT_ENVが未設定の場合、profiles.local.ymlからユーザー名を読み取る
if dbt_env is None and dbt_target == "local":
    username = os.getenv("USER", "local")
    local_profiles = dbt_project_dir / "profiles.local.yml"
    if local_profiles.exists():
        try:
            with open(local_profiles, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("# username:"):
                        username = line.split(":", 1)[1].strip() or username
                        break
        except Exception:
            pass
        # profiles.local.ymlをprofiles.ymlとしてコピー（dbtはprofiles.ymlを探すため）
        profiles_yml = dbt_project_dir / "profiles.yml"
        if (
            not profiles_yml.exists()
            or local_profiles.stat().st_mtime > profiles_yml.stat().st_mtime
        ):
            shutil.copy2(local_profiles, profiles_yml)
    else:
        # profiles.local.ymlが存在しない場合、profiles.local.yml.exampleをコピー
        local_profiles_example = dbt_project_dir / "profiles.local.yml.example"
        if local_profiles_example.exists():
            shutil.copy2(local_profiles_example, local_profiles)
            profiles_yml = dbt_project_dir / "profiles.yml"
            shutil.copy2(local_profiles, profiles_yml)
    dbt_env = f"local-{username}"
elif dbt_env is None:
    dbt_env = "local"

# 環境変数を設定
os.environ["DBT_TARGET"] = dbt_target
os.environ["DBT_ENV"] = dbt_env

# dbtプロジェクトディレクトリのパスを文字列に変換
dbt_project_dir_str = str(dbt_project_dir)
# デバッグ用: パスが正しいことを確認
if not Path(dbt_project_dir_str).exists():
    raise RuntimeError(
        f"dbt project directory does not exist: {dbt_project_dir_str}. "
        f"Expected path: /workspace/odp-assets/odp"
    )

dbt_resource = DbtCliResource(
    project_dir=dbt_project_dir_str,
    profiles_dir=dbt_project_dir_str,
    target=dbt_target,
)

# manifest.jsonを読み込む
manifest_json = None

# リソースを初期化
gcs_resource = GcsResource()

# stg/prd環境の場合、GCSからmanifest.jsonを読み込む
if dbt_target in ["stg", "prd"]:
    gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "odp-data-lake")
    gcs_manifest_path = f"dbt-manifests/{dbt_target}/manifest.json"

    try:
        # GCSアクセスを試行（認証情報が利用可能な場合のみ）
        bucket = gcs_resource.get_bucket(gcs_bucket_name)
        blob = bucket.blob(gcs_manifest_path)

        if blob.exists():
            manifest_json = json.loads(blob.download_as_text())
        else:
            # GCSに存在しない場合、dbt parseを実行してmanifest.jsonを生成
            dbt_parse_invocation = dbt_resource.cli(["parse"]).wait()
            if dbt_parse_invocation.is_successful():
                manifest_json = dbt_parse_invocation.get_artifact("manifest.json")
                # GCSに保存（認証情報が利用可能な場合のみ）
                try:
                    blob.upload_from_string(
                        json.dumps(manifest_json, indent=2), content_type="application/json"
                    )
                except Exception:
                    pass
    except Exception:
        # GCSアクセスに失敗した場合（認証情報が設定されていない等）、ローカルでparseを実行
        dbt_parse_invocation = dbt_resource.cli(["parse"]).wait()
        if dbt_parse_invocation.is_successful():
            manifest_json = dbt_parse_invocation.get_artifact("manifest.json")
else:
    # local環境の場合、ローカルでparseを実行
    dbt_parse_invocation = dbt_resource.cli(["parse"]).wait()
    if dbt_parse_invocation.is_successful():
        manifest_json = dbt_parse_invocation.get_artifact("manifest.json")

if manifest_json is None:
    raise RuntimeError("Failed to load dbt manifest.json")


@dbt_assets(manifest=manifest_json)
def dbt_olist_assets(context: AssetExecutionContext):
    """dbtモデルをDagsterアセットとして実行"""
    # stg/prd環境の場合、実行後にmanifest.jsonをGCSに保存
    yield from dbt_resource.cli(["run"], context=context).stream()

    if dbt_target in ["stg", "prd"]:
        try:
            # 実行後のmanifest.jsonをGCSに保存（認証情報が利用可能な場合のみ）
            dbt_parse_invocation = dbt_resource.cli(["parse"]).wait()
            if dbt_parse_invocation.is_successful():
                updated_manifest = dbt_parse_invocation.get_artifact("manifest.json")
                gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "odp-data-lake")
                gcs_manifest_path = f"dbt-manifests/{dbt_target}/manifest.json"
                bucket = gcs_resource.get_bucket(gcs_bucket_name)
                blob = bucket.blob(gcs_manifest_path)
                blob.upload_from_string(
                    json.dumps(updated_manifest, indent=2),
                    content_type="application/json",
                )
        except Exception:
            # GCSアクセスに失敗した場合（認証情報が設定されていない等）、スキップ
            pass


# 既存のアセットを収集
all_assets = []
for filename in ALL_OLIST_FILES:
    kaggle_var_name = get_variable_name_from_filename(filename, "kaggle")
    gcs_var_name = get_variable_name_from_filename(filename, "gcs")

    if hasattr(assets_module, kaggle_var_name):
        all_assets.append(getattr(assets_module, kaggle_var_name))
    if hasattr(assets_module, gcs_var_name):
        all_assets.append(getattr(assets_module, gcs_var_name))

# dbtアセットを追加
all_assets.append(dbt_olist_assets)

olist_data_portal_job = define_asset_job(
    name="olist_data_portal_job",
    selection=all_assets,
    description="Kaggle APIからデータを取得し、GCSにアップロードし、BigQueryにロードし、dbtで変換するジョブ",
)

defs = Definitions(
    assets=all_assets,
    jobs=[olist_data_portal_job],
    schedules=[],
    resources={
        "bigquery": BigQueryResource(),
        "gcs": gcs_resource,
        "dbt": dbt_resource,
    },
)
