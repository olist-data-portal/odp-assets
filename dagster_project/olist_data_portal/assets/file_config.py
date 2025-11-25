"""ファイル設定の一元管理"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class FileConfig:
    """ファイルごとの設定"""

    filename: str
    description: str
    domain: str
    data_type: Literal["transactional", "master", "reference"]
    is_incremental: bool = False


# 全ファイルの設定を一元管理
FILE_CONFIGS: dict[str, FileConfig] = {
    "olist_orders_dataset.csv": FileConfig(
        filename="olist_orders_dataset.csv",
        description="注文データ",
        domain="orders",
        data_type="transactional",
        is_incremental=True,
    ),
    "olist_customers_dataset.csv": FileConfig(
        filename="olist_customers_dataset.csv",
        description="顧客データ",
        domain="customers",
        data_type="master",
    ),
    "olist_geolocation_dataset.csv": FileConfig(
        filename="olist_geolocation_dataset.csv",
        description="地理情報データ",
        domain="geolocation",
        data_type="reference",
    ),
    "olist_order_items_dataset.csv": FileConfig(
        filename="olist_order_items_dataset.csv",
        description="注文アイテムデータ",
        domain="order_items",
        data_type="transactional",
    ),
    "olist_order_payments_dataset.csv": FileConfig(
        filename="olist_order_payments_dataset.csv",
        description="注文支払いデータ",
        domain="payments",
        data_type="transactional",
    ),
    "olist_order_reviews_dataset.csv": FileConfig(
        filename="olist_order_reviews_dataset.csv",
        description="注文レビューデータ",
        domain="reviews",
        data_type="transactional",
    ),
    "olist_products_dataset.csv": FileConfig(
        filename="olist_products_dataset.csv",
        description="商品データ",
        domain="products",
        data_type="master",
    ),
    "olist_sellers_dataset.csv": FileConfig(
        filename="olist_sellers_dataset.csv",
        description="販売者データ",
        domain="sellers",
        data_type="master",
    ),
    "product_category_name_translation.csv": FileConfig(
        filename="product_category_name_translation.csv",
        description="商品カテゴリ翻訳データ",
        domain="product_categories",
        data_type="reference",
    ),
}

# 全ファイル名のリスト
ALL_OLIST_FILES = list(FILE_CONFIGS.keys())

# インクリメンタル処理が必要なファイル
ORDERS_FILE = "olist_orders_dataset.csv"
