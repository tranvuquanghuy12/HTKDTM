import React, { useEffect, useState } from "react";
import axios from "axios";
import "./Recommendation.css";

export default function RecommendationPage({ student }) {
  // ✅ NÂNG CẤP: Thêm state cho gợi ý "Khám phá"
  const [improveRecs, setImproveRecs] = useState([]);
  const [discoverRecs, setDiscoverRecs] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!student || !student.student_id) {
        console.warn("⚠️ Chưa có thông tin sinh viên.");
        setLoading(false);
        return;
      }

      try {
        const res = await axios.get(
          `https://htkdtm.onrender.com/api/recommendation/${student.student_id}`
        );
        
        // ✅ NÂNG CẤP: Đọc 2 khóa mới từ API
        setImproveRecs(res.data.improve_recommendations || []);
        setDiscoverRecs(res.data.discover_recommendations || []);
        setMessage(res.data.message || "");
        
      } catch (err) {
        console.error("❌ Lỗi khi gọi API:", err);
        setError("Không thể tải gợi ý học tập!");
      } finally {
        setLoading(false);
      }
    };
    fetchRecommendations();
  }, [student]);

  if (loading)
    return <div className="recommendation-loading">⏳ Đang tải dữ liệu...</div>;
  if (error) return <div className="recommendation-error">{error}</div>;

  return (
    <div className="recommendation-container">
      <h2>💡 Gợi ý học tập cá nhân hoá</h2>
      <p className="recommendation-message">⚡ {message}</p>

      {/* ================================================= */}
      {/* ✅ Phần 1 - Môn học cần cải thiện (Từ AI)          */}
      {/* ================================================= */}
      {improveRecs.length > 0 && (
        <>
          <h3 className="recommendation-section-title">🎯 Môn học cần cải thiện</h3>
          <div className="recommendation-list">
            {improveRecs.map((item, idx) => (
              <div className="recommendation-card" key={`improve-${idx}`}>
                <h3 className="course-title">📘 {item.course}</h3>
                <p className="progress-text">
                  Tiến độ: <b>{item.progress}%</b>
                </p>

                {/* Lộ trình (Roadmap) do AI tạo ra */}
                <ul className="roadmap">
                  {item.roadmap.map((tip, i) => (
                    <li key={i}>✅ {tip}</li>
                  ))}
                </ul>

                {/* 🔹 Video gợi ý (Chủ đề từ AI, link từ YouTube) */}
                {item.resources?.videos?.length > 0 && (
                  <div className="resource-block">
                    <h4>📺 Video gợi ý (từ AI)</h4>
                    <div className="video-grid">
                      {item.resources.videos.slice(0, 2).map((v, i) => {
                        const videoId = v.url.split("v=")[1]?.split("&")[0];
                        const thumb = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
                        return (
                          <a
                            key={i}
                            href={v.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="video-card"
                          >
                            <img src={thumb} alt={v.title} className="video-thumb" />
                            <p className="video-title">{v.title}</p>
                          </a>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 🔹 Tài liệu tham khảo (SỬA LỖI new URL(doc)) */}
                {item.resources?.documents?.length > 0 && (
                  <div className="resource-block">
                    <h4>📘 Tài liệu tham khảo</h4>
                    <ul className="link-list">
                      {/* ‼️ SỬA LỖI: 'doc' bây giờ là object {title, url} */}
                      {item.resources.documents.map((doc, i) => (
                        <li key={i}>
                          <a
                            href={doc.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="link-truncate"
                          >
                            📄 {doc.title}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 🔹 Bài tập luyện tập (SỬA LỖI new URL(ex)) */}
                {item.resources?.exercises?.length > 0 && (
                  <div className="resource-block">
                    <h4>🧩 Bài tập luyện tập</h4>
                    <ul className="link-list">
                      {/* ‼️ SỬA LỖI: 'ex' bây giờ là object {title, url} */}
                      {item.resources.exercises.map((ex, i) => (
                        <li key={i}>
                          <a
                            href={ex.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="link-truncate"
                          >
                            💡 {ex.title}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {/* ================================================= */}
      {/* ✅ Phần 2 - Gợi ý khám phá (từ AI Lọc cộng tác)   */}
      {/* ================================================= */}
      {discoverRecs.length > 0 && (
        <>
          <h3 className="recommendation-section-title">🧭 Gợi ý khám phá (từ AI)</h3>
          <p className="recommendation-message">
            Dựa trên điểm của các sinh viên có phong cách học tập giống bạn, 
            AI gợi ý bạn có thể sẽ học tốt các môn sau:
          </p>
          <div className="recommendation-list-discover">
            {discoverRecs.map((item, idx) => (
              <div className="discover-card" key={`discover-${idx}`}>
                <h4>{item.course}</h4>
                <p>Dự đoán phù hợp: {item.predicted_score.toFixed(1)}/10</p>
                <a 
                  href={`https://www.google.com/search?q=thông+tin+môn+học+${item.course.replace(' ', '+')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="discover-link"
                >
                  Tìm hiểu môn học
                </a>
              </div>
            ))}
          </div>
        </>
      )}
      
    </div>
  );
}