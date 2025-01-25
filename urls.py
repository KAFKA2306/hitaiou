import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time
from urllib.parse import urljoin
import json

class BoothScraper:
    def __init__(self):
        """スクレイパーの初期化"""
        self.base_url = "https://booth.pm/ja/browse/3Dモデル"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.results_dir = Path('results')
        self.results_dir.mkdir(exist_ok=True)

    def get_page_content(self, page=1):
        """指定されたページの内容を取得"""
        params = {
            'min_price': '1000',
            'type': 'digital',
            'page': str(page)
        }
        
        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"ページ {page} の取得中にエラーが発生しました: {e}")
            return None

    def parse_items(self, html_content):
        """ページから商品情報を抽出"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        items = []

        # 商品カードを検索
        for item in soup.select('.item-card'):
            try:
                # 商品リンクを取得
                link_elem = item.select_one('.item-card-url')
                if not link_elem:
                    continue

                # 価格を取得
                price_elem = item.select_one('.price')
                price_text = price_elem.text.strip() if price_elem else '0'
                price = int(''.join(filter(str.isdigit, price_text)) or 0)

                # タイトルを取得
                title_elem = item.select_one('.item-card-title')
                title = title_elem.text.strip() if title_elem else 'No Title'

                # 商品情報を格納
                item_info = {
                    'url': urljoin('https://booth.pm', link_elem['href']),
                    'title': title,
                    'price': price
                }
                
                items.append(item_info)
                
            except Exception as e:
                print(f"商品情報の抽出中にエラーが発生しました: {e}")
                continue

        return items

    def save_results(self, items, filename):
        """結果をJSONとCSVで保存"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        base_path = self.results_dir / f"{filename}_{timestamp}"

        # JSONとして保存
        with open(f"{base_path}.json", 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        # CSVとして保存
        df = pd.DataFrame(items)
        df.to_csv(f"{base_path}.csv", index=False, encoding='utf-8')

        print(f"データを保存しました:")
        print(f"- JSON: {base_path}.json")
        print(f"- CSV: {base_path}.csv")
        print(f"取得した商品数: {len(items)}")

    def scrape(self, max_pages=5):
        """指定されたページ数まで商品情報を取得"""
        all_items = []
        
        print("スクレイピングを開始します...")
        
        for page in range(1, max_pages + 1):
            print(f"\nページ {page} を処理中...")
            
            # ページ内容を取得
            content = self.get_page_content(page)
            if not content:
                print(f"ページ {page} の取得に失敗しました。次のページに進みます。")
                continue

            # 商品情報を抽出
            items = self.parse_items(content)
            if not items:
                print(f"ページ {page} に商品が見つかりませんでした。")
                break

            all_items.extend(items)
            print(f"ページ {page} から {len(items)} 件の商品情報を取得しました。")
            
            # サーバーに負荷をかけないよう待機
            time.sleep(2)

        # 結果を保存
        if all_items:
            self.save_results(all_items, 'booth_items')
        else:
            print("商品情報が取得できませんでした。")

def main():
    scraper = BoothScraper()
    scraper.scrape(max_pages=5)  # 最大5ページまで取得

if __name__ == "__main__":
    main()