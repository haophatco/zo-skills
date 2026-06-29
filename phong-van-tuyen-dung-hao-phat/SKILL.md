---
name: phong-van-tuyen-dung-hao-phat
description: "Tạo bộ câu hỏi phỏng vấn và kịch bản phỏng vấn tuyển dụng chuẩn cho HÀO PHÁT GROUP — nhà phân phối sỉ mắt kính hàng hiệu B2B với hơn 1.000 đại lý toàn quốc và 12 thương hiệu độc quyền (BOLON, MOLSION, GINA, SEROVA, ANCCI, FLYER, VOSS, ZIOZIA, GUCCI, SAINT LAURENT, PUMA, MAUI JIM). BẮT BUỘC dùng skill này khi người dùng nhắc đến: 'tạo câu hỏi phỏng vấn', 'bộ câu hỏi tuyển dụng', 'kịch bản phỏng vấn', 'phỏng vấn nhân viên kinh doanh/sales/đại lý', 'phỏng vấn quản lý vùng', 'phỏng vấn key account', 'phỏng vấn brand manager', 'tuyển nhân viên Hào Phát', 'guide phỏng vấn', 'câu hỏi đánh giá ứng viên', hoặc bất kỳ yêu cầu nào liên quan đến soạn câu hỏi/quy trình phỏng vấn cho một vị trí của Hào Phát. Kích hoạt ngay cả khi yêu cầu ngắn gọn kiểu 'làm cho tôi bộ câu hỏi phỏng vấn sales'. Skill tự nạp hồ sơ năng lực theo vị trí, chèn tình huống thật ngành mắt kính B2B, và áp 'Cổng Công Nợ' để loại sớm ứng viên yếu kỷ luật tiền bạc."
metadata:
  author: Hào Phát Group
  version: "1.0"
---

# Phỏng Vấn Tuyển Dụng — Hào Phát Group

## Khi nào dùng skill này

Dùng skill này khi cần:
- Soạn **bộ câu hỏi phỏng vấn** theo vị trí, phân nhóm rõ ràng (hành vi, tình huống, chuyên môn, văn hóa).
- Xây **kịch bản phỏng vấn** chia theo từng vòng (sàng lọc → chuyên sâu → chung kết).
- Thiết kế câu hỏi **lộ ra năng lực thật**, không phải ứng viên học thuộc câu trả lời.
- Chuẩn hóa câu hỏi để **nhiều người phỏng vấn cùng chấm** trên một thước đo.

**KHÔNG dùng** skill này để: viết JD đăng tuyển, chấm điểm KPI nhân viên đang làm việc (dùng skill `cham-diem-nhan-vien-sales`), hay lên lịch phỏng vấn. Skill này chỉ tạo **câu hỏi + cách chấm**.

---

## Nguyên tắc cốt lõi

> HÀNH VI TRONG QUÁ KHỨ DỰ BÁO HIỆU SUẤT TƯƠNG LAI TỐT HƠN MỌI LỜI HỨA. Với một nhà phân phối sỉ mắt kính B2B, hai thứ quyết định ứng viên kinh doanh sống hay chết là: **(1) khả năng đạt chỉ tiêu trên một địa bàn đại lý** và **(2) kỷ luật công nợ**. Bộ câu hỏi phải đào sâu hai trục này bằng câu hỏi về việc ĐÃ LÀM, không phải việc SẼ LÀM.

---

## QUY TRÌNH 5 BƯỚC (làm tuần tự, không nhảy bước)

### Bước 1 — Xác định vị trí & năng lực cần đánh giá

Hỏi (hoặc suy ra từ ngữ cảnh) các thông tin sau. Nếu người dùng đã nói rõ vị trí, **không hỏi lại những gì đã biết** — chỉ xác nhận nhanh rồi đi tiếp.

| Thông tin | Câu hỏi | Mặc định |
|---|---|---|
| **Vị trí tuyển** | "Anh/chị đang tuyển vị trí nào?" | Không có |
| **Cấp bậc** | "Nhân viên, quản lý cấp trung, hay cấp cao?" | Nhân viên |
| **Năng lực ưu tiên** | "3–5 năng lực quan trọng nhất ở vị trí này là gì?" | Lấy theo hồ sơ năng lực có sẵn |
| **Số vòng phỏng vấn** | "Phỏng vấn mấy vòng?" | 2 vòng |
| **Tiêu chí loại ngay** | "Điều gì khiến loại ứng viên ngay lập tức?" | Theo Cổng Công Nợ + giá trị cốt lõi |

**CHỐT CHẶN:** Xác nhận vị trí + bộ năng lực trước khi soạn câu hỏi.

### Bước 2 — Nạp hồ sơ năng lực theo vị trí

Skill có sẵn hồ sơ năng lực cho các vị trí cốt lõi của Hào Phát. **Đọc đúng file tham chiếu cho vị trí được hỏi:**

| Vị trí | File tham chiếu |
|---|---|
| Nhân viên Kinh doanh B2B / Trình dược viên kênh (phủ cửa hàng mắt kính, phòng khám, bệnh viện mắt) | `references/vai-tro-kinh-doanh-b2b.md` |
| Quản lý Kinh doanh Vùng / Khu vực (ASM) | `references/vai-tro-quan-ly-vung.md` |
| Key Account Manager (chăm sóc đại lý lớn, chuỗi) | `references/vai-tro-key-account.md` |
| Brand Manager / Quản lý Thương hiệu (12 brand, trade marketing) | `references/vai-tro-brand-manager.md` |

**Mọi vị trí** đều dùng kèm thư viện dùng chung: `references/thu-vien-dung-chung.md` (câu hỏi văn hóa, câu chốt, hướng dẫn chấm STAR, **Cổng Công Nợ**, ranh giới pháp lý, thang điểm tổng).

> **Vị trí chưa có hồ sơ sẵn** (kho/logistics, marketing, kế toán công nợ, KTVKX, nhân sự...): tự xây bộ năng lực theo khung ở Bước 3, lấy 4–6 năng lực, mỗi năng lực 1–2 câu hành vi + 1 câu tình huống + 1 câu chuyên môn. Vẫn áp thư viện dùng chung. Hỏi người dùng để chốt năng lực trước khi viết.

### Bước 3 — Soạn bộ câu hỏi

Với mỗi năng lực, viết câu hỏi theo 4 nhóm. **Mỗi câu PHẢI kèm "Điểm cần nghe" và "Cờ đỏ"** — nếu không có hai dòng này thì câu hỏi vô dụng vì người phỏng vấn không biết thế nào là tốt.

- **Hành vi (STAR):** "Hãy kể về một lần anh/chị..." → dự báo tốt nhất.
- **Tình huống:** "Nếu gặp tình huống... anh/chị xử lý thế nào?" → dùng khi chưa có kinh nghiệm trực tiếp để hỏi hành vi.
- **Chuyên môn:** câu hỏi kiến thức hoặc bài tập nhỏ thực tế.
- **Văn hóa & giá trị:** lấy từ thư viện dùng chung.

**MẪU BỘ CÂU HỎI — dùng đúng khung này:**

```
## BỘ CÂU HỎI PHỎNG VẤN: [Tên vị trí] — Hào Phát Group

### Năng lực 1: [Tên năng lực]

**Câu hỏi hành vi:**
1. "Hãy kể về một lần anh/chị [tình huống liên quan]. Bối cảnh ra sao, anh/chị đã làm gì, kết quả thế nào (con số cụ thể)?"
   - 🟢 Điểm cần nghe: [bằng chứng cụ thể của năng lực]
   - 🔴 Cờ đỏ: [trả lời chung chung, đổ lỗi, không có con số]

**Câu hỏi tình huống:**
2. "Giả sử [tình huống thật ngành mắt kính B2B]. Hướng xử lý của anh/chị?"
   - 🟢 Điểm cần nghe: [tư duy có cấu trúc, công cụ/quy trình phù hợp]
   - 🔴 Cờ đỏ: [không có khung, chỉ nói khẩu hiệu]

**Câu hỏi chuyên môn:**
3. "[Câu hỏi kiến thức hoặc bài tập nhỏ]"
   - 🟢 Điểm cần nghe: [chiều sâu, áp dụng thực tế]
   - 🔴 Cờ đỏ: [trả lời hời hợt, không giải thích được lý do]
```

Khi tạo, **lấy nguyên các câu hỏi đã soạn sẵn trong file hồ sơ năng lực**, không bịa lại — chúng đã được viết bám tình huống thật của Hào Phát (đại lý chậm công nợ, trả hàng tồn, mở thị trường tỉnh mới, đẩy brand bán chậm...). Có thể bổ sung/điều chỉnh cho khớp cấp bậc người dùng yêu cầu.

**CHỐT CHẶN:** Trình bộ câu hỏi cho người dùng duyệt.

### Bước 4 — Xếp câu hỏi vào kịch bản theo vòng

Không hỏi tất cả câu trong một vòng. Phân bổ theo mục tiêu từng vòng:

```
## KỊCH BẢN PHỎNG VẤN — [Vị trí]

### Vòng 1 — Sàng lọc (20–30 phút)
Mục tiêu: xác nhận động cơ, kinh nghiệm địa bàn, mức lương kỳ vọng, thời gian bắt đầu.
- 1 câu văn hóa/động cơ
- 1 câu hành vi cho năng lực quan trọng nhất (thường là Đạt chỉ tiêu hoặc Phát triển đại lý)
- Câu hậu cần: địa bàn từng phụ trách, phương tiện đi tuyến, lương mong muốn
- 1 câu chốt

### Vòng 2 — Chuyên sâu (45–60 phút)
Mục tiêu: đào sâu năng lực cốt lõi + KIỂM TRA KỶ LUẬT CÔNG NỢ.
- 1 câu hành vi cho từng năng lực cốt lõi
- 1–2 câu tình huống ngành mắt kính B2B
- **BẮT BUỘC: bộ câu Cổng Công Nợ** (xem thư viện dùng chung)
- 1 bài tập nhỏ / chuyên môn
- 1 câu chốt

### Vòng 3 — Chung kết (30 phút) — nếu có
Mục tiêu: chốt quyết định, gỡ băn khoăn còn lại.
- Câu tình huống cho năng lực chưa kiểm tra kỹ
- Câu làm rõ điểm nghi ngại từ vòng trước
- Câu hỏi của ứng viên về vị trí/công ty
```

### Bước 5 — Hướng dẫn chấm điểm & cờ đỏ

Luôn kèm phần này để người phỏng vấn chấm thống nhất. Lấy từ `references/thu-vien-dung-chung.md`:
- **Khung chấm STAR** (Tình huống – Nhiệm vụ – Hành động – Kết quả).
- **CỔNG CÔNG NỢ** — với mọi vị trí chạm tiền/đại lý: nếu ứng viên thể hiện tư duy "cứ bán đã, công nợ tính sau" → **đánh dấu loại**, dù năng lực bán hàng tốt.
- **Thang điểm tổng** 1–5 cho từng năng lực + quy ước Đậu/Cân nhắc/Loại.

---

## Các lỗi cần tránh (Anti-Patterns)

- **Câu hỏi gợi ý đáp án:** "Em là người chủ động đúng không?" → mớm lời. Thay bằng: "Kể về một lần em tự phát hiện và giải quyết vấn đề khi chưa ai giao."
- **Chỉ hỏi giả định:** "Nếu đại lý chậm công nợ thì em làm gì?" cho ra hành vi lý tưởng hóa. Ưu tiên: "Lần gần nhất em xử lý một đại lý chậm công nợ, em đã làm gì?"
- **Bỏ qua Cổng Công Nợ với vị trí kinh doanh** — đây là lỗi đắt nhất ở ngành phân phối sỉ. Ứng viên giỏi mở đại lý nhưng để công nợ xấu sẽ làm thủng dòng tiền.
- **Một bộ câu hỏi cho mọi vị trí** — Trình kinh doanh và Brand Manager cần năng lực khác nhau. Phải đổi hồ sơ năng lực.
- **Không nghe cờ đỏ "chúng tôi/chúng em":** ứng viên nói "team em" cho mọi thành tích có thể đang nhận công của tập thể. Phải hỏi "Cụ thể CÁ NHÂN em đã làm gì?"
- **Hỏi quá nhiều câu:** đào sâu 5–6 câu hơn là lướt 15 câu. Để chỗ cho câu hỏi đào sâu tiếp.

---

## Cứu hộ (Recovery)

- **Ứng viên trả lời na ná nhau:** câu hỏi quá phổ thông. Thêm tình huống đặc thù Hào Phát hoặc bài tập nhỏ buộc phải thể hiện, không chỉ kể.
- **Người phỏng vấn không biết "tốt" là thế nào:** định nghĩa đáp án lý tưởng cho mỗi câu TRƯỚC khi phỏng vấn (đã có sẵn ở dòng 🟢).
- **Lần đầu tuyển vị trí này:** bắt đầu tối thiểu 3 câu hành vi + 2 câu văn hóa + 1 câu chốt cho một buổi sàng lọc 30 phút mạnh.
- **Ứng viên trả lời cộc lốc:** nhắc "Anh/chị kể chi tiết hơn được không?", "Rồi sau đó thế nào?". Dùng cả sự im lặng — đa số sẽ tự lấp đầy.
- **Năng lực khó hỏi bằng lời (vd: kỹ năng tư vấn tại điểm bán):** thêm bài tập đóng vai (role-play) bán một brand cụ thể cho một "đại lý" do người phỏng vấn đóng.

---

## Lưu ý đặc thù Hào Phát

- **Chỉ dùng 12 brand độc quyền** khi ra ví dụ/tình huống: BOLON, MOLSION, GINA, SEROVA, ANCCI, FLYER, VOSS, ZIOZIA, GUCCI, SAINT LAURENT, PUMA, MAUI JIM. **Không** lấy Ray-Ban, Essilor, Prada, Cartier hay brand ngoài danh mục làm ví dụ.
- Khách hàng B2B của Hào Phát gồm 3 tệp: **cửa hàng mắt kính (đại lý bán lẻ), phòng khám mắt, bệnh viện mắt** — tình huống nên phản ánh đúng tệp.
- Phân biệt rõ với **Mắt Việt** (chuỗi bán lẻ B2C 35+ cửa hàng): nếu tuyển cho Mắt Việt (KTV khúc xạ, quản lý cửa hàng, tư vấn viên...), báo người dùng rằng skill này tối ưu cho **kênh phân phối sỉ B2B**; vẫn dùng được khung nhưng nên đổi tình huống sang bối cảnh bán lẻ.
