# CI/CD用サービスアカウント作成手順

このドキュメントでは、GitHub ActionsのCI/CDで使用するGCPサービスアカウントの作成手順を説明します。

## 概要

CI/CD用のサービスアカウントは、以下の用途で使用されます：

- **Terraform CI/CD**: Terraformの実行（init, plan, apply）
- **Dockerイメージのビルド・プッシュ**: Artifact Registryへのプッシュ
- **dbt CI/CD**（将来追加予定）: BigQueryへのアクセス、データセットの作成
- **Dagster asset CI/CD**（将来追加予定）: GCS、BigQueryへのアクセス

## 必要な権限

CI/CD用サービスアカウントには、以下のIAMロールを付与します：

### 必須権限

1. **Terraform実行用**
   - `roles/iam.serviceAccountAdmin`: サービスアカウントの作成・管理
   - `roles/storage.admin`: GCSバケットの作成・管理
   - `roles/bigquery.admin`: BigQueryデータセットの作成・管理（dbt CI/CD用）
   - `roles/resourcemanager.projectIamAdmin`: IAM権限の付与

2. **Artifact Registry Writer**
   - `roles/artifactregistry.writer`: Dockerイメージのプッシュ

### 推奨権限（最小権限の原則に従う場合）

最小権限の原則に従う場合は、以下のカスタムロールを作成することも検討できます：

- Terraform実行用のカスタムロール（必要な権限のみを付与）
- Artifact Registry Writer（既存のロールを使用）

## 作成手順

以下の2つの方法があります：

- **方法1**: GCPコンソールから作成（推奨）
- **方法2**: gcloudコマンドで作成

### 方法1: GCPコンソールから作成

#### 1. GCPコンソールでサービスアカウントを作成

1. [GCPコンソール](https://console.cloud.google.com/)にアクセス
2. プロジェクトを選択: `olist-data-portal`
3. 左側のメニューから「IAMと管理」→「サービスアカウント」を選択
4. 「サービスアカウントを作成」をクリック

### 2. サービスアカウントの詳細を入力

- **サービスアカウント名**: `odp-cicd-sa`
- **サービスアカウントID**: `odp-cicd-sa`（自動入力）
- **説明**: `CI/CD用サービスアカウント（Terraform、Docker、dbt、Dagster asset用）`
- 「作成して続行」をクリック

### 3. ロールを付与

「このサービスアカウントにロールを付与」で、以下のロールを追加：

1. `Service Account Admin` (`roles/iam.serviceAccountAdmin`)
2. `Storage Admin` (`roles/storage.admin`)
3. `BigQuery Admin` (`roles/bigquery.admin`)
4. `Project IAM Admin` (`roles/resourcemanager.projectIamAdmin`)
5. `Artifact Registry Writer` (`roles/artifactregistry.writer`)

各ロールを追加したら「続行」をクリック

### 4. ユーザーアクセスの設定（オプション）

通常はスキップして「完了」をクリック

### 5. サービスアカウントキーの作成

1. 作成したサービスアカウント（`odp-cicd-sa`）をクリック
2. 「キー」タブを選択
3. 「キーを追加」→「新しいキーを作成」を選択
4. キーのタイプ: `JSON`を選択
5. 「作成」をクリック
6. JSONキーファイルがダウンロードされる

### 6. GitHub Secretsに設定

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」を開く
2. 「New repository secret」をクリック
3. 以下のシークレットを追加：

   - **Name**: `GCP_SA_KEY`
   - **Value**: ダウンロードしたJSONキーファイルの内容をそのまま貼り付け

4. 「Add secret」をクリック

### 方法2: gcloudコマンドで作成

以下のコマンドを実行して、サービスアカウントを作成し、必要なロールを付与します：

```bash
# プロジェクトを設定
export PROJECT_ID="olist-data-portal"
export SA_NAME="odp-cicd-sa"
export SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# サービスアカウントを作成
gcloud iam service-accounts create ${SA_NAME} \
  --project=${PROJECT_ID} \
  --display-name="CI/CD Service Account" \
  --description="CI/CD用サービスアカウント（Terraform、Docker、dbt、Dagster asset用）"

# 必要なロールを付与
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountAdmin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/resourcemanager.projectIamAdmin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# サービスアカウントキーを作成（JSON形式）
gcloud iam service-accounts keys create ${SA_NAME}-key.json \
  --iam-account=${SA_EMAIL} \
  --project=${PROJECT_ID}

# キーファイルの内容を表示（GitHub Secretsに設定する際に使用）
cat ${SA_NAME}-key.json
```

**注意**: 作成したキーファイル（`${SA_NAME}-key.json`）は機密情報です。GitHub Secretsに設定した後は、ローカルファイルを削除してください。

```bash
# キーファイルを削除（GitHub Secretsに設定済みの場合）
rm ${SA_NAME}-key.json
```

## 確認

### サービスアカウントの確認

```bash
# サービスアカウントの存在確認
gcloud iam service-accounts describe odp-cicd-sa@olist-data-portal.iam.gserviceaccount.com \
  --project olist-data-portal

# 付与されているロールの確認
gcloud projects get-iam-policy olist-data-portal \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:odp-cicd-sa@olist-data-portal.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

### GitHub Actionsでの動作確認

Terraform CI/CDワークフローを実行して、正常に動作することを確認してください。

## 注意事項

- **セキュリティ**: サービスアカウントキーは機密情報です。GitHub Secretsで管理し、リポジトリにコミットしないでください
- **最小権限の原則**: 必要最小限の権限のみを付与してください
- **定期的な見直し**: 定期的に付与されている権限を見直し、不要な権限は削除してください

## トラブルシューティング

### 権限エラーが発生する場合

- サービスアカウントに必要なロールが付与されているか確認
- GitHub Secretsの`GCP_SA_KEY`が正しく設定されているか確認
- Terraformの実行ログを確認して、どの権限が不足しているか特定

### Artifact Registryへのプッシュが失敗する場合

- `roles/artifactregistry.writer`ロールが付与されているか確認
- Artifact RegistryリポジトリのIAM設定を確認

