import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios"; 
import "./CourseVideoPage.css"; 

// ⚠️ Cấu hình Link API (Bắt buộc phải đúng)
const API_BASE_URL = "https://htkdtm.onrender.com"; 
// Link Bot Node.js (dùng cho tích hợp ChatBot sau)
const CHATBOT_BASE_URL = "https://htkdtm-chatbot1.onrender.com"; 

export default function CourseVideoPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const course = state?.course;

  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mainVideoId, setMainVideoId] = useState(null); 

  // Lấy video theo tên môn học (Tự động chạy khi load trang)
  useEffect(() => {
    if (!course?.title) {
      setLoading(false);
      return;
    }

    const fetchVideos = async () => {
      try {
        const keyword = encodeURIComponent(course.title + " full course tutorial"); // Thêm từ khóa "tutorial" để tìm video chất lượng hơn
        const response = await axios.get(`${API_BASE_URL}/api/youtube/${keyword}`);
        
        if (response.data && Array.isArray(response.data) && response.data.length > 0) {
          setVideos(response.data);
          setMainVideoId(response.data[0].videoId); 
        } else {
          setVideos([]);
          setMainVideoId(null);
        }
        setError(null);
      } catch (err) {
        console.error("Lỗi khi tải video:", err);
        setError("Không thể tải tài liệu. Kiểm tra API Key và kết nối Render/Vercel.");
        setVideos([]); 
        setMainVideoId(null);
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, [course?.title]); 

  // Fallback UI (Trường hợp lỗi)
  if (!course) {
    return (
      <div className="course-video-page-wrapper fallback-message">
        <h2>⚠️ Không tìm thấy thông tin khóa học.</h2>
        <button className="navigate-back-btn" onClick={() => navigate("/schedule")}>
          ← Quay lại các môn đang học
        </button>
      </div>
    );
  }
  
  // Loading UI
  if (loading) {
    return (
      <div className="course-video-page-wrapper loading-state">
        <div className="spinner"></div>
        <h2>⏳ Đang tìm kiếm tài liệu cho môn: **{course.title}**...</h2>
        <p>Vui lòng chờ giây lát để hệ thống tải video từ YouTube.</p>
      </div>
    );
  }

  return (
    <div className="course-video-page-container fade-in-section">
      
      {/* HEADER SECTION */}
      <header className="course-header-section">
        <h1><span role="img" aria-label="books">📘</span> Tài liệu tham khảo: {course.title}</h1>
        <p className="subtitle">
          Khám phá các video hướng dẫn chi tiết liên quan đến môn học của bạn.
        </p>
        <button className="navigate-back-btn" onClick={() => navigate("/schedule")}>
          <span role="img" aria-label="back-arrow">←</span> Quay lại
        </button>
      </header>

      {/* ERROR MESSAGE */}
      {error && <div className="error-message error-box">❌ {error}</div>}


      <div className="main-content-area">
        
        {/* CỘT CHÍNH: VIDEO PLAYER */}
        <div className="video-player-main-column">
          {mainVideoId ? (
            <div className="video-player-box">
              <iframe
                width="100%"
                height="500"
                src={`https://www.youtube.com/embed/${mainVideoId}`}
                title={`Video tham khảo: ${course.title}`}
                frameBorder="0"
                allowFullScreen
              ></iframe>
            </div>
          ) : (
             <div className="no-video-found-box">
              <span role="img" aria-label="magnifying-glass">🔎</span> Không tìm thấy video tham khảo nào cho môn này.
            </div>
          )}

          {/* CHATBOT INTEGRATION SECTION (Giao diện chuẩn bị) */}
          <div className="chatbot-integration-area">
              <h3><span role="img" aria-label="robot">🤖</span> Hỏi đáp cùng SmartBot</h3>
              <p>Bot có thể trả lời các câu hỏi chuyên sâu về môn **{course.title}**.</p>
              {/* Ở đây anh sẽ nhúng Component ChatBot đã deploy vào */}
              {/* <Chatbot topic={course.title} apiUrl={`${CHATBOT_BASE_URL}/chat`} /> */}
          </div>
        </div>


        {/* CỘT LỀ: DANH SÁCH VIDEO */}
        <aside className="video-list-sidebar">
          <h2><span role="img" aria-label="playlist">🎬</span> Đề xuất ({videos.length})</h2>
          <p className="sidebar-description">Chọn video để xem:</p>
          
          <ul className="video-thumbnails-list">
            {videos.length > 0 ? (
                videos.map((video, index) => (
                    <li 
                      key={index} 
                      className={`video-list-item ${video.videoId === mainVideoId ? 'active-video' : ''}`}
                      onClick={() => setMainVideoId(video.videoId)} // Bấm vào là đổi video chính
                    >
                        <img src={video.thumbnail} alt={video.title} className="video-thumbnail" />
                        <div className="video-title-text">
                            <strong>{video.title}</strong>
                        </div>
                    </li>
                ))
            ) : (
                <p>Không có đề xuất video nào.</p>
            )}
          </ul>
        </aside>
      </div>
    </div>
  );
}