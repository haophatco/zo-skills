#!/usr/bin/env python3
"""
AI Recruitment Automation — Mắt Việt Group
Sàng lọc CV, tạo câu hỏi phỏng vấn, draft offer letter bằng AI.
"""
import argparse
import json
import os
import sys
import re
import requests
from datetime import datetime
from pathlib import Path

WORKSPACE = "/home/workspace"
OUTPUT_DIR = f"{WORKSPACE}/Documents/HR/Recruitment"
ZO_API = "https://api.zo.computer/zo/ask"
MODEL = "byok:5879247b-059d-480c-8e71-a4fb1ce36ed6"

MVG_CONTEXT = """
Công ty: Mắt Việt Group (MVG) — chuỗi bán lẻ mắt kính chính hãng hàng đầu Việt Nam
- 30+ năm kinh nghiệm, 30+ cửa hàng toàn quốc
- Phân phối độc quyền các thương hiệu: Essilor, Luxottica, Hoya, Zeiss, Ray-Ban, Oakley
- Giá trị cốt lõi: Chuyên nghiệp, Trung thực, Dịch vụ xuất sắc, Teamwork
- Môi trường: năng động, target-driven, đào tạo bài bản

Tiêu chí chung MVG:
- Giao tiếp tốt, nụ cười thân thiện (đặc biệt vị trí B1-B2)
- Định hướng phục vụ khách hàng
- Sẵn sàng học hỏi, chịu áp lực doanh số
- Trung thực, không có tiền án tiền sự
- Ưu tiên: kinh nghiệm retail, bán hàng trực tiếp, chăm sóc KH
"""

BAND_SALARY = {
    "b1": (7_000_000, 9_000_000),
    "b2": (9_000_000, 13_000_000),
    "b3": (13_000_000, 18_000_000),
    "b4": (18_000_000, 25_000_000),
    "b5": (25_000_000, 45_000_000),
}

POSITION_BAND = {
    "nhân viên bán hàng": "b1",
    "ctv": "b1",
    "cộng tác viên": "b1",
    "nhân viên tư vấn": "b2",
    "kỹ thuật viên": "b2",
    "tổ trưởng": "b3",
    "nhân viên văn phòng": "b3",
    "trưởng cửa hàng": "b4",
    "store manager": "b4",
    "quản lý khu vực": "b5",
    "giám đốc vùng": "b5",
    "area manager": "b5",
}


def get_band(position: str) -> str:
    pos_lower = position.lower()
    for key, band in POSITION_BAND.items():
        if key in pos_lower:
            return band
    return "b2"


def call_zo_api(prompt: str) -> str:
    token = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")
    if not token:
        print("❌ Lỗi: Không tìm thấy ZO_CLIENT_IDENTITY_TOKEN", file=sys.stderr)
        sys.exit(1)

    resp = requests.post(
        ZO_API,
        headers={"authorization": token, "content-type": "application/json"},
        json={"input": prompt, "model_name": MODEL},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["output"]


def screen_cv(position: str, cv_text: str) -> str:
    band = get_band(position)
    salary_range = BAND_SALARY.get(band, (9_000_000, 13_000_000))

    prompt = f"""Bạn là HR Manager chuyên nghiệp của Mắt Việt Group (MVG).

{MVG_CONTEXT}

VỊ TRÍ TUYỂN DỤNG: {position} (Band {band.upper()})
Dải lương: {salary_range[0]:,} – {salary_range[1]:,} VND/tháng

NỘI DUNG CV ỨNG VIÊN:
---
{cv_text}
---

Hãy phân tích CV theo format sau (dùng tiếng Việt, ngắn gọn, thẳng thắn):

## ĐIỂM TỔNG HỢP
**Điểm phù hợp: X/10** (chỉ 1 con số)
**Khuyến nghị:** ✅ Mời phỏng vấn / ⚠️ Cân nhắc / ❌ Không phù hợp

## TÓM TẮT ỨNG VIÊN (3 dòng)
- Họ tên, tuổi, địa chỉ (nếu có)
- Kinh nghiệm nổi bật nhất
- Điểm mạnh cốt lõi cho vị trí này

## ĐIỂM MẠNH (tối đa 3 gạch đầu dòng)

## RED FLAGS (tối đa 3 gạch đầu dòng, nếu không có ghi "Không phát hiện")

## ĐỀ XUẤT MỨC LƯƠNG KHỞI ĐIỂM
Dựa trên kinh nghiệm: X,XXX,XXX VND (trong dải {salary_range[0]:,}–{salary_range[1]:,})

## LÝ DO QUYẾT ĐỊNH (2-3 câu ngắn gọn)
"""
    return call_zo_api(prompt)


def generate_interview_questions(position: str, cv_text: str) -> str:
    band = get_band(position)
    prompt = f"""Bạn là HR Manager của Mắt Việt Group (MVG).

{MVG_CONTEXT}

VỊ TRÍ: {position} (Band {band.upper()})

CV ỨNG VIÊN:
---
{cv_text}
---

Tạo bộ câu hỏi phỏng vấn TÙY BIẾN theo CV này. Format:

## BỘ CÂU HỎI PHỎNG VẤN — {position.upper()}
**Thời gian phỏng vấn:** 30-45 phút
**Người phỏng vấn:** HR + Quản lý trực tiếp

---

### PHẦN 1 — Làm quen (5 phút)
1. [Câu hỏi mở đầu nhẹ nhàng, liên quan đến background ứng viên]
2. [Câu hỏi về động lực ứng tuyển vào MVG cụ thể]

### PHẦN 2 — Kinh nghiệm & Kỹ năng (15 phút)
3. [Câu hỏi khai thác kinh nghiệm liên quan nhất trong CV]
4. [Câu hỏi về thành tích/kết quả cụ thể đã đạt được]
5. [Câu hỏi tình huống dựa trên kinh nghiệm của ứng viên]

### PHẦN 3 — Phù hợp văn hóa MVG (10 phút)
6. [Câu hỏi về cách xử lý khách hàng khó tính]
7. [Câu hỏi về teamwork và áp lực doanh số]
8. [Câu hỏi về định hướng phát triển 1-2 năm tới]

### PHẦN 4 — Câu hỏi thực tế vị trí (10 phút)
9. [Câu hỏi kỹ thuật/chuyên môn cụ thể cho vị trí {position}]
10. [Câu hỏi tình huống thực tế tại cửa hàng MVG]

---
### DẤU HIỆU PASS / FAIL
✅ **Pass nếu:** [3 dấu hiệu tích cực cần nghe trong buổi phỏng vấn]
❌ **Fail ngay nếu:** [2-3 red flag cần loại ngay]

Lưu ý: Câu hỏi phải TÙY BIẾN theo CV, không chung chung. Đề cập tên công ty cũ, vị trí cũ, hoặc điểm cụ thể trong CV.
"""
    return call_zo_api(prompt)


def generate_offer_letter(position: str, candidate_name: str, salary: int, start_date: str) -> str:
    band = get_band(position)
    today = datetime.now().strftime("%d/%m/%Y")
    prompt = f"""Bạn là HR Manager của Mắt Việt Group (MVG). Viết thư đề nghị làm việc (offer letter) chuyên nghiệp bằng tiếng Việt.

Thông tin:
- Ứng viên: {candidate_name}
- Vị trí: {position}
- Band: {band.upper()}
- Lương cơ bản: {salary:,} VND/tháng
- Ngày bắt đầu: {start_date}
- Ngày tạo thư: {today}
- Thử việc: 60 ngày (hưởng 85% lương)
- Chế độ: BHXH/BHYT/BHTN theo luật, thưởng KPI hàng tháng

Format thư:
---
CÔNG TY TNHH MẮT VIỆT GROUP
[Địa chỉ: 123 Đường ABC, Quận X, TP.HCM]
ĐT: (028) xxxx-xxxx | Email: hr@matviet.com.vn

                                        TP. Hồ Chí Minh, ngày {today}

THƯ ĐỀ NGHỊ CÔNG TÁC

Kính gửi: {candidate_name}

[Nội dung chuyên nghiệp, thân thiện, khoảng 200-250 từ bao gồm:
- Chúc mừng và đề nghị vị trí
- Các điều khoản chính: lương, ngày bắt đầu, thử việc
- Chế độ phúc lợi nổi bật
- Deadline xác nhận (5 ngày làm việc)
- Câu kết thúc tích cực]

Trân trọng,

_______________________
[Tên HR Manager]
HR Manager — Mắt Việt Group
---

Thư phải súc tích, chuyên nghiệp, thể hiện văn hóa MVG (nhiệt tình, chuyên nghiệp, cơ hội phát triển).
"""
    return call_zo_api(prompt)


def save_output(content: str, mode: str, name: str) -> str:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    safe_name = re.sub(r"[^\w\-]", "_", name)[:30]
    filename = f"{OUTPUT_DIR}/{mode}_{safe_name}_{date_str}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename


def main():
    parser = argparse.ArgumentParser(description="AI Recruitment Tool — Mắt Việt Group")
    parser.add_argument("--mode", choices=["screen", "interview", "offer"], default="screen",
                        help="screen=sàng lọc CV, interview=câu hỏi PV, offer=thư đề nghị")
    parser.add_argument("--position", required=True, help="Vị trí tuyển dụng")
    parser.add_argument("--cv", help="Đường dẫn file CV (.txt)")
    parser.add_argument("--cv-text", help="Nội dung CV dán trực tiếp")
    parser.add_argument("--candidate-name", default="Ứng viên", help="Tên ứng viên (dùng cho offer)")
    parser.add_argument("--salary", type=int, help="Mức lương đề nghị (VND)")
    parser.add_argument("--start-date", default="01/06/2026", help="Ngày bắt đầu (offer)")
    parser.add_argument("--no-save", action="store_true", help="Không lưu file, chỉ in ra terminal")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"🔍 AI Recruitment — Mắt Việt Group")
    print(f"Mode: {args.mode.upper()} | Vị trí: {args.position}")
    print(f"{'='*60}\n")

    result = ""

    if args.mode in ("screen", "interview"):
        cv_text = ""
        if args.cv:
            with open(args.cv, "r", encoding="utf-8") as f:
                cv_text = f.read()
        elif args.cv_text:
            cv_text = args.cv_text
        else:
            print("❌ Lỗi: Cần cung cấp --cv hoặc --cv-text cho mode screen/interview")
            sys.exit(1)

        print("⏳ Đang phân tích bằng AI... (10-20 giây)\n")

        if args.mode == "screen":
            result = screen_cv(args.position, cv_text)
            save_name = args.candidate_name
        else:
            result = generate_interview_questions(args.position, cv_text)
            save_name = args.candidate_name

    elif args.mode == "offer":
        if not args.salary:
            band = get_band(args.position)
            lo, hi = BAND_SALARY.get(band, (9_000_000, 13_000_000))
            args.salary = (lo + hi) // 2
            print(f"ℹ️  Không có --salary, dùng mức trung bình band: {args.salary:,} VND\n")

        print("⏳ Đang tạo offer letter... (10-20 giây)\n")
        result = generate_offer_letter(args.position, args.candidate_name, args.salary, args.start_date)
        save_name = args.candidate_name

    print(result)

    if not args.no_save:
        saved_path = save_output(result, args.mode, save_name)
        print(f"\n{'='*60}")
        print(f"✅ Đã lưu: {saved_path}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
