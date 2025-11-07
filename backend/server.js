import express from "express";
import fetch from "node-fetch";
import cors from "cors";



const app = express();
app.use(cors()); // cho phép frontend React gọi API
app.use(express.json());

// 🧠 Route chatbot
app.post("/chat", async (req, res) => {
  try {
    const userMessage = req.body.message;
    if (!userMessage) {
      return res.status(400).json({ reply: "Không có tin nhắn nào được gửi!" });
    }

    // Gọi Google Gemini API
    const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${process.env.GEMINI_API_KEY}`,
    {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
        contents: [
            {
            parts: [
                {
                text: `Bạn là SmartBot – trợ lý học tập cho sinh viên ngành Công nghệ thông tin.
                Câu hỏi của sinh viên: "${userMessage}".
                Hãy trả lời ngắn gọn, dễ hiểu, bằng tiếng Việt, có ví dụ hoặc gợi ý tài liệu liên quan.`,
                },
            ],
            },
        ],
        }),
    }
    );


    const data = await response.json();

    // 🧾 In phản hồi thực tế từ Gemini ra terminal (debug)
    console.log("📩 Gemini raw response:");
    console.log(JSON.stringify(data, null, 2));

    const reply =
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      "Xin lỗi, mình chưa hiểu câu hỏi này 😅";

    res.json({ reply });
  } catch (error) {
    console.error("🔥 Lỗi chatbot:", error);
    if (error.response) {
      const errText = await error.response.text();
      console.error("🧾 Lỗi chi tiết từ Gemini:", errText);
    }
    res.status(500).json({ reply: "Lỗi khi gọi API Gemini 😥" });
  }
});

// 🔥 Khởi động server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 Chatbot server đang chạy tại http://localhost:${PORT}`);
});
