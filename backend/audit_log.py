import sqlite3
import os
import re
import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

# Design Intent (Ý đồ thiết kế):
# Module AuditLogger được thiết kế làm Deep Module xử lý ghi log bảo mật.
# Nó chịu trách nhiệm:
# 1. Che giấu thông tin PII nhạy cảm (như số tài khoản, số thẻ tín dụng) trong prompt
#    bằng regex masking trước khi ghi log để đảm bảo không lưu clear text trên ổ cứng.
# 2. Thực hiện các thao tác ghi cơ sở dữ liệu SQLite cục bộ một cách bất đồng bộ (async)
#    thông qua ThreadPoolExecutor nhằm không làm ảnh hưởng đến độ trễ phản hồi (latency) của RM.
# 3. Giao diện cực kỳ đơn giản: Chỉ expose phương thức `log_turn()`.

DB_PATH = os.path.join(os.path.dirname(__file__), "audit.db")
executor = ThreadPoolExecutor(max_workers=2)

def mask_sensitive_data(text: str) -> str:
    """Che giấu thông tin nhạy cảm: Số thẻ (16 số) và Số tài khoản (10-12 số)."""
    if not text:
        return text
    # Mask số thẻ 16 chữ số (e.g. 9704 1234 5678 9012 hoặc 9704-1234-5678-9012 hoặc 9704123456789012)
    masked = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_MASKED]', text)
    # Mask số tài khoản ngân hàng từ 10 đến 12 chữ số
    masked = re.sub(r'\b\d{10,12}\b', '[ACCOUNT_MASKED]', masked)
    return masked

def _sync_init_db():
    """Khởi tạo SQLite database và tạo bảng log."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def _sync_log_turn(session_id: str, model_name: str, prompt: str, response: str, input_tokens: int, output_tokens: int):
    """Thực thi ghi SQLite đồng bộ (được chạy qua Executor)."""
    # Thực hiện che giấu dữ liệu nhạy cảm trước khi lưu
    masked_prompt = mask_sensitive_data(prompt)
    masked_response = mask_sensitive_data(response)
    
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (timestamp, session_id, model_name, prompt, response, input_tokens, output_tokens)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, session_id, model_name, masked_prompt, masked_response, input_tokens, output_tokens))
    conn.commit()
    conn.close()

class AuditLogger:
    def __init__(self):
        # Khởi tạo DB khi load class
        _sync_init_db()

    async def log_turn(self, session_id: str, model_name: str, prompt: str, response: str, input_tokens: int = 0, output_tokens: int = 0):
        """API Async ghi log hội thoại không đồng bộ."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            executor, 
            _sync_log_turn, 
            session_id, 
            model_name, 
            prompt, 
            response, 
            input_tokens, 
            output_tokens
        )

    def get_logs(self, limit: int = 50) -> list:
        """Lấy danh sách audit logs gần nhất (phục vụ hiển thị trên giao diện demo)."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append(dict(row))
        return result
