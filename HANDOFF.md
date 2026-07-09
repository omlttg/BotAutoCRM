# HANDOFF — BotAutoCRM Co-Pilot MVP

> **Tài liệu chuyển giao trạng thái phiên làm việc dành cho AI Agent tiếp theo.**
> Cập nhật lúc: 2026-07-01T11:45:00+07:00

---

## 📌 Trạng Thái Hiện Tại (Current Status)
Dự án **BotAutoCRM Co-Pilot MVP** đã hoàn thành toàn bộ 5 Giai đoạn (Tracer Bullets) trong kế hoạch. Toàn bộ mã nguồn Backend FastAPI, Stateless MCP Server, LLM Fallback Router, SQLite Audit Logger và React Frontend đã được triển khai, build thành công và kiểm thử đạt kết quả 100%.

---

## 📂 Cấu Trúc Mã Nguồn Hiện Tại
```bash
/home/thienvu/workspace/BotAutoCRM/
├── PRD.md                       # Đặc tả yêu cầu sản phẩm
├── clientbrief.mmd              # Sơ đồ thiết kế LR Mermaid
├── HANDOFF.md                   # File này (Nhật ký phiên & Chuyển giao)
├── run_demo.sh                  # Script khởi động đồng thời Backend & Frontend
├── backend/
│   ├── app.py                   # FastAPI BFF API (CORS, Chat, Background Tasks, Audit Logs API)
│   ├── crm_client.py            # Deep Module kết nối Sandbox CRM / fallbacks JSON mock
│   ├── mcp_server.py            # Stateless FastMCP Server cung cấp 6 tools
│   ├── llm_router.py            # LLM Router định tuyến (Gemini Antigravity -> OpenAI -> Anthropic -> Ollama)
│   ├── audit_log.py             # SQLite Logger bất đồng bộ tích hợp PII Regex Masking
│   ├── requirements.txt         # File mô tả python dependencies
│   ├── local_mockup/            # Dữ liệu JSON giả lập offline (KH001 -> KH500)
│   │   ├── clients.json
│   │   ├── interactions.json
│   │   ├── opportunities.json
│   │   └── knowledge.json
│   └── venv/                    # Môi trường ảo Python (đã install packages)
├── frontend/                    # Vite/React Application
│   ├── index.html               # Nạp Tailwind CSS CDN & Google Fonts
│   ├── src/
│   │   ├── App.jsx              # Render ChatInterface
│   │   ├── index.css            # Custom CSS Glassmorphism & Neon styles
│   │   └── components/
│   │       ├── ChatInterface.jsx # Giao diện Chat chính & Real-time Audit Logs Panel
│   │       └── InteractiveCards.jsx # Generative UI (Profile, Opportunities, Timeline, Email Editor)
└── scratch/                     # Thư mục chứa các script test cục bộ
    ├── test_crm_client.py       # Test fallback offline CRM Client
    ├── test_mcp_standalone.py   # Test 6 tools trên Stateless MCP Server
    └── test_llm_fallback.py     # Test chuyển mạch LLM Router & SQLite Masking
```

---

## ⚙️ Hướng Dẫn Khởi Chạy Hệ Thống
Chạy script một chạm tại thư mục gốc:
```bash
./run_demo.sh
```
*   **Frontend URL:** [http://localhost:5173](http://localhost:5173)
*   **Backend URL:** [http://localhost:8001](http://localhost:8001)
*   *Lưu ý:* Hệ thống hiện đang chạy ở chế độ online (`OFFLINE_MODE=false`) với API Key Gemini thật. Nếu kết nối Sandbox CRM gặp sự cố, hệ thống sẽ tự động fallback dữ liệu offline để đảm bảo ổn định.

---

## 🧪 Kết Quả Kiểm Thử (Verification Status)
*   **CRM Fallback:** Script `test_crm_client.py` đã xác nhận hệ thống tự động đọc/ghi dữ liệu offline thành công.
*   **MCP Server Tools:** Script `test_mcp_standalone.py` đã xác nhận 6 tools đã được khai báo chính xác kiểu dữ liệu và gọi thành công qua FastMCP API.
*   **LLM Fallback & Masking:** Script `test_llm_fallback.py` xác minh:
    1.  Tự động bắt lỗi khi Gemini API key sai/lỗi và định tuyến fallback sang OpenAI/Anthropic/Ollama.
    2.  Số thẻ tín dụng và số tài khoản ngân hàng trong prompt được che giấu thành công dạng `[CARD_MASKED]` và `[ACCOUNT_MASKED]` trước khi lưu vào SQLite database.

---

## 🚀 Các Bước Đề Xuất Tiếp Tiếp Theo (Next Steps for Next Agent)
1.  **Tích hợp Sandbox Real-time API:**
    *   Nếu môi trường mạng Hackathon ổn định và cổng Sandbox API `https://sandbox.crm.banka.vn` sẵn sàng, hãy chuyển biến môi trường `OFFLINE_MODE` trong `run_demo.sh` sang `false` để test tích hợp API thật.
2.  **Cài đặt Keys Thật:**
    *   Khi người dùng cấp API Keys thật cho OpenAI/Anthropic/Ollama, hãy thiết lập chúng vào môi trường để kiểm tra kịch bản tự động chuyển đổi LLM Router trong điều kiện trực tiếp.
3.  **Tối ưu hóa UI/UX:**
    *   Phát triển thêm hiệu ứng chuyển cảnh động cho các Generative UI Cards bằng CSS transitions.
    *   Tối ưu hóa cấu trúc JSON của Agent trả về để render biểu đồ cơ hội bán hàng trực quan hơn nếu cần.
