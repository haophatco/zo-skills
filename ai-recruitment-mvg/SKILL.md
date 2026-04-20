---
name: ai-recruitment-mvg
description: AI-powered recruitment automation for Mắt Việt Group. Screens CVs, scores candidates, generates tailored interview questions, and drafts offer letters. Reduces HR screening time from 4 hours to 20 minutes per hiring cycle.
compatibility: Created for Zo Computer
metadata:
  author: hana.zo.computer
---

# AI Recruitment Automation — Mắt Việt Group

## Mục đích
Tự động hóa 3 bước tốn thời gian nhất trong quy trình tuyển dụng:
1. **Sàng lọc CV** — AI chấm điểm và tóm tắt ứng viên
2. **Tạo câu hỏi phỏng vấn** — Tùy biến theo từng CV
3. **Draft offer letter** — Tạo thư đề nghị dựa trên vị trí & mức lương

## Chạy script

### 1. Sàng lọc CV (mode mặc định)
```bash
python3 Skills/ai-recruitment-mvg/scripts/screen_cv.py \
  --position "Nhân viên bán hàng" \
  --cv-text "Họ tên: Nguyễn Văn A..."
```
Hoặc từ file:
```bash
python3 Skills/ai-recruitment-mvg/scripts/screen_cv.py \
  --position "Trưởng cửa hàng" \
  --cv /path/to/cv.txt
```

### 2. Câu hỏi phỏng vấn tùy biến
```bash
python3 Skills/ai-recruitment-mvg/scripts/screen_cv.py \
  --position "Trưởng cửa hàng" \
  --cv-text "..." \
  --mode interview
```

### 3. Draft offer letter
```bash
python3 Skills/ai-recruitment-mvg/scripts/screen_cv.py \
  --mode offer \
  --position "Nhân viên bán hàng" \
  --candidate-name "Nguyễn Văn A" \
  --salary 8500000 \
  --start-date "01/05/2026"
```

## Output
- Kết quả in ra terminal ngay lập tức
- Lưu file: `Documents/HR/Recruitment/[mode]_[tên]_[ngày].md`

## Vị trí MVG thường tuyển
- B1: Nhân viên bán hàng, CTV
- B2: Nhân viên tư vấn cao cấp, Kỹ thuật viên
- B3: Tổ trưởng, Nhân viên văn phòng
- B4: Trưởng cửa hàng
- B5: Quản lý khu vực / Giám đốc vùng
