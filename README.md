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

## 環境

- **local環境**: ローカル開発環境（Docker環境を使用）
- **dev環境**: 開発環境（GKE上で実行）
  - `feature-`ブランチがリモートにプッシュされた時にCI/CDでdev環境に反映
- **prd環境**: 本番環境（GKE上で実行）
  - `main`ブランチにマージされた時にCI/CDでprd環境に反映

## クイックスタート

### ローカル環境で起動（DevContainer）

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
uv run dagster dev -w dagster_project/workspace.local.yaml
```

   - Web UI: http://localhost:3000

**注意**: 
- `DAGSTER_HOME`はDevContainer起動時に自動的に設定されます（`.devcontainer/docker-compose.yml`で設定済み）
- `dagster_project_local`ディレクトリは`dagster dev`コマンド実行時に自動的に作成されます
- 依存関係は`postCreateCommand`で自動的にインストールされます（`uv sync --dev`）
- 環境変数はホストで設定すると、DevContainer内で自動的に読み込まれます
- 本番環境では、Kubernetes Secretから環境変数として設定されます

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

### Kubernetes Secretの設定

本番環境で必要な機密情報をKubernetes Secretとして設定します。GCPコンソールから設定します。

1. **GCPコンソールにアクセス**
   - [GKEコンソール](https://console.cloud.google.com/kubernetes)にアクセス
   - プロジェクト: `olist-data-portal`
   - クラスタ: `odp-dagster-cluster`を選択

2. **Workloads > Secrets に移動**
   - 左メニューから「Workloads」→「Secrets」を選択
   - または、直接URL: `https://console.cloud.google.com/kubernetes/secret?project=olist-data-portal`

3. **Secretを作成**
   - 「CREATE SECRET」ボタンをクリック
   - 以下の情報を入力：
     - **Name**: `odp-kaggle-api-token`
     - **Namespace**: `odp-dagster`
     - **Secret type**: `Generic`
     - **Data**: 
       - Key: `token`
       - Value: `KGAT_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`（Kaggle APIトークン）

4. **作成を確認**
   - Secretが作成されたことを確認

**注意**: 
- Kaggle APIトークンは[Kaggle設定ページ](https://www.kaggle.com/settings)から取得できます
- Secret Managerを使用する場合は、事前にGCPコンソールの[Secret Manager](https://console.cloud.google.com/security/secret-manager?project=olist-data-portal)からシークレットを作成しておく必要があります

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

## インフラとの関係

**インフラリポジトリで管理**: GKE、Cloud SQL、サービスアカウント、VPC Connector、Cloud BuildサービスアカウントへのIAMロール付与等

**このアプリケーションリポジトリで管理**:
- Dagsterのアセット定義（Python）
- dbtプロジェクト（dbtモデル定義）
- Cloud Buildの設定（`cloudbuild_ci.yaml`、`cloudbuild_cd.yaml`）
- Kubernetes DeploymentとJobの定義（`deployments/`ディレクトリ配下）
- データパイプライン用GCPリソース（GCSバケット、task/executionサービスアカウントへのIAMロール付与）
