import csv
import json
import re
import time
from playwright.sync_api import sync_playwright

def scrape_oliveyoung():
    prices_data = {"products": {}, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00")}
    
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
        print("No valid Olive Young items found in CSV.")
        return

    with sync_playwright() as p:
        # 啟動真實 Chromium 瀏覽器，模擬韓國使用者環境
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        page = context.new_page()

        for item in items:
            goods_no = item["goods_no"]
            url = item["url"]
            print(f"Scraping goodsNo: {goods_no}...")

            kr_original = 0
            kr_sale = 0
            extra_price = 0
            promo_start = None
            promo_end = None
            extra_start = None
            extra_end = None
            status = "ERROR"

            try:
                # 前往商品頁面
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)

                # 讀取原價與促銷折後價
                try:
                    price_text = page.locator(".price-info .tx_cur .tx_num, .price .tx_num, .p-price .tx_num").first.inner_text()
                    kr_sale = int(re.sub(r"\D", "", price_text))
                except Exception:
                    pass

                try:
                    org_text = page.locator(".price-info .tx_org .tx_num, .price .tx_org").first.inner_text()
                    kr_original = int(re.sub(r"\D", "", org_text))
                except Exception:
                    kr_original = kr_sale

                # 嘗試點開「혜택정보」（優惠明細）彈窗
                try:
                    benefit_btn = page.locator("text='혜택정보', text='쿠폰', .btn_benefit").first
                    if benefit_btn.is_visible():
                        benefit_btn.click()
                        page.wait_for_timeout(1000)

                        # 讀取彈窗內的時間與優惠價格
                        popup_text = page.locator(".pop_layer, .layer_area, .benefit_info").inner_text()
                        
                        # 擷取日期格式 YYYY.MM.DD 或 MM.DD
                        dates = re.findall(r"(\d{2}\.\d{2})\s*~\s*(\d{2}\.\d{2})", popup_text)
                        if dates:
                            promo_start = dates[0][0].replace(".", "-")
                            promo_end = dates[0][1].replace(".", "-")

                        # 擷取 Coupon 額外折後價
                        coupon_prices = re.findall(r"(\d{1,3}(?:,\d{3})*)\s*원", popup_text)
                        if coupon_prices:
                            parsed_prices = [int(p.replace(",", "")) for p in coupon_prices if int(p.replace(",", "")) < kr_sale]
                            if parsed_prices:
                                extra_price = min(parsed_prices)
                except Exception as b_err:
                    print(f"Benefit popup note for {goods_no}: {b_err}")

                if kr_sale > 0:
                    status = "OK"

            except Exception as page_err:
                print(f"Error loading {goods_no}: {page_err}")

            prices_data["products"][goods_no] = {
                "kr_original_price_krw": kr_original,
                "kr_sale_price_krw": kr_sale,
                "extra_price_krw": extra_price if extra_price > 0 else None,
                "promo_start": promo_start,
                "promo_end": promo_end,
                "extra_start": extra_start,
                "extra_end": extra_end,
                "price_status": status,
                "price_updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
            }

        browser.close()

    # 寫入 JSON
    with open("oliveyoung_prices.json", mode="w", encoding="utf-8") as f:
        json.dump(prices_data, f, ensure_ascii=False, indent=2)
    print("oliveyoung_prices.json successfully updated!")

if __name__ == "__main__":
    scrape_oliveyoung()
