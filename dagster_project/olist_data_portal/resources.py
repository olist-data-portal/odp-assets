from dagster import ConfigurableResource, EnvVar
from google.cloud import bigquery, storage


class BigQueryResource(ConfigurableResource):
    """BigQueryクライアントリソース"""

    project_id: str = EnvVar("GCP_PROJECT_ID")

    def get_client(self) -> bigquery.Client:
        """BigQueryクライアントを取得"""
        return bigquery.Client(project=self.project_id)


class GcsResource(ConfigurableResource):
    """GCSクライアントリソース"""

    project_id: str = EnvVar("GCP_PROJECT_ID")

    def get_client(self) -> storage.Client:
        """GCSクライアントを取得"""
        return storage.Client(project=self.project_id)

    def get_bucket(self, bucket_name: str) -> storage.Bucket:
        """GCSバケットを取得"""
        return self.get_client().bucket(bucket_name)

