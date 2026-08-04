import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thư mục đã sẵn sàng: {DATA_DIR}")


def generate_legal_docs():
    """Tạo 3 văn bản chính sách quy định RMIT Vietnam dạng PDF."""
    setup_directory()

    docs = [
        {
            "filename": "tuition-fees-rmit.pdf",
            "title": "QUY ĐỊNH HỌC PHÍ VÀ PHƯƠNG THỨC THANH TOÁN RMIT VIỆT NAM 2024",
            "content": """QUY ĐỊNH HỌC PHÍ VÀ PHƯƠNG THỨC THANH TOÁN RMIT VIỆT NAM 2024

1. Chính sách học phí chung:
- Học phí đại học tại RMIT Việt Nam được tính theo học phần (credit point).
- Mức học phí trung bình mỗi năm học dao động từ 300,000,000 VNĐ đến 330,000,000 VNĐ tùy theo ngành học.
- Sinh viên có thể đóng học phí theo từng học kỳ (3 kỳ / năm) hoặc đóng theo năm học.

2. Hạn chót đóng học phí:
- Học kỳ 1: Hạn cuối đóng học phí là ngày 15 tháng 03.
- Học kỳ 2: Hạn cuối đóng học phí là ngày 15 tháng 07.
- Học kỳ 3: Hạn cuối đóng học phí là ngày 15 tháng 11.
- Nếu đóng học phí trễ hạn sau 7 ngày, sinh viên sẽ bị tính phí trễ hạn 1,000,000 VNĐ/tuần.

3. Phương thức thanh toán:
- Chuyển khoản ngân hàng qua cổng thanh toán sinh viên RMIT Student Portal.
- Thanh toán qua thẻ tín dụng quốc tế (Visa, MasterCard) hoặc ATM nội địa.
- Hỗ trợ trả góp học phí lãi suất 0% qua các ngân hàng liên kết.
"""
        },
        {
            "filename": "scholarship-eligibility-rmit.pdf",
            "title": "QUY CHẾ HỌC BỔNG VÀ TIÊU CHUẨN XÉT DUYỆT RMIT VIỆT NAM 2024",
            "content": """QUY CHẾ HỌC BỔNG VÀ TIÊU CHUẨN XÉT DUYỆT RMIT VIỆT NAM 2024

1. Các loại học bổng:
- Học bổng Thành tựu Thanh niên (Youth Achievement Scholarship): Trị giá 50% đến 100% học phí.
- Học bổng Thành tích học tập xuất sắc (Academic Achievement Scholarship): Trị giá 100% học phí toàn khóa học.
- Học bổng Khuyến học ngành Công nghệ & Sáng tạo: Trị giá 25% đến 50% học phí.

2. Tiêu chuẩn và điều kiện xét duyệt:
- Điểm trung bình học tập (GPA) lớp 12 từ 8.5/10 trở lên.
- Trình độ tiếng Anh: IELTS Academic tối thiểu 6.5 (không kỹ năng nào dưới 6.0) hoặc TOEFL iBT 79+.
- Bài luận cá nhân (Personal Statement) dài tối thiểu 500 từ trình bày nguyện vọng và hoạt động ngoại khóa.
- Vòng phỏng vấn trực tiếp với Hội đồng Xét duyệt Học bổng RMIT.

3. Duy trì học bổng:
- Sinh viên phải duy trì GPA tối thiểu 3.0/4.0 trong suốt các học kỳ tại RMIT.
- Tham gia tối thiểu 20 giờ hoạt động cộng đồng hoặc hỗ trợ sinh viên mỗi năm.
"""
        },
        {
            "filename": "accommodation-services-rmit.pdf",
            "title": "QUY ĐỊNH KÝ TÚC XÁ VÀ DỊCH VỤ HỖ TRỢ CHỖ Ở RMIT VIỆT NAM",
            "content": """QUY ĐỊNH KÝ TÚC XÁ VÀ DỊCH VỤ HỖ TRỢ CHỖ Ở RMIT VIỆT NAM

1. Dịch vụ Chỗ ở Sinh viên:
- Ký túc xá RMIT Nam Sài Gòn cung cấp phòng ở hiện đại với các lựa chọn: Phòng đơn, Phòng đôi và Căn hộ 3 phòng.
- Giá thuê phòng dao động từ 4,500,000 VNĐ đến 9,000,000 VNĐ / tháng (đã bao gồm chi phí điện, nước, wifi).

2. Quy định an ninh và sinh hoạt:
- Giờ thiết quân: Ký túc xá đóng cửa lúc 23:00 hằng đêm.
- Không sử dụng chất cấm, thuốc lá, đồ uống có cồn trong khu vực Ký túc xá.
- Không dẫn khách lạ qua đêm nếu chưa có sự đồng ý bằng văn bản của Ban Quản lý KTX.

3. Quy trình đăng ký chỗ ở:
- Sinh viên nộp đơn đăng ký trực tuyến qua Residential Portal RMIT trước khai giảng 30 ngày.
- Đặt cọc 1 tháng tiền phòng để giữ chỗ.
"""
        }
    ]

    try:
        from fpdf import FPDF
        for doc in docs:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=11)
            for line in doc["content"].split("\n"):
                pdf.multi_cell(0, 8, txt=line)
            filepath = DATA_DIR / doc["filename"]
            pdf.output(str(filepath))
            print(f"[OK] Đã tạo PDF: {filepath}")
    except ImportError:
        # Simple pure Python PDF generator fallback
        for doc in docs:
            filepath = DATA_DIR / doc["filename"]
            text = doc["content"]
            pdf_bytes = create_simple_pdf_bytes(text)
            filepath.write_bytes(pdf_bytes)
            print(f"[OK] Đã tạo PDF (fallback): {filepath}")


def strip_accents(s: str) -> str:
    import unicodedata
    s = s.replace('đ', 'd').replace('Đ', 'D')
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8')


def create_simple_pdf_bytes(text: str) -> bytes:
    """Tạo file PDF hợp lệ đơn giản bằng Python thuần."""
    text_clean = strip_accents(text)
    lines = text_clean.replace('\r', '').split('\n')
    pdf_text_stream = "BT /F1 10 Tf 50 750 Td 12 TL\n"
    for line in lines:
        escaped_line = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        pdf_text_stream += f"({escaped_line}) T*\n"
    pdf_text_stream += "ET"
    
    stream_len = len(pdf_text_stream)
    pdf_content = (
        "%PDF-1.4\n"
        "1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        "2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        "3 0 obj <</Type /Page /Parent 2 0 R /Resources <</Font <</F1 4 0 R>>>> /MediaBox [0 0 612 792] /Contents 5 0 R>> endobj\n"
        "4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        f"5 0 obj <</Length {stream_len}>>\nstream\n"
        f"{pdf_text_stream}\n"
        "endstream\nendobj\n"
        "xref\n0 6\n0000000000 65535 f \n"
        "0000000009 00000 n \n"
        "0000000058 00000 n \n"
        "0000000115 00000 n \n"
        "0000000244 00000 n \n"
        "0000000315 00000 n \n"
        "trailer <</Size 6 /Root 1 0 R>>\nstartxref\n400\n%%EOF\n"
    )
    return pdf_content.encode('latin1')


if __name__ == "__main__":
    generate_legal_docs()

