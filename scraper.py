import csv
import json
import re
import time
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.oliveyoung.co.kr/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest"
}

def fetch_oliveyoung_price(goods_no):
    # Olive Young 韓國官網內部取得商品價格與優惠資訊的 API
    api_url = f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetailAjax.do?goodsNo={goods_no}"
    
    try:
        res = requests.get(api_url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            html_text = res.text
            
            # 從 API 回傳的 HTML/JSON 數據中提取價格數字
            # 尋找折後價 / 實際售價
            sale_match = re.search(r'class="tx_num"[^>]*>([\d,]+)', html_text) or re.search(r'([1-9]\d{2,3}(?:,\d{3})*)\s*원', html_text)
            org_match = re.search(r'class="tx_org"[^>]*>.*?<span class="tx_num">([\d,]+)', html_text, re.DOTALL)
            
            sale_price = 0
            org_price = 0
            
            if sale_match:
                sale_price = int(sale_match.group(1).replace(",", ""))
            if org_match:
                org_price = int(org_match.group(1).replace(",", ""))
            else:
                org_price = sale_price

            if sale_price > 0:
                return {
                    "kr_original_price_krw": org_price,
                    "kr_sale_price_krw": sale_price,
                    "kr_payment_price_krw": sale_price,
                    "price_status": "OK"
                }
    except Exception as e:
        print(f"Error fetching API for {goods_no}: {e}")
        
    # 如果 Ajax 失敗，退回備用頁面靜態提取
    try:
        page_url = f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={goods_no}"
        res = requests.get(page_url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            prices = re.findall(r'(\d{1,3}(?:,\d{3})+)\s*원', res.text)
            if prices:
                nums = [int(p.replace(',', '')) for p in prices if int(p.replace(',', '')) >= 1000]
                if nums:
                    sale_price = min(nums)
                    org_price = max(nums)
                    return {
                        "kr_original_price_krw": org_price,
                        "kr_sale_price_krw": sale_price,
                        "kr_payment_price_krw": sale_price,
                        "price_status": "OK"
                    }
    except Exception as e:
        print(f"Fallback error for {goods_no}: {e}")

    return {
        "kr_original_price_krw": 0,
        "kr_sale_price_krw": 0,
        "kr_payment_price_krw": 0,
        "price_status": "ERROR"
    }

def main():
    prices_data = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "products": {}
    }

    try:
        with open("pricelist.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("Olive Young URL", "").strip()
                match = re.search(r"goodsNo=([A-Z0-9]+)", url)
                if match:
                    goods_no = match.group(1)
                    print(f"Processing goodsNo: {goods_no}...")
                    data = fetch_oliveyoung_price(goods_no)
                    data["price_updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
                    prices_data["products"][goods_no] = data
                    time.sleep(1) # 避免請求過快
    except Exception as e:
        print(f"Error reading CSV: {e}")

    with open("oliveyoung_prices.json", mode="w", encoding="utf-8") as f:
        json.dump(prices_data, f, ensure_ascii=False, indent=2)
    print("oliveyoung_prices.json updated successfully!")

if __name__ == "__main__":
    main()
