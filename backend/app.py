import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from llm_router import LLMRouter
from audit_log import AuditLogger

# Design Intent (Ý đồ thiết kế):
# FastAPI application đóng vai trò là Backend Proxy (BFF - Backend for Frontend).
# Nó tiếp nhận các HTTP requests từ React Frontend và điều phối logic hội thoại:
# 1. Endpoint `/api/chat` xử lý đồng bộ tin nhắn qua LLMRouter.
# 2. Endpoint `/api/chat/background` tận dụng BackgroundTasks của FastAPI
#    kết hợp với Interactions API của Google (`background=true`) để chạy các tác vụ lâu.
# 3. Endpoint `/api/audit-logs` expose logs SQLite đã che giấu PII giúp RM kiểm tra bảo mật.
# 4. CORS được bật cho phép Frontend React tích hợp mượt mà.

app = FastAPI(title="BotAutoCRM Co-Pilot API", version="1.0.0")

# Cấu hình CORS để React Frontend gọi được API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong thực tế sản xuất sẽ hạn chế lại domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo Router và Logger
llm_router = LLMRouter()
audit_logger = AuditLogger()

# Pydantic Schemas cho API Requests
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    model: str
    session_id: str
    warning: Optional[str] = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """Xử lý hội thoại thông thường giữa RM và Co-Pilot."""
    try:
        # Gọi Router để lấy phản hồi từ LLM hoạt động tốt nhất
        result = await llm_router.generate_response(request.session_id, request.message)
        
        # Ghi log bảo mật (chạy bất đồng bộ)
        background_tasks.add_task(
            audit_logger.log_turn,
            session_id=request.session_id,
            model_name=result["model"],
            prompt=request.message,
            response=result["response"]
        )
        
        return ChatResponse(
            response=result["response"],
            model=result["model"],
            session_id=request.session_id,
            warning=result.get("warning")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_background_task_logic(session_id: str, message: str):
    """Logic thực thi tác vụ nền (Background Task)."""
    # Gửi tín hiệu giả lập đến Interactions API với background=true hoặc xử lý bất đồng bộ
    # Ở đây chúng ta gọi Router và giả lập tiến trình chạy ngầm
    await asyncio.sleep(5.0)  # Giả lập thời gian chạy nền phân tích
    await llm_router.generate_response(session_id, f"[BACKGROUND_TASK_TRIGGER] {message}")

@app.post("/api/chat/background")
async def chat_background_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """Endpoint xử lý các tác vụ nặng chạy ngầm của RM."""
    background_tasks.add_task(run_background_task_logic, request.session_id, request.message)
    return {
        "status": "processing",
        "message": "Yêu cầu của bạn đang được xử lý ở chế độ nền. Kết quả sẽ tự động hiển thị sau khi hoàn tất.",
        "session_id": request.session_id
    }

@app.get("/api/audit-logs")
async def get_audit_logs(limit: Optional[int] = 50):
    """Expose danh sách audit logs để hiển thị trên giao diện demo."""
    try:
        logs = audit_logger.get_logs(limit=limit)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}")
async def get_session_history(session_id: str):
    """Lấy toàn bộ lịch sử trò chuyện in-memory của phiên làm việc."""
    history = llm_router._get_history(session_id)
    return {"history": history}

@app.get("/api/health")
async def health_check():
    """Endpoint kiểm tra sức khỏe của dịch vụ."""
    return {"status": "ok", "environment": "development"}

if __name__ == "__main__":
    import uvicorn
    import asyncio
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
