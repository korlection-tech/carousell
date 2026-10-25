import csv
import json
import os
import re
import time
import requests

def scrape_via_apify_official():
    api_token = os.environ.get("APIFY_TOKEN")
    if not api_token:
        print("Error: APIFY_TOKEN is missing.")
        return

    # 1. 讀取 CSV 內的商品網址
    start_urls = []
    try:
        with open("pricelist.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("Olive Young URL", "").strip()
                if url and "oliveyoung.co.kr" in url:
                    start_urls.append({"url": url})
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if not start_urls:
        print("No URLs found in CSV.")
        return

    print(f"Sending {len(start_urls)} URLs to Apify...")

    # 2. 使用 Apify 官方最穩定的 Olive Young Scraper 模組
    # 這是 Apify 上目前最常用的爬蟲專用代碼
    actor_id = "cocomoon~oliveyoung-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={api_token}"
    
    payload = {
        "startUrls": start_urls
    }

    res = requests.post(run_url, json=payload)
    if res.status_code != 201:
        print(f"Failed to trigger Apify: {res.text}")
        return

    run_data = res.json().get("data", {})
    run_id = run_data.get("id")
    dataset_id = run_data.get("defaultDatasetId")
    print(f"Apify job started (Run ID: {run_id}). Waiting...")

    # 3. 等待 Apify 爬蟲執行完成（最多等待 3 分鐘）
    for _ in range(36):
        time.sleep(5)
        status_res = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}?token={api_token}").json()
        status = status_res.get("data", {}).get("status")
        print(f"Status: {status}")
        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
            print("Apify execution failed.")
            return

    # 4. 下載 Apify 抓取下來的資料
    items_res = requests.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={api_token}&format=json")
    if items_res.status_code != 200:
        print("Failed to fetch dataset.")
        return

    items = items_res.json()

    # 5. 寫入 oliveyoung_prices.json
    prices_data = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "products": {}
    }

    for item in items:
        url = item.get("url", "") or item.get("productUrl", "")
        match = re.search(r"goodsNo=([A-Z0-9]+)", url)
        if match:
            goods_no = match.group(1)
            
            # 支援多種常見的價格欄位名稱，確保不會抓到 0
            sale_price = int(
                item.get("price") or 
                item.get("salePrice") or 
                item.get("discountPrice") or 
                item.get("realPrice") or 0
            )
            orig_price = int(
                item.get("originalPrice") or 
                item.get("orgPrice") or 
                sale_price
            )
            if orig_price == 0:
                orig_price = sale_price

            prices_data["products"][goods_no] = {
                "kr_original_price_krw": orig_price,
                "kr_sale_price_krw": sale_price,
                "kr_payment_price_krw": sale_price,
                "price_status": "OK" if sale_price > 0 else "ERROR",
                "price_updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
            }

    with open("oliveyoung_prices.json", mode="w", encoding="utf-8") as f:
        json.dump(prices_data, f, ensure_ascii=False, indent=2)
    print("Successfully generated oliveyoung_prices.json via Apify!")

if __name__ == "__main__":
    scrape_via_apify_official()
