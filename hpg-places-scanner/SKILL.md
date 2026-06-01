---
name: hpg-places-scanner
description: Quét data đại lý/cửa hàng tiềm năng từ Google Places API (chính thống, hợp pháp) cho Hào Phát Group B2B. Lọc theo tỉnh/thành + ngành kính mắt/thời trang, xuất Excel + sync vào HPG_CRM. Use khi cần mở rộng kênh phân phối hoặc enrich danh sách lead B2B.
compatibility: Created for Zo Computer
metadata:
  author: hana.zo.computer
  version: 1.0.0
  owner: Hào Phát Group
---

# HPG Places Scanner

Skill quét dữ liệu doanh nghiệp B2B từ **Google Places API (New)** cho Hào Phát Group.

## Mục đích

Thay thế các phần mềm scrape Google Maps không chính thống (MKT Maps, ...) bằng API chính thức của Google – **hợp pháp 100%, data real-time, an toàn brand**.

## Use cases chính

1. **Mở kênh đại lý mới**: Quét toàn bộ cửa hàng kính mắt theo tỉnh/thành để tiếp cận
2. **Enrich CRM**: Bổ sung SĐT/địa chỉ/website cho danh sách lead hiện có
3. **Cạnh tranh**: Map vị trí đối thủ + đại lý của HPG trong vùng
4. **Trade marketing**: Phân tích mật độ cửa hàng theo brand mix per territory

## Setup (1 lần duy nhất)

### Bước 1: Bật Google Places API
1. Vào https://console.cloud.google.com/
2. Tạo project mới: `hpg-places-scanner`
3. APIs & Services → Library → tìm **Places API (New)** → Enable
4. Credentials → Create API Key → copy key

### Bước 2: Lưu API key vào Zo Secrets
1. Vào [Settings > Advanced](/?t=settings&s=advanced)
2. Add secret: `GOOGLE_PLACES_API_KEY` = `<key vừa copy>`

### Bước 3: Bật billing (bắt buộc, nhưng có $200 free credit/tháng)
1. Console → Billing → Link billing account
2. **Free tier**: Mỗi tháng được $200 credit ≈ 6,000 lượt Text Search miễn phí

## Cách dùng

### Quét cửa hàng theo từ khóa + thành phố
```bash
python3 scripts/scan_places.py \
  --query "cửa hàng kính mắt" \
  --city "Ho Chi Minh City" \
  --output "Documents/Leads/hcmc-eyewear.xlsx"
```

### Quét theo bán kính từ tọa độ
```bash
python3 scripts/scan_places.py \
  --query "shop kính" \
  --lat 10.7769 --lng 106.7009 \
  --radius 5000 \
  --output "Documents/Leads/district1-eyewear.xlsx"
```

### Enrich email từ website (sau khi có data)
```bash
python3 scripts/enrich_emails.py \
  --input "Documents/Leads/hcmc-eyewear.xlsx" \
  --output "Documents/Leads/hcmc-eyewear-enriched.xlsx"
```

## Output schema

File Excel với các cột:
- `place_id` (unique key)
- `name` – Tên cửa hàng
- `address` – Địa chỉ đầy đủ
- `phone` – Số điện thoại
- `website` – Website
- `email` – Email (sau khi enrich)
- `rating` – Đánh giá Google (0-5)
- `user_ratings_total` – Số lượt review
- `business_status` – OPERATIONAL / CLOSED
- `lat`, `lng` – Tọa độ
- `types` – Loại hình kinh doanh
- `opening_hours` – Giờ mở cửa
- `scanned_at` – Timestamp quét

## Chi phí ước tính

| Use case | Số calls | Chi phí |
|---|---|---|
| Quét 1 quận HCMC (~500 shop) | ~520 calls | **Miễn phí** (trong $200 credit) |
| Quét toàn HCMC (~5,000 shop) | ~5,200 calls | ~$80 (~2tr VND) |
| Quét toàn quốc (~50,000 shop) | ~52,000 calls | ~$1,300 (~32tr VND) – làm 1 lần dùng nhiều năm |

## Tích hợp HPG_CRM

Sau khi quét xong, file Excel có thể import trực tiếp vào HPG_CRM qua chức năng Import Excel hiện có.

## Tham khảo

- [Places API Pricing](https://developers.google.com/maps/billing-and-pricing/pricing)
- [Places API Overview](https://developers.google.com/maps/documentation/places/web-service/overview)
- [Field Mask](https://developers.google.com/maps/documentation/places/web-service/text-search#fieldmask)
