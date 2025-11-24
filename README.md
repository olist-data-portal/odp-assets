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

3. **GCP認証（初回のみ）**
   - DevContainer起動時に`init.sh`が自動的に`gcloud auth application-default login --no-launch-browser`を実行します
   - 表示されたURLにアクセスして認証コードを入力してください
   - 既に認証済みの場合はスキップされます

4. **Dagsterを起動**

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

## CI/CD

- **CI**: `feature-`ブランチから`main`へのPull Request時に実行
  - `gcp/**`ディレクトリの変更があった場合のみTerraformのフォーマットチェック、バリデーション、プランを実行
- **CD**: `main`ブランチにマージされた時に実行
  - `gcp/**`ディレクトリの変更があった場合のみTerraformのプランと適用を実行
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
