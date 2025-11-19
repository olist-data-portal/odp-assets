import os
from pathlib import Path

from dagster_dbt import DbtProject

# GCP環境ではパッケージ化されたプロジェクトを使用、開発環境では元のプロジェクトを使用
# 環境変数GCP_PROJECT_IDの有無で自動判定
# ただし、ローカル開発時（dbt-projectディレクトリが存在しない場合）はjaffle_shopを使用
is_gcp = bool(os.getenv("GCP_PROJECT_ID"))

# dbt-projectディレクトリの存在確認
dbt_project_dir = Path(__file__).joinpath("..", "..", "dbt-project").resolve()
jaffle_shop_dir = Path(__file__).joinpath("..", "..", "..", "jaffle_shop").resolve()

if is_gcp and dbt_project_dir.exists():
    # GCP環境（本番）: パッケージ化されたプロジェクトを使用
    project_dir = dbt_project_dir
    packaged_project_dir = dbt_project_dir
else:
    # ローカル環境またはGCP環境でもローカル開発時: jaffle_shopを使用
    project_dir = jaffle_shop_dir
    packaged_project_dir = dbt_project_dir if dbt_project_dir.exists() else jaffle_shop_dir

jaffle_shop_project = DbtProject(
    project_dir=project_dir,
    packaged_project_dir=packaged_project_dir,
)
jaffle_shop_project.prepare_if_dev()

