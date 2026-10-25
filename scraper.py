import csv
import json
import re
import urllib.request
from bs4 import BeautifulSoup

# 設定 User-Agent 扮成正常瀏覽器，避免被 Olive Young 擋低
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

prices_data = {"products": {}}

try:
    with open("pricelist.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("Olive Young URL", "")
            match = re.search(r"goodsNo=([A-Z0-9]+)", url)
            if match:
                goods_no = match.group(1)
                
                # 初始化預設結構
                sale_price = 0
                original_price = 0
                
                try:
                    # 抓取 Olive Young 商品頁面
                    req = urllib.request.Request(url, headers=HEADERS)
                    with urllib.request.urlopen(req, timeout=10) as response:
                        html = response.read().decode('utf-8')
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 嘗試從頁面中尋找價格元素 (Olive Young 常見的價錢標籤 class)
                        # 註：如果官網結構調整，可透過這裏微調抓取 selector
                        price_elem = soup.select_sone('.price-info .tx_cur .tx_num') or soup.select('.price .tx_num')
                        if price_elem:
                            price_text = price_elem[0].get_text().replace(',', '').strip()
                            sale_price = int(re.sub(r'\D', '', price_text))
                            
                        # 如果抓不到自動售價，先略過讓網站顯示手動價或稍後更新
                except Exception as net_err:
                    print(f"Network error for {goods_no}: {net_err}")

                # 暫存結果 (如果爬蟲暫時未擷取到，會保留 0，前端則會顯示備用狀態)
                prices_data["products"][goods_no] = {
                    "kr_original_price_krw": original_price,
                    "kr_sale_price_krw": sale_price,
                    "discount_rate": 0,
                    "in_stock": True,
                    "price_status": "OK" if sale_price > 0 else "PENDING"
                }
                
except Exception as e:
    print(f"Error reading CSV: {e}")

# 輸出 JSON 檔案供前端網頁讀取
with open("oliveyoung_prices.json", mode="w", encoding="utf-8") as f:
    json.dump(prices_data, f, ensure_ascii=False, indent=2)
