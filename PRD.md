# Product Requirement Document (PRD) — BotAutoCRM

## 1. Tổng quan dự án (Project Overview)
**BotAutoCRM** là hệ thống AI Co-Pilot tích hợp CRM dành cho Relationship Manager (RM) tại Ngân hàng TMCP A. Hệ thống giúp RM tự động hóa việc truy xuất hồ sơ khách hàng, quản lý cơ hội bán hàng, soạn thảo email/script tư vấn và nhắc lịch làm việc, từ đó nâng cao năng suất và hiệu quả bán hàng. Dự án tận dụng **Bộ não thông minh chủ động Interactions API** (phát hành tháng 6/2026 của Google) làm nền tảng xử lý mặc định, kết hợp với **Cánh tay thực thi Antigravity SDK** để quản lý các tác nhân cục bộ tích hợp MCP Server. Hệ thống được trang bị cơ chế **Multi-LLM Resilience** tự động fallback sang các LLM thay thế để đảm bảo độ tin cậy tuyệt đối.

---

## 2. Bài toán & Giải pháp tinh gọn nhất (Complexity Reduction)
### Bài toán thực tế
RM mất từ 2-3 giờ mỗi ca làm việc để thực hiện thủ công các thao tác trên CRM (tìm kiếm khách hàng, xem lịch sử giao dịch, tạo cơ hội bán hàng mới, soạn email tư vấn theo template). Salesforce hoặc MS Copilot có chi phí rất cao và khó tùy biến sâu để tích hợp với các hệ thống nội địa của Ngân hàng A. Đồng thời, nguy cơ gián đoạn kết nối LLM (hết quota, mất mạng Internet) là rất lớn trong các buổi demo trực tiếp.

### Giải pháp tinh gọn (Simplest Solution)
Xây dựng một ứng dụng Web Chat Co-Pilot có giao diện tương tác cao (Generative UI):
* RM ra lệnh bằng ngôn ngữ tự nhiên (tiếng Việt).
* AI Agent sử dụng **MCP Server** để kết nối trực tiếp với CRM Sandbox API, tự động điền thông tin và thực hiện các tác vụ CRM.
* **Bộ não thông minh chủ động & Đa LLM (Interactions API & LLM Router):**
  * *Mặc định:* Backend Proxy sử dụng Interactions API của Google với tham số `previous_interaction_id` để duy trì lịch sử hội thoại trên máy chủ Google (Server-side State), tối ưu hóa Context Caching, giảm chi phí token và giảm độ trễ (latency < 5s).
  * *Cơ chế dự phòng (Resilience Fallback):* Nếu Interactions API gặp sự cố (lỗi mạng, hết quota, lỗi 429/503), lớp **LLM Router** tại Backend Proxy sẽ tự động định tuyến lại yêu cầu sang các LLM thay thế (OpenAI GPT-4o-mini, Anthropic Claude 3.5 Sonnet, hoặc Local Ollama chạy ngoại tuyến hoàn toàn). Khi chuyển đổi, lịch sử chat in-memory sẽ được gửi đầy đủ dưới dạng stateless message array để đảm bảo tính liên tục của ngữ cảnh.
* **Cánh tay thực thi (Antigravity SDK):** Sử dụng Antigravity SDK làm framework điều phối ở Backend để khởi chạy Agent, tự động nạp các công cụ từ Stateless MCP Server cục bộ qua stdio transport và điều phối quá trình tool-calling nhất quán bất kể LLM nào đang xử lý.

---

## 3. Các Luồng Nghiệp Vụ Cốt Lõi (Contexts)
Hệ thống hỗ trợ chuyển mạch mượt mà giữa 3 ngữ cảnh chính thông qua cơ chế chuyển đổi context thông minh:

1. **Hồ sơ khách hàng & Lịch sử tương tác (Customer Profile & Interaction History)**
   * Tra cứu thông tin cá nhân, phân khúc khách hàng, số dư tài khoản.
   * Xem và thêm mới lịch sử tương tác (cuộc gọi, email, buổi gặp mặt). Khi RM bấm "Gửi Email" trên UI, một bản ghi tương tác mới sẽ tự động được ghi nhận ngược lại CRM.
2. **Cơ hội bán hàng (Opportunity)**
   * Liệt kê danh sách cơ hội bán hàng hiện tại của khách hàng.
   * Tạo mới, cập nhật trạng thái cơ hội bán hàng (New, Contacted, Proposal, Won, Lost) thông qua Card tương tác trực tiếp.
3. **Chiến dịch & Sản phẩm (Campaign & Knowledge Base)**
   * Truy vấn danh sách các chiến dịch marketing đang áp dụng cho khách hàng.
   * Tra cứu tài liệu sản phẩm (lãi suất tiết kiệm, điều khoản tín dụng, gói bảo hiểm liên kết).

---

## 4. Yêu cầu Chức năng & Giao diện (Functional & UI Requirements)

### Generative UI (Interactive UI Components)
Để tạo ra hiệu ứng **Wow-factor** trong buổi demo Hackathon, giao diện chat không chỉ hiển thị text đơn thuần mà tích hợp các React component động:
* **Customer Info Card:** Hiển thị thông tin tổng hợp của khách hàng (Tên, tuổi, phân khúc, liên hệ, người quản lý).
* **Interaction Timeline:** Dòng thời gian lịch sử tương tác trực quan.
* **Opportunity Manager Card:** Hiển thị trạng thái các cơ hội bán hàng và nút bấm chuyển đổi nhanh trạng thái, hoặc form tạo cơ hội bán hàng mới.
* **Email/Script Editor Box:** Khi Agent soạn email/script tư vấn, hiển thị trong một khung soạn thảo riêng biệt kèm nút bấm "Edit" (RM tự sửa) và "Gửi Email" (khi click sẽ gọi API CRM tạo lịch sử tương tác mới).

### CRM Sandbox API & Hackathon Fallback
* AI Agent sẽ gọi đến các endpoint thực tế của hệ thống CRM Sandbox tại địa chỉ `sandbox.crm.banka.vn`.
* **Cơ chế Fallback:** Trong trường hợp mạng internet tại địa điểm demo bị lỗi hoặc server sandbox không phản hồi, mã nguồn Client/Server phải tự động chuyển sang đọc dữ liệu mô phỏng từ các file JSON cục bộ (`local_mockup/*.json`) để đảm bảo buổi demo không bị gián đoạn.

---

## 5. Yêu cầu Phi chức năng & Bảo mật (Non-Functional Requirements)

### Hiệu năng (Performance)
* Latency xử lý yêu cầu đơn giản (ví dụ: tra cứu 1 khách hàng) phải $\le 5$ giây.
* Latency xử lý yêu cầu phức tạp (ví dụ: tổng hợp thông tin từ nhiều nguồn để soạn script) phải $\le 15$ giây.
* Sử dụng mô hình **Gemini 1.5 Flash** (hoặc `gemini-3.5-flash` khi chạy thực tế trên Interactions API) làm mặc định. Tự động fallback sang OpenAI GPT-4o-mini hoặc Claude 3.5 Sonnet với latency tối ưu.

### Bảo mật & Lưu trữ (Security & Storage)
* **Stateless Chat (Local Database):** Không lưu trữ nội dung chat dưới dạng plain text trên ổ đĩa cứng của server proxy hay local database. Lịch sử chat được lưu trữ an toàn phía máy chủ Google thông qua Interactions API (lưu giữ 1 ngày cho tài khoản free, 55 ngày cho tài khoản enterprise) hoặc lưu hoàn toàn in-memory tại Backend Proxy (khi chạy chế độ fallback). Trên client, lịch sử chỉ lưu tạm trên React state (tắt trình duyệt là mất).
* **Audit Log:** Ghi log bảo mật vào một cơ sở dữ liệu SQLite cục bộ (hoặc Supabase).
  * **Thông tin ghi log:** Timestamp, lượng tokens tiêu thụ (input/output/thinking), và nội dung prompt.
  * **Masking:** Nội dung prompt ghi log phải được lọc bỏ/thế chỗ các từ nhạy cảm có trong từ điển định nghĩa sẵn (ví dụ: thay số tài khoản, tên khách hàng thành `[MASKED]`).
* **Tính Chính xác của Số liệu (No Hallucination):** Agent không được tự bịa ra số liệu thống kê (như số lượng khách hàng cần xử lý, số tiền, tên cơ hội) trong lời chào hoặc phản hồi khi chưa thực sự gọi tool MCP để truy vấn dữ liệu thực tế từ CRM.

---

## 6. Thiết kế Module Sâu (Deep Modules - Ousterhout Principle)
Để giữ hệ thống gọn gàng, tránh hiện tượng manh mún code ("Class-itis"), các module cốt lõi sẽ được thiết kế theo hướng **Deep Module** (giao diện đơn giản, che giấu độ phức tạp cao bên dưới):

### 1. `CRMClient` (Module kết nối CRM)
* **Interface đơn giản:** Expose các phương thức như `get_client_profile(client_id)`, `update_opportunity(opp_id, status)`, `get_campaigns(client_id)`.
* **Thông tin bị che giấu (Information Hiding):**
  * Logic tự động định tuyến: gọi API thực (`sandbox.crm.banka.vn`) hay fallback đọc file JSON cục bộ khi gặp lỗi kết nối.
  * Chi tiết cấu trúc HTTP requests, xử lý HTTP errors và rate-limit.

### 2. `AuditLogger` (Module giám sát bảo mật)
* **Interface đơn giản:** `log_turn(prompt, response, tokens_metadata)`.
* **Thông tin bị che giấu:**
  * Logic so khớp từ khóa và thay thế dữ liệu nhạy cảm bằng `[MASKED]`.
  * Cơ chế kết nối và ghi dữ liệu không đồng bộ (async write) vào SQLite cục bộ để không ảnh hưởng đến latency của luồng chat chính.

### 3. `ConversationOrchestrator` (Module quản lý hội thoại & LLM Router)
* **Interface đơn giản:** `send_message(session_id, user_message)`.
* **Thông tin bị che giấu:**
  * Tích hợp **LLM Router**: Tự động phát hiện lỗi và chuyển mạch giữa Interactions API (Gemini), OpenAI API, Anthropic API, và Local Ollama.
  * Tự động điều chỉnh cơ chế quản lý trạng thái: Sử dụng `previous_interaction_id` phía Google Server (đối với Gemini) hoặc tự động đóng gói toàn bộ mảng chat history gửi đi (đối với các LLM fallback khác).
  * Tích hợp **Google Antigravity SDK** để quản lý các custom local agents và liên kết MCP Server local process.
  * Điều phối hành vi chủ động (Proactive Interaction) bằng cách hướng dẫn Agent phân tích ngữ cảnh thực tế (sau khi gọi tool CRM) để đề xuất bước tiếp theo cho RM thông qua System Instruction.
