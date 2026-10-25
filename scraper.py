import csv
import json
import re
import time
from playwright.sync_api import sync_playwright

def scrape_oliveyoung():
    prices_data = {"updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"), "products": {}}
    
    # 讀取 CSV 內的商品網址
    items = []
    try:
        with open("pricelist.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("Olive Young URL", "").strip()
                match = re.search(r"goodsNo=([A-Z0-9]+)", url)
                if match:
                    goods_no = match.group(1)
                    items.append({"goods_no": goods_no, "url": url})
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if not items:
        print("No valid Olive Young items found.")
        return

    with sync_playwright() as p:
        # 💡 如果你有穩定的韓國 Proxy，可在此填入（例如：http://ip:port）
        # 留空則會直接嘗試用 GitHub Actions 預設環境連接
        PROXY_SERVER = None  # 範例: "http://183.110.216.159:8090"
        
        launch_options = {
            "headless": True,
            "args": ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
        }
        if PROXY_SERVER:
            launch_options["proxy"] = {"server": PROXY_SERVER}

        browser = p.chromium.launch(**launch_options)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        for item in items:
            goods_no = item["goods_no"]
            url = item["url"]
            print(f"Fetching goodsNo: {goods_no} with proxy={bool(PROXY_SERVER)}...")

            kr_original = 0
            kr_sale = 0
            status = "ERROR"

            try:
                page.goto(url, wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(3000)

                price_selectors = [
                    ".price-info .tx_cur .tx_num",
                    ".price .tx_num",
                    "#contents .price-info .tx_cur",
                    "span.tx_num"
                ]

                for selector in price_selectors:
                    try:
                        elem = page.locator(selector).first
                        if elem.is_visible():
                            txt = elem.inner_text()
                            num = int(re.sub(r"\D", "", txt))
                            if num > 0:
                                kr_sale = num
                                break
                    except Exception:
                        continue

                try:
                    org_elem = page.locator(".price-info .tx_org .tx_num, .price .tx_org").first
                    if org_elem.is_visible():
                        kr_original = int(re.sub(r"\D", "", org_elem.inner_text()))
                except Exception:
                    kr_original = kr_sale

                if kr_sale == 0 and kr_original > 0:
                    kr_sale = kr_original

                if kr_sale > 0:
                    status = "OK"

            except Exception as page_err:
                print(f"Error scraping {goods_no}: {page_err}")

            prices_data["products"][goods_no] = {
                "kr_original_price_krw": kr_original,
                "kr_sale_price_krw": kr_sale,
                "kr_payment_price_krw": kr_sale,
                "price_status": status,
                "price_updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
            }

        browser.close()

    with open("oliveyoung_prices.json", mode="w", encoding="utf-8") as f:
        json.dump(prices_data, f, ensure_ascii=False, indent=2)
    print("oliveyoung_prices.json successfully updated.")

if __name__ == "__main__":
    scrape_oliveyoung()
