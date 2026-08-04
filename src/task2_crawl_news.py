import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thư mục news sẵn sàng: {DATA_DIR}")


SAMPLE_NEWS = [
    {
        "url": "https://www.rmit.edu.vn/news/vi/2024/library-services-expansion",
        "title": "Thu vien RMIT Vietnam mo rong khong gian hoc tap 24/7 va kho sach so",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Thu vien RMIT Vietnam mo rong khong gian hoc tap 24/7 va kho sach so

Thu vien RMIT Vietnam Nam Sai Gon va Ha Noi vua chinh thuc nang cap he thong tra cuu va mo rong khong gian hoc tap phuc vu sinh vien.

## Cac tien ich noi bat:
- **Khong gian mo 24/7**: Phong hoc nhom va khu vuc yen tinh mo cua phuc vu sinh vien trong suot mua thi.
- **Kho sach so va truy cap CSDL**: Sinh vien co the truy cap hon 300,000 cuon sach dien tu (e-books) va cac tap chi khoa hoc quoc te tu IEEE, ACM, Springer qua tai khoan RMIT.
- **Dich vu ho tro nghien cuu**: Thu vien cung cap cac buoi workshop phan mem trich dan EndNote, Mendeley va tu van ho tro nghien cuu 1-on-1 voi thu thu chuyên nganh.

Sinh vien co the dat phong hoc nhom truc tuyen qua ung dung RMIT Library Portal.
"""
    },
    {
        "url": "https://www.rmit.edu.vn/news/vi/2024/student-support-mental-health",
        "title": "Dich vu Tu van va Ho tro Tam ly Sinh vien RMIT Vietnam Student Wellbeing",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Dich vu Tu van va Ho tro Tam ly Sinh vien RMIT Vietnam Student Wellbeing

Trung tam Ho tro Sinh vien RMIT (Student Wellbeing Centre) cung cap cac dich vu tu van tam ly mien phi va bao mat cho toan bo sinh vien dang theo hoc.

## Chi tiet dich vu:
- **Tu van ca nhan 1-on-1**: Ho tro sinh vien giai quyet cac van de ve cang thang hoc tap, lo au, hoa nhap va dinh huong ca nhan.
- **Hoi thao ky nang (Wellbeing Workshops)**: Cac buoi huong dan quan ly thoi gian, kiem soat stress va thuc hanh mindfulness.
- **Ho tro sinh vien khuyet tat (Equitable Learning Services)**: Cung cap ke hoach ho tro hoc tap va thi hop ly cho sinh vien co nhu cau dac biet.

De dat lich hen tu van, sinh vien truy cap Student Connect hoac gui email ve wellbeing@rmit.edu.vn.
"""
    },
    {
        "url": "https://www.rmit.edu.vn/news/vi/2024/career-fair-internship-opportunities",
        "title": "Ngay hoi Viec lam va Ket noi Doanh nghiep RMIT Career Fair 2024",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Ngay hoi Viec lam va Ket noi Doanh nghiep RMIT Career Fair 2024

Phong Ket noi Doanh nghiep va Viec lam sinh vien RMIT to chuc Ngay hoi Viec lam Career Fair 2024 voi su tham gia cua hon 50 doanh nghiệp va tap doan da quoc gia.

## Thong tin su kien:
- **Thoi gian**: 09:00 - 16:00, Ngay 20 tháng 10 năm 2024.
- **Dia diem**: Hall A, RMIT Nam Sai Gon Campus.
- **Doi tac tham gia**: Unilever, Shopee, HSBC, Intel, Bosch, VNG, PwC va FPT.

## Quyen loi sinh vien:
- Ung tuyen truc tiep cac vi tri thuc tap sinh (Internship) va Chuyen vien tap su (Management Trainee).
- Sua CV va phong van thu 1-on-1 voi cac chuyên gia HR tuyen dung.
- Tham gia cac buoi Panel Discussion ve xu huong viec lam va tri tue nhan tao (AI) trong doanh nghiep.
"""
    },
    {
        "url": "https://www.rmit.edu.vn/news/vi/2024/course-registration-guide-2024",
        "title": "Huong dan dang ky hoc phan va hoan hoc phi Hoc ky 1 2024 qua Enrolment Online",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Huong dan dang ky hoc phan va hoan hoc phi Hoc ky 1 2024 qua Enrolment Online

Phong Quản ly Dao tao RMIT thong bao lich dang ky mon hoc va quy trinh thay doi hoc phan cho Hoc ky 1 nam 2024.

## Quy trinh dang ky:
1. Truy cap he thong **Enrolment Online (EO)** qua tai khoan sinh vien.
2. Chon cac mon hoc trong khung chuong trinh (Program Plan).
3. Kiem tra thoi khoa bieu va xac nhan dang ky.

## Cac moc thoi gian quan trong (Census Date):
- **Ngay mo cong dang ky**: 08:00 ngay 01 thang 02 năm 2024.
- **Han cuoi them/xoa mon (Add/Drop Deadline)**: 23:59 ngay 15 thang 02 năm 2024.
- **Moc Census Date (Han cuoi rut mon khong tinh hoc phi)**: Ngay 28 thang 02 năm 2024.
- Neu sinh vien rut mon hoc sau ngay Census Date, hoc phi môn hoc se khong duoc hoan lai va mon hoc se ghi nhan ket qua W (Withdrawn).
"""
    },
    {
        "url": "https://www.rmit.edu.vn/news/vi/2024/sports-club-facilities-registration",
        "title": "Dang ky CLB The thao va Suu tap Tien ich Trung tam Thao thao RMIT Sports Centre",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Dang ky CLB The thao va Suu tap Tien ich Trung tam Thao thao RMIT Sports Centre

Trung tam The thao RMIT Sports Centre thong bao mo dang ky thanh vien cac CLB the thao va su dung phong Gym cho sinh vien.

## Co so vat chat:
- Phong Gym hien dai voi may tap cardio va ta nang.
- San bong da co nhan tao, san bong bas, san tennis va ho boi dat chuan quoc te.
- Phong tap Yoga va Martial Arts.

## Dang ky va Le phi:
- Sinh vien RMIT duoc su dung phong Gym va ho boi **mien phi** khi xuat trinh the sinh vien hop le.
- Cac CLB The thao (Bong bas, Cầu long, Taekwondo, Esports) chiu su quan ly cua Student Council, dang ky tham gia tai Ngay hoi CLB (Club Fair).
"""
    }
]


def generate_news_files():
    """Tạo 5 file JSON bài viết tin tức RMIT vào data/landing/news/."""
    setup_directory()

    for i, article in enumerate(SAMPLE_NEWS, 1):
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] Đã tạo file tin tức JSON: {filepath.name}")


if __name__ == "__main__":
    generate_news_files()

