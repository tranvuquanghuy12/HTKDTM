import React, { useState } from "react";
import "./Chatbot.css";

function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { text: "Xin chào! Mình là SmartBot 🤖 – trợ lý học tập của bạn.", sender: "bot" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const newMessage = { text: input, sender: "user" };
    setMessages((prev) => [...prev, newMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("https://htkdtm-chatbot1.onrender.com/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        { text: data.reply || "Xin lỗi, mình chưa hiểu câu hỏi này 😅", sender: "bot" },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { text: "⚠️ Lỗi kết nối tới server. Kiểm tra lại backend nhé!", sender: "bot" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") handleSend();
  };

  return (
    <>
      {/* Nút bật/tắt */}
      <button className="chatbot-toggle" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? "✖ Đóng Chatbot" : "💬 Chat SmartBot"}
      </button>

      {/* Hộp chat */}
      {isOpen && (
        <div className="chatbot">
          <div className="chat-window">
            {messages.map((msg, i) => (
              <div key={i} className={msg.sender === "bot" ? "bot-msg" : "user-msg"}>
                {msg.text}
              </div>
            ))}
            {loading && <div className="bot-msg">SmartBot đang suy nghĩ... 💭</div>}
          </div>

          <div className="chat-input">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Nhập câu hỏi về học tập..."
            />
            <button onClick={handleSend}>Gửi</button>
          </div>
        </div>
      )}
    </>
  );
}

export default Chatbot;
