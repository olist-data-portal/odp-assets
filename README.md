# Olist Data Pipeline Assets

DagsterでオーケストレーションするデータパイプラインのアプリケーションをdbtとPythonで作成します。

## データパイプラインの構成

以下の3つのステップで構成されます：

1. **APIからGCSへのデータ取得**: 外部APIからデータを取得し、GCS（データレイク）に保存
2. **GCSからBigQueryへのロード**: GCSのデータをBigQuery（データウェアハウス）にロード
3. **dbtでのモデル構築**: BigQueryのデータをdbtで変換・モデル化

## プロジェクト情報

- **GCPプロジェクトID**: `olist-data-portal`
- **リソースプレフィックス**: `odp`

## クイックスタート

1. **DevContainerを起動**
   - VS Code/Cursorでこのリポジトリを開き、「Reopen in Container」を選択
   - 初回起動時は、依存関係のインストールとGCP認証の設定が自動的に実行されます

2. **環境変数を設定**
   - `.env.example`をコピーして`.env`ファイルを作成して、実際の値を設定します：

   - `KAGGLE_API_TOKEN`: [Kaggle設定ページ](https://www.kaggle.com/settings)からAPIトークンを取得して設定
   - `.env`ファイルは`.devcontainer/docker-compose.yml`の`env_file`セクションで自動的に読み込まれます
   - `.env`ファイルはgit管理に含まれません（`.gitignore`で除外されています）

3. **dbt設定（チーム開発用）**
   - `odp/profiles.local.yml.example`をコピーして`odp/profiles.local.yml`を作成
   - `# username: yourname`を自分のユーザー名に変更
   - `profiles.local.yml`はgit管理に含まれません

4. **GCP認証（初回のみ）**
   - DevContainer起動時に`init.sh`が自動的に`gcloud auth application-default login --no-launch-browser`を実行します
   - 表示されたURLにアクセスして認証コードを入力してください
   - 既に認証済みの場合はスキップされます

5. **Dagsterを起動**

```bash
cd dagster_project
uv sync --dev
uv run dagster dev
```

   - Web UI: http://localhost:3000

**注意**: 
- `DAGSTER_HOME`はDevContainer起動時に自動的に設定されます（`.devcontainer/docker-compose.yml`で設定済み）
- 依存関係は`postCreateCommand`で自動的にインストールされます（`uv sync --dev`）
- 環境変数はホストで設定すると、DevContainer内で自動的に読み込まれます

## dbt環境

dbtは環境変数で環境を切り替えられます。

- **local環境**: `cd dagster_project && uv run dagster dev`
  - manifest.jsonはローカルで管理
- **stg環境**: `DBT_TARGET=stg DBT_ENV=stg cd dagster_project && uv run dagster dev`
  - manifest.jsonはGCSで管理（`dbt-manifests/stg/manifest.json`）
- **prd環境**: `DBT_TARGET=prd DBT_ENV=prd cd dagster_project && uv run dagster dev`
  - manifest.jsonはGCSで管理（`dbt-manifests/prd/manifest.json`）

**データセット名**: local/stgは`odp-{環境名}-{層名}`、prdは`{層名}`のみ

## CI/CD

### CI（Pull Request時）

`feature-`ブランチから`main`へのPull Request時に実行：

- **Terraformチェック**: `gcp/**`ディレクトリの変更があった場合のみ実行
  - フォーマットチェック、バリデーション、プラン
- **dbtチェック**: `odp/**`ディレクトリの変更があった場合のみ実行
  - dbt parse（構文チェック）
- **Dagsterチェック**: `dagster_project/**`ディレクトリの変更があった場合のみ実行
  - Blackフォーマットチェック、Ruffリンター、Dagster定義の検証

### CD（デプロイ）

#### Staging環境へのデプロイ

`main`ブランチにマージされた時に自動実行：

- 変更されたファイルパスを検知して自動的にデプロイ
- **Terraform**: `gcp/**`ディレクトリの変更があった場合、プランと適用を実行
- **dbt**: `odp/**`ディレクトリの変更があった場合、`dbt run`を実行
- **Dagster**: `dagster_project/**`または`odp/**`ディレクトリの変更があった場合、ジョブを実行

#### Production環境へのデプロイ

手動トリガー（GitHub Actionsの「Run workflow」）で実行：

- Terraform、dbt、Dagsterのデプロイを個別に選択可能
- `environment: production`を設定し、リソース変更時に承認が必要

詳細は`.cursor/rules/06-ci-cd.mdc`を参照してください。

## 管理対象

**このアプリケーションリポジトリで管理**:
- Dagsterのアセット定義（Python）
- dbtプロジェクト（dbtモデル定義）
- データパイプライン用GCPリソース（GCSバケット）

**Terraformで管理していないリソース**:
- GitHub Actions用のサービスアカウント（CI/CD実行用）
- Terraform状態ファイル保存用のGCSバケット（`odp-terraform-state`）
