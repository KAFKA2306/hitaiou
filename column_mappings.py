"""
Column mappings for data processing
This file contains mappings between original column names and their standardized versions
"""

FORM_COLUMNS = {
    'タイムスタンプ': 'timestamp',
    '非対応改変したいアバターのBooth URLを入れてください。(https://booth.pm/{language}/items/{item_id})': 'avatar_url',
    '非対応改変したい衣装のBooth URLを入れてください。(https://booth.pm/{language}/items/{item_id})': 'item_url',
    'あなたのTwitter IDを書いてください。非対応改変が確定した際の連絡にのみ使用します。（https://x.com/{twitter_id}）': 'twitter_id',
    '参考に、希望改変価格を書いてください。非対応改変作業者とのマッチング率に影響します。': 'desired_price',
    '参考に、希望する非対応改変作業者を書いてください。': 'hitaiou_worker_name'
}

# Add reverse mapping for easier lookups
REVERSE_FORM_COLUMNS = {v: k for k, v in FORM_COLUMNS.items()}

# Output column names for processed data
PROCESSED_COLUMNS = [
    'timestamp',
    'avatar_url',
    'item_url',
    'twitter_id',
    'desired_price',
    'hitaiou_worker_name',
    'avatar_shop_id',
    'avatar_item_id',
    'item_shop_id',
    'item_item_id',
    'is_avatar'
]

# Dashboard metric column names
DASHBOARD_COLUMNS = [
    'avatar_id',
    'item_id',
    'request_count',
    'unique_users',
    'median_price',
    'mean_price',
    'min_price',
    'max_price',
    'price_std',
    'potential_sales'
]