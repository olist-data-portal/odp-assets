# GCPリソース管理（Terraform）

このディレクトリには、データパイプラインで使用するGCPリソースをTerraformで定義しています。

## 管理対象リソース

- **サービスアカウント**: データパイプライン実行用サービスアカウント
- **GCSバケット**: データレイク（データ保存用）

## 構成

### サービスアカウント
- アカウントID: `odp-data-pipeline`
- 用途: データパイプラインの実行（GCSへのアクセス）

### GCSバケット
- バケット名: `odp-data-lake`
- 用途: データレイク（APIから取得したデータの保存）

## 使用方法

### 初期化

```bash
cd gcp
terraform init
```

### プランの確認

```bash
terraform plan
```

### 適用

```bash
terraform apply
```

### 変数のカスタマイズ

デフォルト値を使用せず、変数を変更する場合は`terraform.tfvars`ファイルを作成してください：

```hcl
project_id      = "olist-data-portal"
region          = "asia-northeast1"
resource_prefix = "odp"
```

### 出力の確認

適用後、以下のコマンドで出力値を確認できます：

```bash
terraform output
```

主な出力値:
- `service_account_email`: サービスアカウントのメールアドレス
- `gcs_bucket_name`: GCSバケット名

## IAM権限

サービスアカウントには以下の権限が付与されます：

- **GCS**: `roles/storage.objectViewer`, `roles/storage.objectCreator`

## 注意事項

- GCSバケットの`force_destroy`は`false`に設定されています（誤削除を防ぐため）
- GCSバケットには90日経過したオブジェクトを自動削除するライフサイクルルールが設定されています

