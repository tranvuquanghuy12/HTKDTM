import React, { useState } from "react";
import axios from "axios";
import "./Login.css";

export default function Login({ onLoginSuccess }) {
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [fadeOut, setFadeOut] = useState(false); // Hiệu ứng chuyển trang

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await axios.post("https://htkdtm.onrender.com/api/login", {
        student_id: studentId,
        password: password,
      });

      if (res.data.success) {
        // Hiệu ứng fade-out trước khi vào Dashboard
        localStorage.setItem('tlu_token', auth_result.access_token);
        setFadeOut(true);
        setTimeout(() => {
          onLoginSuccess(res.data.student);
        }, 700); // Thời gian khớp với animation CSS
      } else {
        setError(res.data.message || "Sai mã sinh viên hoặc mật khẩu!");
      }
    } catch (err) {
      setError("Lỗi kết nối server!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`login-container ${fadeOut ? "fade-out" : ""}`}>
      <div className="login-card">
        <h2>&#127891; Smart Learning System</h2>
        <p>Đăng nhập bằng tài khoản TLU</p>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            placeholder="Nhập mã sinh viên..."
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Nhập mật khẩu..."
            required
          />

          <button type="submit" disabled={loading}>
            {loading ? <div className="loading-spinner"></div> : "Đăng nhập"}
          </button>
        </form>

        {error && <p className="error-text">{error}</p>}
      </div>
    </div>
  );
}
