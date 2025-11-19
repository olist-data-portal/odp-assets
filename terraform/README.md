# Terraform構成

DagsterをCloud Runで動かすインフラ構成。基盤とアプリケーションに分離して管理。

## 構成

```
terraform/
├── foundation/          # 基盤リソース（先に作成）
│   ├── main.tf         # VPC、Cloud SQL、Artifact Registry、IAM、Secret Manager、BigQuery
│   ├── variables.tf    # 変数定義
│   ├── outputs.tf      # 出力値（application側で使用）
│   ├── providers.tf    # プロバイダー設定
│   └── terraform.tfvars.example
├── application/         # アプリケーションリソース（後に作成）
│   ├── main.tf         # Cloud Load Balancer、Cloud Run、Cloud DNS、VPC Access Connector
│   ├── variables.tf    # 変数定義
│   ├── outputs.tf      # Load Balancerエンドポイント等
│   ├── providers.tf    # プロバイダー設定
│   └── terraform.tfvars.example
└── README.md
```

## 実行手順

### 1. GCP認証設定

```bash
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
```

### 2. 変数ファイル準備

```bash
# foundation
cp terraform/foundation/terraform.tfvars.example terraform/foundation/terraform.tfvars
# 編集

# application
cp terraform/application/terraform.tfvars.example terraform/application/terraform.tfvars  
# 編集
```

### 3. 基盤リソース作成（先に実行）

```bash
cd terraform/foundation
terraform init && terraform apply
```

### 4. アプリケーションリソース作成（後に実行）

```bash
cd terraform/application
terraform init && terraform apply
```

**注意**: applicationはfoundationの出力値を参照するため、foundationの`terraform.tfstate`が必要です。

### 5. Artifact Registryイメージ準備（foundation作成後）

コンテナイメージをArtifact Registryにプッシュします。

**注意**: イメージのビルドとプッシュはGitHub Actionsで自動化されています。手動で行う場合は、以下のコマンドを実行してください：

```bash
cd dagster_project
docker compose build
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
# タグ付け・プッシュ（詳細は dagster_project/README.md 参照）
```

## 必要な変数

### foundation/

**必須変数:**
- `prefix`: リソース名プレフィックス（デフォルト: "twitch-dp"）
- `project_id`: GCPプロジェクトID
- `dbt_env_secret_bigquery_project`: BigQueryプロジェクトID

**オプション変数:**
- `region`: GCPリージョン（デフォルト: asia-northeast1）
- `vpc_cidr`: VPC CIDRブロック（デフォルト: "10.0.0.0/16"）
- `public_subnet_cidrs`: パブリックサブネットCIDR（デフォルト: ["10.0.1.0/24", "10.0.2.0/24"]）
- `private_subnet_cidrs`: プライベートサブネットCIDR（デフォルト: ["10.0.3.0/24", "10.0.4.0/24"]）
- `prefix_list_ids`: ALBセキュリティグループ用プレフィックスリスト（デフォルト: []）
- `dagster_postgres_db`: Dagsterデータベース名（デフォルト: "dagster"）
- `dagster_postgres_user`: Dagsterデータベースユーザー名（デフォルト: "dagster_user"）
- `dbt_env_secret_bigquery_location`: BigQueryロケーション（デフォルト: "asia-northeast1"）
- `dbt_env_secret_bigquery_dataset`: BigQueryデータセット名（レガシー、オプション）
- `dbt_environments`: DBT環境名リスト（デフォルト: ["dev"]）
- `dbt_model_directories`: DBTモデルディレクトリ名リスト（デフォルト: ["staging", "models"]）
- `dataset_prefix`: BigQueryデータセット名プレフィックス（デフォルト: "dp"）

### application/

- `prefix`: リソース名プレフィックス（デフォルト: "twitch-dp"）
- `project_id`: GCPプロジェクトID
- `region`: GCPリージョン（デフォルト: asia-northeast1）

## 主要なGCPリソース

### Foundation

**ネットワーク:**
- **VPC Network**: プライベートネットワーク
- **Subnet**: パブリック/プライベートサブネット
- **Cloud Router**: NAT用ルーター
- **Cloud NAT**: プライベートサブネットのインターネットアクセス
- **Firewall Rules**: ネットワークセキュリティルール
- **Private Service Connection**: Cloud SQL用VPCピアリング

**データベース:**
- **Cloud SQL**: PostgreSQLデータベース（Dagster用）

**コンテナ:**
- **Artifact Registry**: コンテナイメージリポジトリ（Dagster core、User code）

**セキュリティ:**
- **Secret Manager**: 機密情報管理（PostgreSQL認証情報、BigQuery認証情報）
- **IAM Service Accounts**: タスク実行用、実行用、BigQuery用のサービスアカウント

**データ:**
- **BigQuery Dataset**: DBT変換用データセット（環境×ディレクトリの組み合わせで作成）

### Application

**ロードバランシング:**
- **Cloud Load Balancer**: HTTPロードバランサー
- **Backend Service**: Cloud Run用バックエンドサービス
- **Network Endpoint Group (NEG)**: Cloud Run用NEG
- **Health Check**: Webサービス用ヘルスチェック

**コンテナ:**
- **Cloud Run Services**: Dagster Web、Daemon、User Codeサービス

**ネットワーク:**
- **VPC Access Connector**: Cloud RunからVPCリソースへのアクセス
- **Cloud DNS**: サービスディスカバリー用のプライベートDNS

## 注意事項

1. **実行順序**: foundation → application（必須）
2. **状態ファイル**: applicationはfoundationの`terraform.tfstate`を参照するため、foundation作成後に`terraform.tfstate`が存在することを確認
3. **機密情報**: `terraform.tfvars`で管理（バージョン管理対象外）
4. **削除順序**: application → foundation（重要: この順序を守らないとエラーが発生します）
5. **Cloud Runのシークレット**: Secret Managerのシークレットは環境変数として直接参照可能
6. **VPC Access Connector**: Cloud RunからVPC内のCloud SQLにアクセスするために必要
7. **BigQuery**: データセットはfoundationで作成され、application側で使用

## 削除手順（重要）

リソースを削除する際は、**必ず以下の順序で実行**してください：

### 1. Applicationレイヤーを先に削除

```bash
cd terraform/application
terraform destroy
```

これにより、Cloud Runサービスが削除され、データベースへの接続が切断されます。

### 2. Foundationレイヤーを削除

```bash
cd terraform/foundation
terraform destroy
```

**注意**: データベース削除時に「being accessed by other users」エラーが発生した場合は、Cloud Runサービスが完全に削除されるまで待つか、手動でCloud Runサービスを削除してください。

## アクセスURL確認

デプロイ後、DagsterのURLは以下のコマンドで確認できます：

```bash
cd terraform/application
terraform output -raw dagster_url
```

## ログ確認

Cloud Runのログは自動的にCloud Loggingに送信されます。

```bash
# Webサービスのログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${prefix}-dagster-web" --limit 50

# Daemonサービスのログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${prefix}-dagster-daemon" --limit 50
```
