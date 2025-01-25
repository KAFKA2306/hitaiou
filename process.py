import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
import requests
from datetime import datetime
import re
from typing import Optional, Tuple
from urllib.parse import urlparse
import json
from config_handler import load_config
from column_mappings import FORM_COLUMNS, PROCESSED_COLUMNS, DASHBOARD_COLUMNS

class DataProcessor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.dashboard_dir = self.data_dir / "dashboard"
        
        self.raw_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)
        self.dashboard_dir.mkdir(exist_ok=True)

    def download_spreadsheet(self, spreadsheet_id: str, api_key: str) -> Optional[pd.DataFrame]:
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_path = self.raw_dir / f"raw_data_{timestamp}.csv"
            
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A:Z"
            params = {
                'key': api_key,
                'majorDimension': 'ROWS',
                'valueRenderOption': 'UNFORMATTED_VALUE'
            }
            
            print("Downloading spreadsheet using Google Sheets API...")
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json().get('values', [])
                if not data:
                    print("No data found in spreadsheet")
                    return None
                    
                headers = data[0]
                df = pd.DataFrame(data[1:], columns=headers)
                
                # Save raw data before column mapping
                df.to_csv(csv_path, index=False)
                print(f"Raw data saved to: {csv_path}")
                print(f"Downloaded {len(df)} rows")
                print(f"Original columns: {headers}")
                
                # Apply column mapping
                df = df.rename(columns=FORM_COLUMNS)
                print(f"Mapped columns: {df.columns.tolist()}")
                
                return df
            else:
                print(f"Failed to download spreadsheet. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error downloading spreadsheet: {str(e)}")
            return None

    @staticmethod
    def extract_booth_info(url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract shop_id and item_id from Booth URLs with improved pattern matching"""
        if pd.isna(url):
            return (None, None)
            
        if isinstance(url, (int, float)):
            return (None, str(int(url)))
        
        if not isinstance(url, str):
            return (None, None)
            
        if url.isdigit():
            return (None, url)
            
        try:
            # パターンを改善：言語指定やショップIDの有無に対応
            patterns = [
                # Standard shop URL: https://shop.booth.pm/items/123
                r'https://([^.]+)\.booth\.pm/items/(\d+)',
                # Language-specific URL: https://booth.pm/ja/items/123
                r'https://booth\.pm/[^/]+/items/(\d+)',
                # Direct item URL: https://booth.pm/items/123
                r'https://booth\.pm/items/(\d+)',
            ]
            
            url = url.strip()
            
            for pattern in patterns:
                match = re.match(pattern, url)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        return groups
                    elif len(groups) == 1:
                        # 言語指定URLの場合はitem_idのみ取得
                        return (None, groups[0])
            
            # item_idだけを抽出してみる最後の手段
            item_id_pattern = r'/items/(\d+)'
            match = re.search(item_id_pattern, url)
            if match:
                return (None, match.group(1))
            
            print(f"Warning: Could not parse Booth URL: {url}")
            return (None, None)
            
        except Exception as e:
            print(f"Error processing URL {url}: {str(e)}")
            return (None, None)

    def process_raw_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        try:
            if df is None or df.empty:
                print("No data to process")
                return None
                
            print("Processing raw data...")
            print("Input columns:", df.columns.tolist())
            
            # データの内容を確認
            print("\nSample of input data:")
            print(df[['avatar_url', 'item_url']].head())
            
            # Process URLs and extract IDs
            df['avatar_info'] = df['avatar_url'].apply(self.extract_booth_info)
            df['item_info'] = df['item_url'].apply(self.extract_booth_info)
            
            print("\nExtracted URL info:")
            print(pd.DataFrame({
                'avatar_url': df['avatar_url'],
                'avatar_info': df['avatar_info'],
                'item_url': df['item_url'],
                'item_info': df['item_info']
            }).head())
            
            # Extract shop_id and item_id
            df['avatar_shop_id'] = df['avatar_info'].apply(lambda x: x[0] if x else None)
            df['avatar_item_id'] = df['avatar_info'].apply(lambda x: x[1] if x else None)
            df['item_shop_id'] = df['item_info'].apply(lambda x: x[0] if x else None)
            df['item_item_id'] = df['item_info'].apply(lambda x: x[1] if x else None)
            
            # Clean price data - handle potential non-numeric values
            df['desired_price'] = pd.to_numeric(
                df['desired_price'].astype(str).str.extract(r'(\d+)')[0], 
                errors='coerce'
            ).fillna(0)  # 価格が指定されていない場合は0を設定
            
            # Drop temporary columns
            df = df.drop(['avatar_info', 'item_info'], axis=1)
            
            # フィルタリング条件を緩和：item_idのどちらかが存在すれば良い
            df = df[df['avatar_item_id'].notna() | df['item_item_id'].notna()]
            
            # Add is_avatar column based on URL position
            df['is_avatar'] = 1  # avatarとして指定されたURLは1
            
            # Save processed data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            parquet_path = self.processed_dir / f"processed_data_{timestamp}.parquet"
            
            df.to_parquet(
                parquet_path,
                compression='snappy',
                engine='pyarrow'
            )
            print(f"\nProcessed data saved to: {parquet_path}")
            print("Output columns:", df.columns.tolist())
            print("\nProcessed data summary:")
            print(df)
            
            return df
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            print("Current DataFrame columns:", df.columns.tolist())
            raise

    def prepare_dashboard_data(self, df: pd.DataFrame) -> bool:
        try:
            if df is None or df.empty:
                print("No data to prepare for dashboard")
                return False
                
            print("Preparing dashboard data...")
            
            # Calculate demand metrics
            demand_metrics = df.groupby(['avatar_item_id', 'item_item_id']).agg({
                'twitter_id': ['count', 'nunique'],
                'desired_price': ['median', 'mean', 'min', 'max', 'std']
            }).reset_index()
            
            # Flatten column names
            demand_metrics.columns = [
                'avatar_id', 'item_id', 'request_count', 'unique_users',
                'median_price', 'mean_price', 'min_price', 'max_price', 'price_std'
            ]
            
            # Calculate potential sales
            demand_metrics['potential_sales'] = (
                demand_metrics['request_count'] * demand_metrics['median_price']
            )
            
            # Sort by potential sales (highest first)
            demand_metrics = demand_metrics.sort_values('potential_sales', ascending=False)
            
            # Save demand metrics
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            demand_metrics_path = self.dashboard_dir / f"demand_metrics_{timestamp}.parquet"
            demand_metrics.to_parquet(demand_metrics_path, compression='snappy')
            
            print("\nDemand metrics summary:")
            print(demand_metrics)
            print(f"\nDemand metrics saved to: {demand_metrics_path}")
            
            return True
            
        except Exception as e:
            print(f"Error preparing dashboard data: {str(e)}")
            return False

def main():
    config = load_config()
    if config.get('api_key') == 'YOUR-API-KEY':
        print("Please update the API key in config.json")
        return

    processor = DataProcessor()
    
    spreadsheet_id = config.get('spreadsheet_id')
    api_key = config.get('api_key')
    
    print("\n=== Step 1: Downloading Spreadsheet ===")
    raw_data = processor.download_spreadsheet(spreadsheet_id, api_key)
    
    if raw_data is not None:
        print("\n=== Step 2: Processing Raw Data ===")
        processed_data = processor.process_raw_data(raw_data)
        
        if processed_data is not None:
            print("\n=== Step 3: Preparing Dashboard Data ===")
            processor.prepare_dashboard_data(processed_data)
            
            print("\nAll processing steps completed successfully!")
        else:
            print("Failed to process raw data")
    else:
        print("Failed to download spreadsheet")

if __name__ == "__main__":
    main()