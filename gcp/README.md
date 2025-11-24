# GCPリソース管理（Terraform）

データパイプラインで使用するGCPリソースをTerraformで管理します。

## 管理対象リソース

- **GCSバケット**: データレイク（`${resource_prefix}-data-lake`）
- **IAMロール**: インフラリポジトリで作成されたtask/executionサービスアカウントへのデータパイプライン関連IAMロール付与
  - `roles/storage.objectAdmin`
  - `roles/bigquery.dataEditor`
  - `roles/bigquery.jobUser`

## 使用方法

```bash
cd gcp
terraform init
terraform plan
terraform apply
```

状態ファイルはGCSバケット（`odp-terraform-state`）に保存されます。

## 注意事項

- インフラリポジトリで作成されたtask/executionサービスアカウントが存在することを前提としています
