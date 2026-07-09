#!/bin/bash

# Thiết lập màu sắc hiển thị
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0;5m' # No Color
RESET='\033[0;0m'

echo -e "${BLUE}================================================================${RESET}"
echo -e "${GREEN}   KHỞI CHẠY HỆ THỐNG BOTAUTOCRM CO-PILOT MVP (HACKATHON DEMO)   ${RESET}"
echo -e "${BLUE}================================================================${RESET}"

# Di chuyển về thư mục dự án
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Kích hoạt môi trường ảo Python và chạy Backend
echo -e "${YELLOW}[1/3] Đang khởi chạy API Backend (FastAPI)...${RESET}"
# Nạp biến môi trường từ file .env ở gốc nếu có
if [ -f .env ]; then
    echo -e "${YELLOW}Phát hiện file .env, đang nạp các biến môi trường...${RESET}"
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}[Cảnh báo] Chưa cấu hình biến môi trường GEMINI_API_KEY!${RESET}"
    echo -e "${YELLOW}Hệ thống sẽ chạy ở chế độ [Offline Demo Mode] (Mock LLM Engine).${RESET}"
    echo -e "${YELLOW}Để chạy với Gemini thật, vui lòng cấu hình bằng cách: export GEMINI_API_KEY='your-key' hoặc tạo file .env${RESET}"
    export OFFLINE_MODE=true
else
    echo -e "${GREEN}Đã nạp GEMINI_API_KEY thành công từ biến môi trường/file .env.${RESET}"
    export OFFLINE_MODE=false
fi

# Chạy Backend ngầm
./backend/venv/bin/python3 backend/app.py > backend.log 2>&1 &
BACKEND_PID=$!

# Đợi Backend khởi động
sleep 2

# Kiểm tra xem Backend có chạy tốt không
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}Backend đã khởi chạy thành công (PID: $BACKEND_PID) trên port 8001!${RESET}"
else
    echo -e "${RED}Lỗi: Không thể khởi chạy Backend. Xem chi tiết tại backend.log${RESET}"
    exit 1
fi

# Chạy Frontend dev server
echo -e "${YELLOW}[2/3] Đang khởi chạy Frontend React (Vite)...${RESET}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 2

# Kiểm tra xem Frontend có chạy tốt không
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}Frontend đã khởi chạy thành công (PID: $FRONTEND_PID) trên port 5173!${RESET}"
else
    echo -e "${RED}Lỗi: Không thể khởi chạy Frontend. Xem chi tiết tại frontend.log${RESET}"
    kill $BACKEND_PID
    exit 1
fi

echo -e "${BLUE}================================================================${RESET}"
echo -e "${GREEN}Hệ thống đã sẵn sàng phục vụ!${RESET}"
echo -e "👉 Vui lòng mở trình duyệt truy cập: ${YELLOW}http://localhost:5173${RESET}"
echo -e "👉 Để xem logs Backend chạy: ${BLUE}tail -f backend.log${RESET}"
echo -e "👉 Nhấn ${RED}Ctrl + C${RESET} trong terminal này để dừng toàn bộ dịch vụ."
echo -e "${BLUE}================================================================${RESET}"

# Bẫy tín hiệu Ctrl+C để dọn dẹp các tiến trình chạy ngầm khi người dùng dừng
cleanup() {
    echo -e "\n${YELLOW}Đang dừng toàn bộ các dịch vụ Backend và Frontend...${RESET}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Đã tắt các tiến trình an toàn. Hẹn gặp lại!${RESET}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Duy trì terminal để xem logs hoặc chờ tắt
while true; do
    sleep 1
done
