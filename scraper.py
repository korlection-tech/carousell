import csv
import json
import re
import requests

# 讀取 CSV 內的商品網址
prices_data = {"products": {}}

try:
    with open("pricelist.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("Olive Young URL", "")
            match = re.search(r"goodsNo=([A-Z0-9]+)", url)
            if match:
                goods_no = match.group(1)
                
                # 實際應用中，此處會對 Olive Young 進行請求或透過 API 取得 JSON 價格
                # 以下為結構示範：
                prices_data["products"][goods_no] = {
                    "kr_original_price_krw": 33000,
                    "kr_sale_price_krw": 27000,
                    "discount_rate": 18,
                    "in_stock": True,
                    "price_status": "OK"
                }
except Exception as e:
    print(f"Error reading CSV: {e}")

# 寫入 oliveyoung_prices.json 供前端 HTML 讀取
with open("oliveyoung_prices.json", mode="w", encoding="utf-8") as f:
    json.dump(prices_data, f, ensure_ascii=False, indent=2)
