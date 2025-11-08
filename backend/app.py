import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import random
import requests
import json
import sqlite3 
import time 
from io import StringIO
from dotenv import load_dotenv
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")



# Thêm hoặc sửa lại cấu hình CORS này:
# CODE CHUẨN ĐÃ SỬA:


if not YOUTUBE_API_KEY:
    print("⚠️ CẢNH BÁO: Thiếu YOUTUBE_API_KEY trong file .env!")


# IMPORT CÁC MODULE MỚI 
from tlu_api import (
    authenticate_tlu, 
    fetch_student_marks,
    fetch_current_semester_id, 
    fetch_student_schedule     
)
from recommender import (
    process_tlu_data_to_progress, 
    get_recommendation_logic, 
    predict_future_logic,
    get_insight_logic,
    process_schedule_to_courses,
    build_cf_model_data
)

# ==============================
# 💾 YouTube Cache System
# ==============================
def init_youtube_cache_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS youtube_cache (
            query TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Bảng youtube_cache đã sẵn sàng.")

def init_ai_cache_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_cache (
            prompt TEXT PRIMARY KEY,
            response TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Bảng ai_cache đã sẵn sàng.")

CORS(app, origins=["https://smart-learning-system-ecru.vercel.app"]) # <--- Gửi header "cho phép"
YOUTUBE_CACHE_TTL = 86400  # cache 1 ngày (24 giờ)

def get_youtube_cache(query):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT data, expires_at FROM youtube_cache WHERE query = ?", (query,))
    row = c.fetchone()
    conn.close()

    if not row:
        print(f"❌ Cache MISS cho từ khóa: {query}")
        return None

    data, expires_at = row
    if time.time() > expires_at:
        print(f"⚠️ Cache EXPIRED cho từ khóa: {query}")
        return None

    print(f"✅ Cache HIT cho từ khóa: {query}")
    return json.loads(data)


def set_youtube_cache(query, videos):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    expires_at = time.time() + YOUTUBE_CACHE_TTL
    c.execute(
        "INSERT OR REPLACE INTO youtube_cache (query, data, expires_at) VALUES (?, ?, ?)",
        (query, json.dumps(videos, ensure_ascii=False), expires_at)
    )
    conn.commit()
    conn.close()
    print(f"💾 Đã lưu cache YouTube cho từ khóa: {query}")


def clean_expired_youtube_cache():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM youtube_cache WHERE expires_at < ?", (time.time(),))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    if deleted > 0:
        print(f"🧹 Đã dọn {deleted} cache YouTube hết hạn.")

AI_CACHE_TTL = 86400  # 24h

def get_ai_cache(prompt):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT response, expires_at FROM ai_cache WHERE prompt = ?", (prompt,))
    row = c.fetchone()
    conn.close()
    if not row:
        print(f"❌ AI Cache MISS cho prompt: {prompt[:60]}...")
        return None
    response, expires_at = row
    if time.time() > expires_at:
        print(f"⚠️ AI Cache EXPIRED cho prompt: {prompt[:60]}...")
        return None
    print(f"✅ AI Cache HIT cho prompt: {prompt[:60]}...")
    return json.loads(response)

def set_ai_cache(prompt, response):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    expires_at = time.time() + AI_CACHE_TTL
    c.execute(
        "INSERT OR REPLACE INTO ai_cache (prompt, response, expires_at) VALUES (?, ?, ?)",
        (prompt, json.dumps(response, ensure_ascii=False), expires_at)
    )
    conn.commit()
    conn.close()
    print(f"💾 Đã lưu AI cache cho prompt: {prompt[:60]}...")

def clean_expired_ai_cache():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM ai_cache WHERE expires_at < ?", (time.time(),))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    if deleted > 0:
        print(f"🧹 Đã dọn {deleted} AI cache hết hạn.")


def search_youtube_videos(query, max_results=5):
    """Gửi API YouTube để tìm video hoặc tập."""
    if not YOUTUBE_API_KEY:
        print("❌ Không có YOUTUBE_API_KEY — không thể gửi API.")
        return []
    
    print(f"🔍 Gọi YouTube API thật cho từ khóa: {query}")
    url = (
        "https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&type=video&maxResults={max_results}&q={query}&key={YOUTUBE_API_KEY}"
    )

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"❌ Lỗi YouTube API: {resp.status_code}")
            return []

        data = resp.json()
        videos = []
        for item in data.get("items", []):
            videos.append({
                "title": item["snippet"]["title"],
                "videoId": item["id"]["videoId"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
            })

        return videos

    except Exception as e:
        print(f"❌ Lỗi khi gửi YouTube API: {e}")
        return []

def get_youtube_videos_with_cache(query):
    """Trả về video từ cache nếu có, nếu không thì gọi YouTube API thật và lưu cache."""
    cached = get_youtube_cache(query)
    if cached:
        return cached

    videos = search_youtube_videos(query)
    if videos:
        set_youtube_cache(query, videos)
    return videos



app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False 
CORS(app)

# ==============================
# Static upload (avatar)
# ==============================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/api/upload_avatar", methods=["POST"])
def upload_avatar():
    if "file" not in request.files or "student_id" not in request.form:
        return jsonify({"success": False, "message": "Thiếu file hoặc mã sinh viên!"}), 400

    file = request.files["file"]
    student_id = request.form["student_id"]

    if file.filename == "":
        return jsonify({"success": False, "message": "Chưa chọn file!"}), 400
    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Định dạng file không hợp lệ!"}), 400

    filename = secure_filename(f"{student_id}.jpg")
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    avatar_url = f"https://htkdtm.onrender.com/static/uploads/{filename}"
    return jsonify({"success": True, "url": avatar_url})


# --- THIẾT LẬP CACHE ---
DB_NAME = "tlu_cache.db"
CACHE_DURATION = 3600 # 1 giờ

def init_db():
    """ Khởi tạo CSDL SQLite (chạy 1 lần) """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_cache (
        student_id TEXT,
        data_type TEXT,
        json_data TEXT,
        timestamp REAL,
        PRIMARY KEY (student_id, data_type)
    )
    ''')
    conn.commit()
    conn.close()

    
def get_from_cache(student_id, data_type):
    """ Lấy dữ liệu từ cache (nếu có và chưa hết hạn) """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT json_data, timestamp 
        FROM api_cache 
        WHERE student_id = ? AND data_type = ?
    ''', (student_id, data_type))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        json_data, cache_timestamp = result
        
        if time.time() - cache_timestamp > CACHE_DURATION:
            print(f"CACHE EXPIRED: Dữ liệu {data_type} đã hết hạn. Gọi lại API TLU.")
            return None
            
        print(f"CACHE HIT: Trả về dữ liệu {data_type} cho {student_id} từ CSDL.")
        
        try:
            json_io = StringIO(json_data) 
            return pd.read_json(json_io, orient='records')
        except Exception as e:
            print(f"LỖI: Không thể đọc/convert JSON từ cache CSDL: {e}")
            return None 
    
    print(f"CACHE MISS: Không tìm thấy {data_type} cho {student_id} trong CSDL.")
    return None

def set_to_cache(student_id, data_type, data):
    """ Lưu dữ liệu vào cache CSDL """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        if isinstance(data, pd.DataFrame):
             data_to_serialize = data
        elif isinstance(data, list) and all(isinstance(i, dict) for i in data):
             data_to_serialize = pd.DataFrame(data)
        else:
             print(f"LỖI: Dữ liệu {data_type} không thể lưu vào cache (phải là list/DataFrame).")
             return

        json_data = data_to_serialize.to_json(orient='records') 
        
        cursor.execute(
            "INSERT OR REPLACE INTO api_cache (student_id, data_type, json_data, timestamp) VALUES (?, ?, ?, ?)",
            (student_id, data_type, json_data, time.time())
        )
        conn.commit()
        print(f"CACHE SET: Đã lưu dữ liệu {data_type} cho {student_id} vào CSDL.")
    except Exception as e:
        print(f"LỖI: Không thể lưu vào cache. Lý do: {e}")
    finally:
        conn.close()


# =========================================================
# NẠP VÀ HUẤN LUYỆN MÔ HÌNH AI KHI KHỞI ĐỘNG
# =========================================================
print("🤖 Đang nạp mô hình gợi ý AI (CF) từ 'tong_hop_diem_sinh_vien.csv'...")
cf_model_data = None
try:
    full_data = pd.read_csv("tong_hop_diem_sinh_vien.csv")
    cf_model_data = build_cf_model_data(full_data)
    
    if cf_model_data and cf_model_data[0] is not None:
        print(f"✅ Nạp mô hình AI (CF) thành công. Đã phân tích {len(cf_model_data[0])} sinh viên.")
    else:
        print("❌ LỖI: Không thể nạp mô hình AI (CF).")
        cf_model_data = None
        
except FileNotFoundError:
    print("❌ LỖI: Không tìm thấy tệp 'tong_hop_diem_sinh_vien.csv'.")
    cf_model_data = None
except Exception as e:
    print(f"❌ LỖI: Không thể nạp mô hình AI (CF) từ CSV. Lý do: {e}")
    cf_model_data = None
    

# =========================================================
# NẠP CƠ SỞ DỮ LIỆU HỌC LIỆU (JSON)
# =========================================================
print("📚 Đang nạp 'CSDL học liệu' từ 'learning_materials.json'...")
materials_db = {}
try:
    with open("learning_materials.json", "r", encoding="utf-8") as f:
        materials_db = json.load(f)
    print(f"✅ Nạp CSDL học liệu thành công. Đã tải {len(materials_db)} môn học.")
except FileNotFoundError:
    print("⚠️ CẢNH BÁO: Không tìm thấy tệp 'learning_materials.json'. Gợi ý sẽ bị tạm trống.")
except Exception as e:
    print(f"❌ LỖI: Không thể nạp 'learning_materials.json'. Lý do: {e}")

# =========================================================

user_sessions = {}  # Lưu phiên đăng nhập tạm thời


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Yêu cầu không có JSON body."}), 400
            
        student_id = data.get('student_id')
        password = data.get('password') 
        
        if not student_id or not password: 
            return jsonify({"success": False, "message": "Vui lòng cung cấp mã sinh viên và mật khẩu."}), 400

        auth_result = authenticate_tlu(student_id, password) 

        if auth_result and auth_result.get("success"):
            user_sessions[student_id] = {
                "access_token": auth_result["access_token"],
                "name": auth_result["name"],
                "student_info": auth_result
            }
            
            return jsonify({
                "success": True,
                "student": {
                    "student_id": auth_result["student_id"],
                    "name": auth_result["name"],
                    "major": auth_result["major"]
                }
            }), 200
        
        return jsonify({"success": False, "message": "Sai mã sinh viên hoặc mật khẩu."}), 401
    
    except Exception as e:
        print(f"LỖI CRITICAL TẠI API LOGIN: {e}")
        return jsonify({"success": False, "message": "Lỗi server khi đăng nhập."}), 500


def get_ALL_marks_data(student_id): 
    """ 
    Hàm hỗ trợ: Lấy dữ liệu ĐIỂM TỔNG KẾT (Tất cả các môn đã học).
    """
    cached_data = get_from_cache(student_id, "marks")
    if cached_data is not None:
        return cached_data, None 

    session = user_sessions.get(student_id)
    if not session or "access_token" not in session:
        return None, "Phiên đăng nhập hết hạn."

    access_token = session.get("access_token")
    
    tlu_marks = fetch_student_marks(access_token)
    
    if tlu_marks is None: 
        return None, "Không thể lấy dữ liệu điểm tổng kết từ TLU API."
    
    progress_data = process_tlu_data_to_progress(tlu_marks, student_id)
    
    set_to_cache(student_id, "marks", progress_data)

    return progress_data, None


@app.route('/api/progress/<student_id>', methods=['GET'])
def get_progress(student_id):
    """ 
    API lấy tiến độ học tập (dùng cho Dashboard).
    """
    progress_data, error = get_ALL_marks_data(student_id) 
    if error:
        return jsonify({"message": error}), 500
        
    return jsonify(progress_data.to_dict(orient='records'))


@app.route('/api/recommendation/<student_id>', methods=['GET'])
def get_recommendation(student_id):
    """ 
    API Gợi ý học tập, sử dụng từ 3 nguồn: TLU API, CF (CSV), và Gemini AI.
    """
    progress_data, error = get_ALL_marks_data(student_id) 
    if error:
        return jsonify({"message": error}), 500
    
    try:
        student_id_int = int(student_id)
    except ValueError:
        student_id_int = None
        print(f"Cảnh báo: student_id {student_id} không phải là số, không thể dùng mô hình CF.")

    recommendations = get_recommendation_logic(
        progress_data,
        student_id_int, 
        cf_model_data,
        materials_db  # materials_db này có thể bị bỏ qua nếu logic dùng AI
    )
    
    return jsonify(recommendations)


# =========================================================
# 🧠 SỬA LỖI LOGIC: API /api/insight PHẢI LẤY ĐÚNG student_id
# =========================================================
@app.route('/api/insight/<student_id>', methods=['GET'])
def get_insight(student_id):
    """ 
    API Phân tích AI tổng quan (dùng cho Dashboard).
    Sử dụng dữ liệu điểm tổng kết của sinh viên đang xem.
    """
    if not student_id:
        return jsonify({"insights": ["Không tìm thấy mã sinh viên để phân tích."]})

    progress_data, error = get_ALL_marks_data(student_id) 

    if error or progress_data.empty:
        return jsonify({"insights": ["Không đủ dữ liệu để phân tích."]})
        
    insights = get_insight_logic(progress_data)
    return jsonify(insights)


@app.route('/api/predict/<student_id>', methods=['GET'])
def predict_future(student_id):
    """ 
    API Dự báo tiến độ học tập (Mô phỏng AI).
    """
    progress_list, error = get_ALL_marks_data(student_id)
    if error:
        return jsonify({"message": error}), 500
        
    try:
        progress_data = pd.DataFrame(progress_list)
    except Exception as e:
        return jsonify({"message": f"Lỗi khi tạo DataFrame từ tiến độ: {e}"}), 500

    predictions = predict_future_logic(progress_data) 
    return jsonify(predictions)


# --- API CHO TRANG "CÁC MÔN ĐANG HỌC" ---
@app.route('/api/current-schedule/<student_id>', methods=['GET'])
def get_current_schedule(student_id):
    """
    API lấy danh sách các môn đang học (cho trang SchedulePage.js)
    """
    cached_data = get_from_cache(student_id, "schedule")
    if cached_data is not None:
        return jsonify(cached_data.to_dict(orient='records')) 

    session = user_sessions.get(student_id)
    if not session or "access_token" not in session:
        return jsonify({"error": "Phiên đăng nhập hết hạn."}), 401

    access_token = session.get("access_token")

    current_semester_id = fetch_current_semester_id(access_token)
    if not current_semester_id:
        return jsonify({"error": "Không thể lấy dữ liệu học kỳ hiện tại."}), 500

    schedule_data = fetch_student_schedule(access_token, current_semester_id)
    
    if schedule_data is None: 
        return jsonify({"error": "Không thể lấy dữ liệu lịch học."}), 500
    
    processed_schedule = process_schedule_to_courses(schedule_data, student_id)
    
    set_to_cache(student_id, "schedule", processed_schedule)
    
    return jsonify(processed_schedule.to_dict(orient='records'))


@app.route('/api/youtube/<keyword>', methods=['GET'])
def youtube_search(keyword):
    """API tìm kiếm video YouTube có cache"""
    videos = get_youtube_videos_with_cache(keyword)
    if not videos:
        return jsonify({"message": "Không tìm thấy video"}), 404
    return jsonify(videos)


@app.route('/')
def home():
    return jsonify({"message": "Smart Learning System Backend Ready (TLU Integrated) 🚀"})


if __name__ == '__main__':
    init_db()
    init_youtube_cache_db()  
    init_ai_cache_db() 
    clean_expired_youtube_cache() 
    app.run(debug=True, port=5000)
