import csv
import json
import re
import time

def process_csv_to_json():
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
                    
                    # 讀取價格
                    kr_sale = int(row.get("KRW Price", 0) or row.get("Korean Price", 0) or 0)
                    manual_hkd = int(row.get("Manual Price HKD", 0) or 0)

                    # 讀取日期欄位
                    promo_start = row.get("Promo Start", "").strip() or None
                    promo_end = row.get("Promo End", "").strip() or None
                    extra_start = row.get("Extra Start", "").strip() or None
                    extra_end = row.get("Extra End", "").strip() or None

                    prices_data["products"][goods_no] = {
                        "kr_original_price_krw": kr_sale,
                        "kr_sale_price_krw": kr_sale,
                        "kr_payment_price_krw": kr_sale,
                        "manual_hkd": manual_hkd if manual_hkd > 0 else None,
                        "promo_start": promo_start,
                        "promo_end": promo_end,
                        "extra_start": extra_start,
                        "extra_end": extra_end,
                        "price_status": "OK" if (kr_sale > 0 or manual_hkd > 0) else "ERROR",
                        "price_updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
                    }
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    with open("oliveyoung_prices.json", mode="w", encoding="utf-8") as f:
        json.dump(prices_data, f, ensure_ascii=False, indent=2)
    print("oliveyoung_prices.json successfully updated with dates from CSV!")

if __name__ == "__main__":
    process_csv_to_json()
