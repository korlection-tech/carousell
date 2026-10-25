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
                    
                    # 1. 讀取你直接照抄嘅數字
                    orig_price = int(row.get("Original Price", 0) or 0)
                    sale_discount = int(row.get("Sale Discount", 0) or 0)      # 例如 4000
                    coupon_discount = int(row.get("Coupon Discount", 0) or 0)  # 例如 2000
                    manual_hkd = int(row.get("Manual Price HKD", 0) or 0)

                    # 2. 讓程式自動做減法，完全唔使你心算！
                    sale_price = orig_price - sale_discount if orig_price > 0 else 0
                    coupon_price = sale_price - coupon_discount if coupon_discount > 0 else None
                    
                    # 最終用來算港幣代購價的韓元金額 (有 Coupon 優先用 Coupon 價)
                    final_payment_price = coupon_price if coupon_price else sale_price

                    # 3. 讀取日期
                    promo_start = row.get("Promo Start", "").strip() or None
                    promo_end = row.get("Promo End", "").strip() or None
                    extra_start = row.get("Extra Start", "").strip() or None
                    extra_end = row.get("Extra End", "").strip() or None

                    prices_data["products"][goods_no] = {
                        "kr_original_price_krw": orig_price,
                        "kr_sale_price_krw": sale_price,             # 自動算好 29000
                        "extra_price_krw": coupon_price,             # 自動算好 27000
                        "kr_payment_price_krw": final_payment_price, # 最終計算港幣售價用
                        "manual_hkd": manual_hkd if manual_hkd > 0 else None,
                        "promo_start": promo_start,
                        "promo_end": promo_end,
                        "extra_start": extra_start,
                        "extra_end": extra_end,
                        "price_status": "OK" if (final_payment_price > 0 or manual_hkd > 0) else "ERROR",
                        "price_updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
                    }
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    with open("oliveyoung_prices.json", mode="w", encoding="utf-8") as f:
        json.dump(prices_data, f, ensure_ascii=False, indent=2)
    print("oliveyoung_prices.json updated successfully with auto-calculated discounts!")

if __name__ == "__main__":
    process_csv_to_json()
