# GCPリソース管理（Terraform）

データパイプラインで使用するGCPリソースをTerraformで管理します。

## 管理対象リソース

- **GCSバケット**: データレイク（`${resource_prefix}-data-lake`）
  - データレイク用のGCSバケット
  - dbt manifest.jsonの保存先（`dbt-manifests/{環境名}/manifest.json`）
- **BigQueryデータセット**: データレイク（`data_lake`）

## Terraformで管理していないリソース

以下のリソースはTerraformで管理していません（手動作成済み）:

- **GitHub Actions用のサービスアカウント**: CI/CD実行用のサービスアカウント
- **Terraform状態ファイル保存用のGCSバケット**: `odp-terraform-state`（リモート状態バックエンド用）

## 使用方法

```bash
cd gcp
terraform init
terraform plan
terraform apply
```

状態ファイルはGCSバケット（`odp-terraform-state`）に保存されます。
