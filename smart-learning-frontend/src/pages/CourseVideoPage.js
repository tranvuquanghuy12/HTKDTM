import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios"; 
import "./CourseVideoPage.css";

// ⚠️ LƯU Ý QUAN TRỌNG:
// Đã thay link API bằng link Render Python thật của anh
const API_BASE_URL = "https://htkdtm.onrender.com"; 

// Link Bot Node.js (cái này ta dùng sau, nhưng cứ để đây)
const CHATBOT_BASE_URL = "https://htkdtm-chatbot1.onrender.com"; 

export default function CourseVideoPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const course = state?.course;

  // STATE MỚI để lưu video và trạng thái tải
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // useEffect để gọi YouTube API ngay khi Component được render
  useEffect(() => {
    // ⚠️ Đảm bảo course.title được truyền vào từ trang trước (SchedulePage.js)
    if (!course?.title) {
      setLoading(false);
      return;
    }

    const fetchVideos = async () => {
      try {
        const keyword = encodeURIComponent(course.title); 
        
        // Gọi API YouTube qua Backend Flask
        // Lỗi 404 (Không tìm thấy video) hoặc 500 (Lỗi server) sẽ bị bắt ở đây
        const response = await axios.get(`${API_BASE_URL}/api/youtube/${keyword}`);
        
        if (response.data && Array.isArray(response.data)) {
          setVideos(response.data);
        } else {
          setVideos([]);
        }
        setError(null);
      } catch (err) {
        console.error("Lỗi khi tải video:", err);
        setError("Không thể tải tài liệu hoặc video tham khảo. Vui lòng kiểm tra API Key!");
        setVideos([]); // Đảm bảo list video rỗng khi lỗi
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, [course?.title]); 

  // Nếu không có dữ liệu, quay về trang schedule
  if (!course) {
    return (
      <div className="video-page-wrapper">
        <h2>⚠️ Không tìm thấy thông tin khóa học.</h2>
        <button className="back-btn" onClick={() => navigate("/schedule")}>
          ← Quay lại các môn đang học
        </button>
      </div>
    );
  }
  
  // Hiển thị Loading khi đang tải
  if (loading) {
    return (
      <div className="video-page-container fade-in" style={{ textAlign: 'center', padding: '50px' }}>
        <h2>Đang tìm kiếm tài liệu cho môn {course.title}...</h2>
        <p>Vui lòng chờ. (Đang chờ Backend gọi YouTube API)</p>
      </div>
    );
  }


  return (
    <div className="video-page-container fade-in">
      <div className="video-section">
        <div className="video-header">
          <h2>Tài liệu tham khảo: {course.title}</h2>
          <p>
            *Lưu ý: Bạn đang xem các video liên quan, không phải nội dung khóa học chính thức.
          </p>
          {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
        </div>

        {/* PHẦN CHÍNH: HIỂN THỊ VIDEO YOUTUBE ĐẦU TIÊN TÌM ĐƯỢC */}
        <div className="video-player">
          {videos.length > 0 ? (
            <iframe
              width="100%"
              height="450"
              // Dùng videoId của video đầu tiên tìm được
              src={`https://www.youtube.com/embed/${videos[0].videoId}`} 
              title={`Video tham khảo: ${course.title}`}
              frameBorder="0"
              allowFullScreen
            ></iframe>
          ) : (
            <div className="no-video-found">
              Không tìm thấy video tham khảo nào hoặc API Key chưa được cài đặt.
            </div>
          )}
        </div>

        <button className="back-btn" onClick={() => navigate("/schedule")}>
          ← Quay lại các môn đang học
        </button>
      </div>

      
      <div className="lesson-section">
        <h3>📖 Danh sách Video Tham Khảo ({videos.length} video)</h3>
        
        {videos.length > 0 ? (
          <ul className="lesson-list">
            {videos.map((video, index) => (
              <li key={index} className="lesson-item video-item-link">
                <a href={video.url} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center' }}>
                    <img src={video.thumbnail} alt={video.title} style={{ width: '120px', height: 'auto', marginRight: '10px', objectFit: 'cover' }} />
                    <div style={{ flexGrow: 1 }}>
                        <strong>{video.title}</strong>
                        <p style={{ margin: 0, fontSize: '0.9em', color: '#666' }}>Tác giả/Kênh: {video.channelTitle}</p>
                    </div>
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <p>Không có video nào được tìm thấy. Vui lòng kiểm tra Cấu hình hoặc Tên môn học.</p>
        )}
      </div>

       {/* TÍCH HỢP CHATBOT (Có thể thêm component sau) */}
       {/* Ví dụ: <Chatbot topic={course.title} apiUrl={CHATBOT_BASE_URL} /> */}
    </div>
  );
}