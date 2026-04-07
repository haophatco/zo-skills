---
name: mat-viet-weekly-ops
description: "Weekly operations review and action planning for Mắt Việt Group (MVG). Analyzes daily sales Excel files, tracks progress vs previous week's actions, generates CEO-level insights with store-by-store breakdown. Triggers: user uploads MatViet_Daily SalesReport Excel, or mentions 'họp tuần', 'weekly ops', 'phân tích doanh số', 'action plan tuần', 'review cửa hàng'."
compatibility: Created for Zo Computer
metadata:
  author: hana.zo.computer
---
# Mắt Việt Weekly Ops Review Skill

## WORKFLOW KHI NHẬN FILE MỚI

### Bước 1 — Đọc Memory tuần trước

Luôn đọc 2 files này TRƯỚC khi phân tích:

1. `file Documents/MVG-Weekly-Ops-Tracker.md` — Action items từ tuần trước + KPI targets
2. `Documents/MVG-Weekly-History/` — Tìm file tuần gần nhất (e.g. W13-2026-Summary.md)

### Bước 2 — Extract data từ Excel

Chạy script để lấy data:

```bash
python3 Skills/mat-viet-weekly-ops/scripts/extract_weekly.py "<file_path>"
```

Script sẽ extract:

- OPS sheet: Weekly revenue by store type + individual stores
- DAY sheet: Daily per-store performance (TY, FCST, GOAL, LY, CR%)
- SUMMARY sheet: MTD, QTD, YTD
- Weekly sheet: Product mix (Sun/Lens/Frames)

### Bước 3 — Progress Review (quan trọng nhất!)

So sánh TỪNG action từ tuần trước với data tuần này:

```markdown
Format progress review:
✅ DONE / 📈 IMPROVING / ⚠️ NO CHANGE / 🔴 WORSE

[Action W(n-1)] → [KPI target] → [Kết quả thực tế W(n)] → [Đánh giá]
```

### Bước 4 — Phân tích tuần này

Theo retail causal chain: Traffic → CR → ATV/UPT → Mix → Margin

**Store scoring per week:**

- ⭐ Star: vs Goal ≥+10%
- ✅ On Track: vs Goal 0% đến +10%
- 🟡 Watch: vs Goal -10% đến 0%
- 🔴 Action: vs Goal &lt; -10%
- 💀 Critical: vs Goal &lt; -30%

### Bước 5 — Output structure

```markdown
1. PROGRESS REVIEW — Actions W(n-1) → Kết quả tuần này
2. TỔNG QUAN TUẦN — Key metrics table (vs Fcst, vs Target, vs LY)
3. SCOREBOARD CỬA HÀNG — Tất cả 30 CH với rating
4. TOP 5 / BOTTOM 5 — Analysis chi tiết
5. RED FLAGS — Alerts cần xử lý ngay
6. ROOT CAUSE — Retail causal chain
7. ACTION PLAN TUẦN TỚI — What/Who/When/KPI
8. AGENDA HỌP — 60 phút structured
```

### Bước 6 — Cập nhật Memory

Sau khi phân tích xong, tạo/cập nhật:

1. `file Documents/MVG-Weekly-History/W[XX]-[Year]-Summary.md` — Lưu summary tuần này
2. `file Documents/MVG-Weekly-Ops-Tracker.md` — Cập nhật actions mới

## KPI BENCHMARKS

| KPI | Benchmark | Critical threshold |
| --- | --- | --- |
| CR (Conversion Rate) | ≥20% | &lt;15% = Emergency |
| Traffic growth | &gt;14.2% vs LY | &lt;-5% = Alert |
| SUN AUR | ≥80K VND | &lt;60K = Alert |
| UPDPS (Sun) | ≥2.0 | &lt;1.5 = Alert |
| CPUPD | ≥1.5 | &lt;1.0 = Alert |
| vs Target | ≥0% | &lt;-10% = Red flag |

## STORE TYPES

- **Boutique (14 CH)**: AEON/Vincom locations — high traffic, lower CR
- **Counter w.Refraction (6 CH)**: Premium eye exam centers — lower traffic, higher ATV
- **Street (10 CH)**: Standalone stores — highest CR, community-focused
- **Event/Other**: Variable

## PHÂN TÍCH NGUYÊN NHÂN CR THẤP

Khi CR &lt; benchmark, diagnose theo:

1. **Traffic mix**: Khách mục tiêu hay "window shoppers"?
2. **Greeting rate**: NV có tiếp cận đủ khách không?
3. **Consultation quality**: Có đủ bước Try-on, Discover needs?
4. **Objection handling**: Lý do từ chối phổ biến?
5. **Product availability**: Hết hàng SKU cần thiết?

## REFERENCES

- KPI benchmarks: `file Skills/mat-viet-weekly-ops/references/kpi-benchmarks.md`
- Action plan framework: `file Skills/mat-viet-weekly-ops/references/action-plan-framework.md`
- Weekly history: `Documents/MVG-Weekly-History/`
- Rolling tracker: `file Documents/MVG-Weekly-Ops-Tracker.md`