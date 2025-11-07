import sqlite3
import pandas as pd
from io import StringIO
import re # Thêm thư viện regex để làm sạch dữ liệu
import sys
# Fix lỗi encoding khi in ra console
sys.stdout.reconfigure(encoding='utf-8')

# Tên CSDL phải khớp với file đã tạo trước đó
DATABASE_NAME = 'smart_learning.db'

# Dữ liệu bảng điểm mẫu bạn đã cung cấp (lưu dưới dạng chuỗi)
STATIC_MARKS_DATA = """
MSV,Họ và tên, Chuyên ngành,Ảnh,Chuyên ngành,Phân tích HTTT,Cơ sở dữ liệu,Lập trình Python,Khai phá dữ liệu,HQT CSDL nâng cao
2251162030, NGUYỄN THIÊN HƯƠNG,Hệ thống thông tin,,,6.8,7.0,7.8,9.4,7.4
2251161975, NGUYỄN CÔNG ĐỊNH,Hệ thống thông tin,,,7.3,8.0,9.2,8.9,8.5
2251161979, NGUYỄN ĐỖ TRUNG ĐỨC,Hệ thống thông tin,,,8.5,8.2,8.5,7.8,6.8
2251162115, ĐÌNH LAN PHƯƠNG,Hệ thống thông tin,,,8.2,8.3,7.2,7.5,6.5
2251161952, ĐINH CHÍ BẰNG,Hệ thống thông tin,,,8.1,7.2,7.3,7.8,9.6
2251162172, BÙI MINH TIẾN,Hệ thống thông tin,,,8.3,7.1,9.2,8.3,8.5
2251162165, HOÀNG VĂN THƯỞNG,Hệ thống thông tin,,,7.5,9.6,9.7,9.2,7.6
2251162082, PHẠM NGUYỄN HẢI NAM,Hệ thống thông tin,,,8.2,8.4,9.4,7.2,9.0
2251161945, TRẦN DUY ANH,Hệ thống thông tin,,,9.1,7.0,7.8,7.3,9.4
2251162123, NGUYỄN HỒNG QUÂN,Hệ thống thông tin,,,8.1,9.7,9.4,7.1,6.8
2251162153, HỒ PHÚC THÀNH,Hệ thống thông tin,,,9.7,7.3,8.7,9.7,6.6
2251162015, NGUYỄN VĂN HOÀNG,Hệ thống thông tin,,,9.0,7.8,8.8,9.3,9.6
2251162018, CAO VĂN HUẤN,Hệ thống thông tin,,,9.0,7.7,7.3,7.4,8.3
2251162014, ĐẶNG HUY HOÀNG,Hệ thống thông tin,,,6.8,9.8,8.1,8.1,9.3
2251162050, NGUYỄN THỊ LỆ,Hệ thống thông tin,,,9.7,7.5,9.5,8.5,9.1
2251162161, NGUYỄN THỊ THIỀM,Hệ thống thông tin,,,9.4,8.7,8.2,9.2,8.4
2251161982, LƯU CÔNG QUỐC DŨNG,Hệ thống thông tin,,,9.4,9.3,7.7,9.7,7.2
2251161936, BÙI TUẤN ANH,Hệ thống thông tin,,,7.3,7.2,9.0,9.2,6.9
2251162064, PHẠM HOÀNG LONG,Hệ thống thông tin,,,8.1,6.8,9.1,8.7,7.5
2251162135, PHẠM DIỄM QUỲNH,Hệ thống thông tin,,,8.1,9.6,8.0,9.6,8.1
2251161970, PHẠM TIẾN ĐẠT,Hệ thống thông tin,,,8.3,7.5,7.9,7.5,9.0
2251161993, HOÀNG THỊ THU HẰNG,Hệ thống thông tin,,,8.3,7.7,9.1,9.2,8.8
2251162106, NGÔ VĂN PHÁT,Hệ thống thông tin,,,7.2,9.6,6.9,7.8,6.6
2251162114, BÙI BÍCH PHƯƠNG,Hệ thống thông tin,,,7.7,7.4,8.1,6.9,9.5
2251161934, NGUYỄN THÀNH AN,Hệ thống thông tin,,,8.5,7.0,9.2,7.9,7.3
2251162060, ĐỖ THỊ THANH LOAN,Hệ thống thông tin,,,7.6,6.7,7.2,7.5,9.5
2251162136, PHẠM HƯƠNG QUỲNH,Hệ thống thông tin,,,8.9,6.9,7.3,7.4,8.0
2251162185, TRẦN HÀ TRANG,Hệ thống thông tin,,,8.1,8.6,9.6,8.4,9.0
2251162107, NGUYỄN HUY PHONG,Hệ thống thông tin,,,7.8,8.8,8.8,9.0,7.2
2251162184, PHÙNG THU TRANG,Hệ thống thông tin,,,9.7,8.0,9.5,7.4,8.7
2251161968, NGUYỄN XUÂN ĐẠT,Hệ thống thông tin,,,9.5,7.8,8.4,6.7,9.7
2251161959, TRẦN ĐỨC CƠ,Hệ thống thông tin,,,7.5,8.1,9.6,9.5,6.6
2251162102, LÊ THỊ HỒNG NHUNG,Hệ thống thông tin,,,9.7,7.3,6.7,9.7,6.8
2251162101, ĐỖ THỊ QUỲNH NHƯ,Hệ thống thông tin,,,7.4,9.2,8.5,9.0,8.4
2251162052, ĐẶNG VĂN LINH,Hệ thống thông tin,https://htkdtm.onrender.com/static/uploads/2251162052.jpg,Hệ thống thông tin,8.9,7.6,8.9,8.4,7.9
2251162036, TRẦN VŨ QUANG HUY,Hệ thống thông tin,,,7.8,7.7,9.1,9.2,6.9
2251161965, NGÔ ĐÌNH ĐẠT,Hệ thống thông tin,,,7.8,9.2,8.3,9.2,7.1
2251162178, HOÀNG THANH TRANG,Hệ thống thông tin,,,8.8,9.2,7.9,8.5,8.7
2251162007, LÊ THỊ HOA,Hệ thống thông tin,,,7.8,9.7,7.9,6.7,7.0
2251161949, VƯƠNG THỊ MAI ANH,Hệ thống thông tin,,,7.4,6.7,7.6,7.8,9.7
2251162167, BÙI THỊ THU THỦY,Hệ thống thông tin,,,7.2,9.4,9.2,9.5,6.7
2251162182, PHẠM THỊ HUYỀN TRANG,Hệ thống thông tin,,,7.8,7.3,7.1,7.8,7.4
2251162187, VŨ THỊ QUỲNH TRANG,Hệ thống thông tin,,,9.5,7.5,6.6,7.2,7.6
2251161984, HÀ QUANG DƯƠNG,Hệ thống thông tin,,,8.9,7.1,8.7,8.3,8.2
2251162004, NGUYỄN TRUNG HIẾU,Hệ thống thông tin,,,9.1,7.4,6.9,7.8,8.1
2251162166, NGUYỄN THỊ THANH THÙY,Hệ thống thông tin,,,9.5,8.7,9.3,7.7,8.4
2251162208, TRẦN ĐỨC VIỆT,Hệ thống thông tin,,,6.8,6.6,9.5,7.2,6.9
2251162103, NGUYỄN THỊ HỒNG NHUNG,Hệ thống thông tin,,,9.2,7.4,6.8,7.1,7.7
2251162156, NGUYỄN PHƯƠNG THẢO,Hệ thống thông tin,,,9.4,7.4,9.4,9.4,9.4
2251161951, TRẦN NGỌC ÁNH,Hệ thống thông tin,,,7.5,9.7,7.3,7.1,8.2
2251162094, TRẦN HOÀNG NHẤT,Hệ thống thông tin,,,7.2,7.9,8.3,7.1,8.0
2251161933, NGUYỄN NGỌC THÀNH AN,Hệ thống thông tin,,,9.1,8.0,7.4,9.3,6.6
2251162065, TRƯƠNG PHẠM HẢI LONG,Hệ thống thông tin,,,8.6,8.6,7.5,9.8,6.6
2251162158, NGUYỄN THỊ PHƯƠNG THẢO,Hệ thống thông tin,,,9.2,9.0,7.6,8.4,8.4
2251162188, NGUYỄN MINH TRÚC,Hệ thống thông tin,,,6.8,8.4,6.9,9.0,7.3
2151163673, Hà Thị Thùy Dung,Hệ thống thông tin,,,8.3,7.4,8.1,8.7,8.8
2251162186, VŨ QUỲNH TRANG,Hệ thống thông tin,,,6.8,7.0,7.2,7.9,8.1
"""

def clean_data(data):
    """Làm sạch dữ liệu CSV để xử lý."""
    # Loại bỏ các dòng tiêu đề lặp lại
    cleaned_lines = []
    header = None
    for line in data.strip().split('\n'):
        if line.startswith('MSV,Họ và tên'):
            if header is None:
                header = line
                cleaned_lines.append(header)
            continue
        cleaned_lines.append(line)
        
    return '\n'.join(cleaned_lines)

def import_static_data():
    """Đọc dữ liệu mẫu và chèn vào CSDL."""
    conn = None
    try:
        # 0. KẾT NỐI CSDL
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        print(f"✅ Đã kết nối CSDL: {DATABASE_NAME}")

        # 1. LÀM SẠCH VÀ ĐỌC DỮ LIỆU BẰNG PANDAS
        cleaned_csv = clean_data(STATIC_MARKS_DATA)
        df = pd.read_csv(StringIO(cleaned_csv))
        
        # Loại bỏ các cột không cần thiết và chứa giá trị rỗng (Ảnh, Chuyên ngành lặp)
        df = df.iloc[:, [0, 1, 2, 5, 6, 7, 8, 9]]
        
        # Đặt lại tên cột để dễ truy cập
        df.columns = ['MSV', 'Ho_va_ten', 'Chuyen_nganh', 'Phan_tich_HTTT', 'Co_so_du_lieu', 'Lap_trinh_Python', 'Khai_pha_du_lieu', 'HQT_CSDL_nang_cao']
        
        # Lấy danh sách 5 môn học và làm sạch tên
        subject_names = df.columns[3:].tolist()
        
        # Đặt một mã ID giả định cho các môn học này
        SUBJECT_MAPPING = {
            'Phan_tich_HTTT': {'code': 'ITS401', 'name': 'Phân tích HTTT', 'credits': 3},
            'Co_so_du_lieu': {'code': 'ITS402', 'name': 'Cơ sở dữ liệu', 'credits': 3},
            'Lap_trinh_Python': {'code': 'ITS403', 'name': 'Lập trình Python', 'credits': 3},
            'Khai_pha_du_lieu': {'code': 'ITS404', 'name': 'Khai phá dữ liệu', 'credits': 3},
            'HQT_CSDL_nang_cao': {'code': 'ITS405', 'name': 'HQT CSDL nâng cao', 'credits': 3},
        }
        
        total_students = 0
        total_grades = 0

        # --- CHÈN DỮ LIỆU MÔN HỌC (SUBJECTS) ---
        for sub in SUBJECT_MAPPING.values():
            cursor.execute("""
                INSERT OR IGNORE INTO subjects (subject_id, subject_name, credits)
                VALUES (?, ?, ?)
            """, (sub['code'], sub['name'], sub['credits']))
        conn.commit()
        print("✅ Đã chèn/cập nhật 5 môn học mẫu vào bảng 'subjects'.")
        
        # --- CHÈN DỮ LIỆU SINH VIÊN VÀ ĐIỂM (STUDENTS & GRADES) ---
        # Giả định học kỳ cho dữ liệu mẫu này là 'HK1_2023_2024'
        SEMESTER_NAME = "HK Mẫu 2023-2024"
        
        for index, row in df.iterrows():
            msv = str(row['MSV']).strip()
            full_name = str(row['Ho_va_ten']).strip()
            major = str(row['Chuyen_nganh']).strip()
            
            # 1. Chèn vào bảng STUDENTS
            # Lưu ý: Sửa lỗi khoảng trắng đầu tiên trong tên
            cleaned_name = re.sub(r'^\s+|\s+$', '', full_name)
            
            cursor.execute("""
                INSERT OR REPLACE INTO students (student_id, full_name, email, major)
                VALUES (?, ?, ?, ?)
            """, (msv, cleaned_name, f"{msv}@tlu.edu.vn", major))
            total_students += 1

            # 2. Chèn vào bảng GRADES
            for col_name, sub_info in SUBJECT_MAPPING.items():
                subject_id = sub_info['code']
                score = row[col_name]
                
                # Kiểm tra nếu điểm là hợp lệ (không phải NaN)
                if pd.notna(score):
                    cursor.execute("""
                        INSERT OR REPLACE INTO grades (student_id, subject_id, semester, score)
                        VALUES (?, ?, ?, ?)
                    """, (msv, subject_id, SEMESTER_NAME, float(score)))
                    total_grades += 1
            
        conn.commit()
        print(f"✅ Đã chèn/cập nhật {total_students} sinh viên vào bảng 'students'.")
        print(f"✅ Đã chèn/cập nhật {total_grades} điểm số vào bảng 'grades'.")

    except sqlite3.Error as e:
        print(f"❌ Lỗi SQLite: {e}")
    except Exception as e:
        print(f"❌ Lỗi xử lý dữ liệu: {e}")
    finally:
        if conn:
            conn.close()
            print("--- Đã đóng kết nối CSDL ---")

if __name__ == '__main__':
    # Yêu cầu cài đặt thư viện pandas nếu chưa có
    try:
        pd.read_csv
    except NameError:
        print("⚠️ CẦN CÀI ĐẶT THƯ VIỆN PANDAS!")
        print("Vui lòng chạy lệnh sau trong Terminal:")
        print("pip install pandas")
        sys.exit(1)
        
    import_static_data()
