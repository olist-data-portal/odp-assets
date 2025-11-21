# Twitch Data Pipeline Assets

DagsterでオーケストレーションするデータパイプラインのアプリケーションをdbtとPythonで作成します。

## データパイプラインの構成

以下の3つのステップで構成されます：

1. **APIからGCSへのデータ取得**: 外部APIからデータを取得し、GCS（データレイク）に保存
2. **GCSからBigQueryへのロード**: GCSのデータをBigQuery（データウェアハウス）にロード
3. **dbtでのモデル構築**: BigQueryのデータをdbtで変換・モデル化

## 環境

- **local環境**: ローカル開発環境（Docker環境を使用）
- **dev環境**: 開発環境（GKE上で実行）
  - `feature-`ブランチがリモートにプッシュされた時にCI/CDでdev環境に反映
- **prd環境**: 本番環境（GKE上で実行）
  - `main`ブランチにマージされた時にCI/CDでprd環境に反映

## クイックスタート

### ローカル環境で起動

1. VS Code/Cursorでこのリポジトリを開き、「Reopen in Container」を選択
2. devContainerが起動したら、依存関係をインストールしてDagsterを起動：

```bash
cd dagster_project
uv sync --dev
uv run dagster dev -w dagster_project/workspace.yaml
```

Web UI: http://localhost:3000

## インフラとの関係

**注意**: Dagsterのインフラ（GKE、Cloud SQL、サービスアカウント等）のデプロイはインフラリポジトリで行います。このアプリケーションリポジトリでは、以下のみを管理します：

- Dagsterのアセット定義（Python）
- dbtプロジェクト（dbtモデル定義）
- Dockerイメージのビルド設定

