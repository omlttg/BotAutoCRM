# BotAutoCRM Co-Pilot 🤖💼

> **Hệ thống AI Co-Pilot tích hợp CRM thông minh dành cho Quan hệ Khách hàng (Relationship Manager - RM) tại Ngân hàng TMCP A.**

BotAutoCRM hỗ trợ các RM tự động hóa quy trình tra cứu hồ sơ khách hàng, cập nhật cơ hội bán hàng, soạn thảo email/script tư vấn cá nhân hóa và tự động lưu vết lịch sử tương tác. Hệ thống được thiết kế theo các tiêu chuẩn kỹ thuật hiện đại, đảm bảo tính sẵn sàng cao và bảo mật dữ liệu khách hàng tuyệt đối.

---

## ✨ Các Tính Năng Nổi Bật

1. **Giao Diện Động Tương Tác Cao (Generative UI)**:
   - Khung chat không chỉ hiển thị văn bản thuần túy mà tự động render các thẻ tương tác thông minh dựa trên dữ liệu JSON trả về từ Agent:
     - **Customer Profile Card**: Hồ sơ chi tiết khách hàng (VIP/Gold/Standard), phân khúc, số dư.
     - **Interaction Timeline**: Dòng thời gian lịch sử giao tiếp (Email, Cuộc gọi, SMS, Gặp mặt).
     - **Opportunity Manager**: Trạng thái các cơ hội bán hàng và cụm nút bấm cập nhật nhanh trạng thái (Mới, Đã liên hệ, Đề xuất, Thành công, Thất bại).
     - **Email Editor Box**: Trình soạn thảo thư mẫu nháp cho phép RM chỉnh sửa trực tiếp và bấm gửi (khi gửi sẽ tự động gọi API ghi nhận tương tác mới vào CRM).

2. **Cơ Chế Dự Phòng Đa Mô Hình (Multi-LLM Resilience - LLM Router)**:
   - Mặc định sử dụng **Gemini 3.5 Flash** (hoặc Interactions API của Google) để tối ưu chi phí token, context caching và độ trễ.
   - Khi gặp sự cố mạng hoặc lỗi vượt hạn ngạch (Quota Limit - HTTP 429), lớp **LLM Router** tại Backend Proxy sẽ tự động chuyển mạch (fallback) sang **OpenAI (GPT-4o-mini)** ➔ **Anthropic (Claude 3.5 Sonnet)** ➔ **Local Ollama (Llama3)** ➔ **Mock LLM Engine (Offline Demo Mode)** để đảm bảo ứng dụng không bao giờ bị crash.
   - Khi chuyển mạch, ngữ cảnh lịch sử chat in-memory sẽ được đóng gói và gửi kèm để cuộc hội thoại diễn ra liên tục.

3. **Cánh Tay Thực Thi Mạnh Mẽ (Antigravity SDK & Stateless MCP)**:
   - Sử dụng **Google Antigravity SDK** làm framework điều phối agent ở Backend.
   - Kết nối với **Stateless FastMCP Server** nội bộ qua stdio transport cung cấp 6 công cụ (tools) nghiệp vụ CRM. MCP Server không lưu trạng thái hội thoại mà chỉ thực thi truy xuất/cập nhật dữ liệu từ CRM.

4. **Bảo Mật & Giám Sát (Security Audit Log & PII Masking)**:
   - Ghi nhận lịch sử gọi API, lượng token tiêu thụ và nội dung prompt vào cơ sở dữ liệu SQLite cục bộ (`audit.db`) một cách bất đồng bộ để tránh ảnh hưởng đến độ trễ hệ thống.
   - Tích hợp bộ lọc Regex bảo mật tự động phát hiện và che giấu (masking) các thông tin nhạy cảm PII (Số thẻ tín dụng, Số tài khoản ngân hàng) thành `[CARD_MASKED]` và `[ACCOUNT_MASKED]` trước khi lưu log.

---

## 📂 Cấu Trúc Thư Mục Dự Án

```bash
BotAutoCRM/
├── README.md                    # Tài liệu hướng dẫn dự án (file này)
├── PRD.md                       # Đặc tả yêu cầu sản phẩm (Product Requirement Document)
├── AGENTS.md                    # Quy trình làm việc nội bộ của AI Agent (Vibe Code + Ousterhout)
├── CLAUDE.md                   # Symlink trỏ đến AGENTS.md
├── GEMINI.md                   # Symlink trỏ đến AGENTS.md
├── HANDOFF.md                   # Nhật ký chuyển giao phiên làm việc giữa các Agent
├── run_demo.sh                  # Script khởi chạy đồng thời Backend và Frontend (One-touch)
├── .env.example                 # File mẫu cấu hình biến môi trường
├── backend/                     # API BFF (FastAPI) & Agent Runtime
│   ├── app.py                   # FastAPI app (BFF, CORS, API Chat, Security Logs)
│   ├── crm_client.py            # Deep Module kết nối CRM Sandbox / fallback Offline JSON data
│   ├── mcp_server.py            # Stateless FastMCP Server cung cấp 6 tools CRM
│   ├── llm_router.py            # Bộ não định tuyến LLM Router (Gemini -> OpenAI -> Claude -> Ollama)
│   ├── audit_log.py             # SQLite Audit Logger tích hợp PII Masking
│   ├── requirements.txt         # Các thư viện Python cần thiết
│   └── local_mockup/            # Dữ liệu khách hàng giả lập ngoại tuyến (Offline mockup)
│       ├── clients.json
│       ├── interactions.json
│       ├── opportunities.json
│       └── knowledge.json
└── frontend/                    # Ứng dụng client (React + Vite + Tailwind CSS)
    ├── src/
    │   ├── App.jsx              # Điểm nạp ứng dụng chính
    │   ├── index.css            # CSS cấu hình Glassmorphism & Neon styles
    │   └── components/
    │       ├── ChatInterface.jsx # Giao diện chat Co-Pilot & Security Logs Panel
    │       └── InteractiveCards.jsx # Các Generative UI Components hiển thị động
    └── package.json             # Các thư viện JS cần thiết
```

---

## ⚙️ Hướng Dẫn Khởi Chạy

### 1. Cài đặt các phụ thuộc (Dependencies)

**Backend:**
Yêu cầu Python $\ge 3.10$. Tạo môi trường ảo và cài đặt thư viện:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

**Frontend:**
Cài đặt các gói Javascript:
```bash
cd frontend
npm install
cd ..
```

### 2. Cấu hình biến môi trường
Sao chép tệp cấu hình mẫu và điền thông tin API Key của bạn:
```bash
cp .env.example .env
```
*Mở file `.env` và điền `GEMINI_API_KEY`. Nếu chạy thử nghiệm Hackathon không có mạng hoặc không có API key, hãy cấu hình `OFFLINE_MODE=true` trong file `.env`.*

### 3. Khởi chạy bằng một dòng lệnh
Chạy script khởi động đồng thời cả Backend (port 8001) và Frontend (port 5173):
```bash
chmod +x run_demo.sh
./run_demo.sh
```
Sau khi khởi chạy thành công, vui lòng truy cập trình duyệt tại địa chỉ: **[http://localhost:5173](http://localhost:5173)**

---

## 🛠️ Thiết Kế Module Sâu (Deep Modules)

Theo nguyên lý thiết kế của *John Ousterhout*, hệ thống đóng gói các logic phức tạp đằng sau các giao diện (interface) đơn giản:
*   **`CRMClient`**: Ẩn giấu hoàn toàn cơ chế tự động chuyển mạch giữa gọi API Sandbox thực và đọc dữ liệu từ file JSON giả lập ngoại tuyến.
*   **`LLMRouter`**: Che giấu cơ chế định tuyến đa LLM (Gemini/OpenAI/Anthropic/Ollama) và logic duy trì lịch sử hội thoại dạng Server-side State (Interactions API) hoặc Stateless array.
*   **`AuditLogger`**: Đảm nhiệm việc ghi log bất đồng bộ (SQLite) và tự động lọc dữ liệu nhạy cảm PII bằng Regex, các module ngoài chỉ cần gọi `log_turn(prompt, response, tokens)`.
