# Dagster Project

このプロジェクトは、dbtプロジェクト（jaffle_shop）をDagsterで管理するためのプロジェクトです。

## 構成

```
dagster_project/
├── dagster_project/
│   ├── __init__.py
│   ├── definitions.py      # Dagster定義（Assets、Schedules、Resources）
│   ├── assets.py          # dbtアセット定義
│   ├── project.py         # dbtプロジェクト設定（環境に応じて自動切り替え）
│   ├── schedules.py       # スケジュール定義
│   ├── dagster.yaml       # ローカル環境用設定
│   ├── dagster.yaml.production  # GCP本番環境用設定
│   ├── workspace.yaml     # ローカル環境用ワークスペース設定
│   ├── workspace.yaml.production  # GCP本番環境用ワークスペース設定
│   ├── startup.sh         # コンテナ起動スクリプト（workspace.yaml選択）
│   ├── Dockerfile_dagster # Dagster core用Dockerfile（Web、Daemon）
│   ├── Dockerfile_user_code  # User code用Dockerfile（gRPCサーバー）
│   └── docker-compose.yaml   # ローカルテスト用Docker Compose
├── pyproject.toml         # プロジェクト設定・依存関係
├── uv.lock                # 依存関係ロックファイル
└── README.md
```

## クイックスタート

### ローカル環境で起動

このプロジェクトは**devContainer前提**で動作します。

1. VS Code/Cursorでこのリポジトリを開く
2. プロンプトが表示されたら「Reopen in Container」を選択
   - または、コマンドパレット（Cmd/Ctrl+Shift+P）から「Dev Containers: Reopen in Container」を選択
3. devContainerが起動したら、依存関係をインストールしてDagsterを起動：

```bash
cd dagster_project
uv sync --dev
uv run dagster dev
```

**devContainerのメリット:**
- IDE統合（コード補完、デバッグ、リントなど）
- 統一された開発環境
- 依存関係の自動管理（uvが自動インストール済み）

Web UI: http://localhost:3000

## 依存関係のインストール

devContainer内で以下を実行：

```bash
cd dagster_project
uv sync --dev
```

**注意**: `uv sync --dev`は開発用の依存関係（`dagster-webserver`など）もインストールします。

## コンテナイメージのビルドとプッシュ

GCP環境（Cloud Run）にデプロイする前に、コンテナイメージをArtifact Registryにプッシュする必要があります。

### 前提条件

- Terraformのfoundationレイヤーが作成済み（Artifact Registryが存在）
- GCP認証が完了している

### 手順

```bash
# 1. GCP認証設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# 2. プロジェクトIDとリポジトリ名を設定（Terraformの出力値から取得）
export PROJECT_ID=your-project-id
export PREFIX=twitch-dp
export REGION=asia-northeast1

# 3. Dagster coreイメージのビルドとプッシュ
docker build -f dagster_project/dagster_project/Dockerfile_dagster \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${PREFIX}-dagster-cloudrun-core/dagster:latest \
  .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${PREFIX}-dagster-cloudrun-core/dagster:latest

# 4. User codeイメージのビルドとプッシュ
docker build -f dagster_project/dagster_project/Dockerfile_user_code \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${PREFIX}-dagster-cloudrun-user-code/user-code:latest \
  .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${PREFIX}-dagster-cloudrun-user-code/user-code:latest
```

**注意**: イメージのビルドとプッシュは手動で実行する必要があります。Terraformの`application`レイヤーを適用する前に、必ずイメージをプッシュしてください。

## 設定ファイル

### ローカル環境

- `dagster.yaml`: ローカル環境用の設定（SQLiteストレージ）
- `workspace.yaml`: ローカル環境用のワークスペース設定（python_moduleから直接読み込み）

### GCP本番環境（Cloud Run）

- `dagster.yaml.production`: GCP本番環境用の設定（PostgreSQLストレージ、Cloud Runランチャー）
- `workspace.yaml.production`: GCP本番環境用のワークスペース設定（gRPCサーバーから読み込み）
- `startup.sh`: 環境変数`GCP_PROJECT_ID`の有無で適切なworkspace.yamlを選択

### 環境変数による自動切り替え

`startup.sh`が以下のロジックでworkspace.yamlを選択します：

- `GCP_PROJECT_ID`が設定されている場合: `workspace.yaml.production`を使用
- それ以外: `workspace.yaml.local`を使用

## Web UI

### ローカル環境

Dagsterが起動したら、以下のURLでWeb UIにアクセスできます：

- http://localhost:3000

### GCP環境（Cloud Run）

GCP環境でデプロイされたDagsterのURLは、以下のコマンドで確認できます：

```bash
cd terraform/application
terraform output -raw dagster_url
```

## トラブルシューティング

### ローカル環境

#### ポート3000が既に使用されている場合

別のポートで起動するには：

```bash
uv run dagster dev --port 3001
```

#### 依存関係のインストールエラー

```bash
cd dagster_project
uv sync --dev
```

#### Dagsterが起動しない場合

1. 依存関係が正しくインストールされているか確認
2. ポート3000が既に使用されていないか確認：`lsof -i :3000`
3. devContainerを再ビルド：コマンドパレットから「Dev Containers: Rebuild Container」を実行

### devContainer

#### devContainerが起動しない場合

1. Dockerが起動していることを確認
2. `.devcontainer`ディレクトリが正しく配置されていることを確認
3. コマンドパレットから「Dev Containers: Rebuild Container」を実行

#### uvコマンドが見つからない場合

devContainer内で以下を実行：

```bash
which uv
# パスが表示されない場合
export PATH="/home/vscode/.local/bin:$PATH"
```

### GCP環境（Cloud Run）

#### ログの確認

Cloud RunのログはCloud Loggingに自動的に送信されます：

```bash
# Webサービスのログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${PREFIX}-dagster-web" --limit 50

# Daemonサービスのログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${PREFIX}-dagster-daemon" --limit 50

# User codeサービスのログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${PREFIX}-dagster-user-code" --limit 50
```

