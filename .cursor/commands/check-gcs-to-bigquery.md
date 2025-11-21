# GCS→BigQueryステップ コードチェック

GCSからBigQueryへのデータロードステップのコードがプロジェクトのルールに準拠しているかチェックします。

## 実施内容

以下のルールファイルに基づいて、選択されたコードをレビューしてください：

- `.cursor/rules/00-overview.mdc` - プロジェクト概要
- `.cursor/rules/01-dagster-conventions.mdc` - Dagster開発規約
- `.cursor/rules/03-python-conventions.mdc` - Python開発規約
- `.cursor/rules/04-important-notices.mdc` - 重要な注意事項

## チェックポイント

1. **アセット定義**: GCSからBigQueryへのデータロードアセットが正しく定義されているか
2. **命名規則**: アセット名がスネークケースで適切に命名されているか（例: `gcs_to_bigquery`, `load_to_bigquery`）
3. **依存関係**: API→GCSステップのアセットへの依存が明示的に定義されているか
4. **BigQuery認証**: BigQuery接続情報が環境変数またはSecret Managerから取得されているか
5. **エラーハンドリング**: データロード時のエラーハンドリングが適切か
6. **GCS読み込み**: GCSからのデータ読み込みが正しく実装されているか
7. **BigQuery書き込み**: BigQueryへのデータ書き込みが正しく実装されているか
8. **テーブル命名規則**: BigQueryテーブル名が適切に命名されているか

違反があれば具体的に指摘し、修正案を提案してください。

