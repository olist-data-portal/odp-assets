from dagster import Definitions, define_asset_job

from olist_data_portal.assets import (
    gcs_customers_to_bigquery,
    gcs_geolocation_to_bigquery,
    gcs_order_items_to_bigquery,
    gcs_order_payments_to_bigquery,
    gcs_order_reviews_to_bigquery,
    gcs_orders_to_bigquery,
    gcs_product_category_name_translation_to_bigquery,
    gcs_products_to_bigquery,
    gcs_sellers_to_bigquery,
    kaggle_customers_to_gcs,
    kaggle_dataset_download,
    kaggle_geolocation_to_gcs,
    kaggle_order_items_to_gcs,
    kaggle_order_payments_to_gcs,
    kaggle_order_reviews_to_gcs,
    kaggle_orders_to_gcs,
    kaggle_product_category_name_translation_to_gcs,
    kaggle_products_to_gcs,
    kaggle_sellers_to_gcs,
)
from olist_data_portal.resources import BigQueryResource, GcsResource

all_assets = [
    kaggle_dataset_download,
    kaggle_orders_to_gcs,
    kaggle_customers_to_gcs,
    kaggle_geolocation_to_gcs,
    kaggle_order_items_to_gcs,
    kaggle_order_payments_to_gcs,
    kaggle_order_reviews_to_gcs,
    kaggle_products_to_gcs,
    kaggle_sellers_to_gcs,
    kaggle_product_category_name_translation_to_gcs,
    gcs_orders_to_bigquery,
    gcs_customers_to_bigquery,
    gcs_geolocation_to_bigquery,
    gcs_order_items_to_bigquery,
    gcs_order_payments_to_bigquery,
    gcs_order_reviews_to_bigquery,
    gcs_products_to_bigquery,
    gcs_sellers_to_bigquery,
    gcs_product_category_name_translation_to_bigquery,
]

olist_data_portal_job = define_asset_job(
    name="olist_data_portal_job",
    selection=all_assets,
    description="Kaggle APIからデータを取得し、GCSにアップロードし、BigQueryにロードするジョブ",
)

defs = Definitions(
    assets=all_assets,
    jobs=[olist_data_portal_job],
    schedules=[],
    resources={
        "bigquery": BigQueryResource(),
        "gcs": GcsResource(),
    },
)
