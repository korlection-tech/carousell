import csv
import json
import os
import time
import requests

# Apify 上的 Olive Young 專用 Actor ID
ACTOR_ID = "cocomoon~oliveyoung-scraper" # 或對應的 Actor Endpoint

def scrape_via_apify():
    api_token = os.environ.get("APIFY_TOKEN")
    if not api_token:
        print("Error: APIFY_TOKEN environment variable not set.")
        return

    # 1. 從 pricelist.csv 收集所有 Olive Young 網址
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
        print("No valid Olive Young URLs found in CSV.")
        return

    print(f"Sending {len(start_urls)} URLs to Apify...")

    # 2. 呼叫 Apify API 啟動爬蟲
    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={api_token}"
    payload = {
        "startUrls": start_urls,
        "maxItems": len(start_urls)
    }

    response = requests.post(run_url, json=payload)
    if response.status_code != 201:
        print(f"Failed to start Apify run: {response.text}")
        return

    run_data = response.json().get("data", {})
    run_id = run_data.get("id")
    dataset_id = run_data.get("defaultDatasetId")
    print(f"Apify run started. Run ID: {run_id}. Waiting for completion...")

    # 3. 輪詢檢查 Apify 是否跑完（最多等待 3 分鐘）
    for _ in range(36):
        time.sleep(5)
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={api_token}"
        status_res = requests.get(status_url).json()
        status = status_res.get("data", {}).get("status")
        print(f"Current Apify status: {status}")
        
        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
            print(f"Apify run failed with status: {status}")
            return
    else:
        print("Apify run timed out.")
        return

    # 4. 從 Apify Dataset 下載抓取回來的結果
    items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={api_token}&format=json"
    items_res = requests.get(items_url)
    if items_res.status_code != 200:
        print("Failed to fetch dataset items from Apify.")
        return

    scraped_items = items_res.json()
    
    # 5. 整理並寫入 oliveyoung_prices.json 供前端網頁使用
    prices_data = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "products": {}
    }

    for item in scraped_items:
        # 根據 Apify 回傳的結構提取 goodsNo 與價格
        url = item.get("url", "") or item.get("productUrl", "")
        import re
        match = re.search(r"goodsNo=([A-Z0-9]+)", url)
        if match:
            goods_no = match.group(1)
            
            # 提取原價與折後價
            sale_price = int(item.get("price", 0) or item.get("salePrice", 0) or 0)
            orig_price = int(item.get("originalPrice", 0) or item.get("orgPrice", 0) or sale_price)
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
    print("oliveyoung_prices.json successfully updated via Apify!")

if __name__ == "__main__":
    scrape_via_apify()
