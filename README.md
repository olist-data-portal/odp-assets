# Olist Data Pipeline Assets

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

## プロジェクト情報

- **GCPプロジェクトID**: `olist-data-portal`
- **リソースPREFIX**: `odp`

## インフラとの関係

**注意**: Dagsterのインフラ（GKE、Cloud SQL、サービスアカウント等）のデプロイはインフラリポジトリで行います。このアプリケーションリポジトリでは、以下のみを管理します：

- Dagsterのアセット定義（Python）
- dbtプロジェクト（dbtモデル定義）
- Dockerイメージのビルド設定
- Kubernetes DeploymentとJobの定義
- データパイプライン用GCPリソース（Terraformで管理）

## CI/CD

GitHub Actionsを使用してCI/CDを自動化しています。

### ワークフロー

- **CI**: `feature-`ブランチから`main`へのPull Requestが作成・更新されたときに実行
  - コードのフォーマットチェック、バリデーション、テストを実行
  - Terraformのフォーマットチェック、バリデーション、プランを実行
- **CD（dev環境）**: `feature-`ブランチがリモートにプッシュされたときに実行
  - Dockerイメージのビルドとプッシュを自動的に実行
- **CD（prd環境）**: `main`ブランチにマージされたときに実行
  - Dockerイメージのビルドとプッシュを自動的に実行
  - Terraformのプランと適用を実行（`environment: production`により承認が必要）

## Kubernetesデプロイ

### 初回デプロイ

GKEクラスタに接続してDeploymentを作成します：

```bash
# GKEクラスタに接続
gcloud container clusters get-credentials odp-dagster-cluster \
  --region asia-northeast1 \
  --project olist-data-portal

# Deploymentを作成
kubectl apply -f deployments/webserver.yaml
kubectl apply -f deployments/daemon.yaml
kubectl apply -f deployments/user-code.yaml
```

### イメージ更新

Dockerイメージが更新されたら、以下のコマンドでDeploymentのイメージを更新します（インフラデプロイ不要）：

```bash
# イメージを更新
kubectl set image deployment/dagster-web \
  webserver=asia-northeast1-docker.pkg.dev/olist-data-portal/odp-dagster/dagster:latest \
  -n odp-dagster

kubectl set image deployment/dagster-daemon \
  daemon=asia-northeast1-docker.pkg.dev/olist-data-portal/odp-dagster/dagster:latest \
  -n odp-dagster

kubectl set image deployment/dagster-user-code \
  user-code=asia-northeast1-docker.pkg.dev/olist-data-portal/odp-dagster/dagster-user-code:latest \
  -n odp-dagster
```

### デプロイ済みリソースの確認

```bash
# Deploymentの状態を確認
kubectl get deployments -n odp-dagster

# Podの状態を確認
kubectl get pods -n odp-dagster

# ログの確認
kubectl logs -f deployment/dagster-web -n odp-dagster
```

