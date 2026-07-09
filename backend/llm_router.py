import os
import json
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from openai import OpenAI
from anthropic import Anthropic
from google.antigravity import Agent, LocalAgentConfig, types

# Design Rationale (Giải thích thiết kế):
# LLMRouter là một Deep Module đóng vai trò là "bộ não định tuyến" (LLM Router).
# Nó tích hợp:
# 1. Google Antigravity SDK làm runtime thực thi mặc định (Gemini) để tự động nạp
#    Stateless MCP Server cục bộ qua stdio transport và tận dụng cơ chế lưu trữ
#    trạng thái hội thoại phía máy chủ (Server-side State) qua conversation_id.
# 2. Các SDK OpenAI và Anthropic làm phương án dự phòng (fallback) độc lập hoàn toàn.
# 3. HTTP Client gọi Local Ollama cho kịch bản offline hoàn toàn.
#
# Khi có lỗi từ Gemini (ví dụ: HTTP Error 429, API Key lỗi, cạn quota), hệ thống sẽ
# bắt ngoại lệ và tự động chuyển mạch (fallback) sang OpenAI/Anthropic/Ollama.
# Để giữ ngữ cảnh khi fallback, Backend sẽ tự đóng gói toàn bộ lịch sử tin nhắn
# tích lũy cục bộ và gửi đi dưới dạng stateless chat history array.

class LLMRouter:
    def __init__(self):
        self.sessions_gemini: Dict[str, str] = {}  # session_id -> conversation_id
        self.sessions_history: Dict[str, List[Dict[str, str]]] = {}  # session_id -> chat history list
        
        # Cấu hình lưu trữ trạng thái Antigravity Agent
        self.save_dir = os.path.join(os.path.dirname(__file__), "sessions")
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Đọc các API Keys từ môi trường
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
        
        # Khởi tạo các client SDK dự phòng
        self.openai_client = OpenAI(api_key=self.openai_key) if self.openai_key else None
        self.anthropic_client = Anthropic(api_key=self.anthropic_key) if self.anthropic_key else None
        
        # Định nghĩa system instruction hướng dẫn Agent chủ động (proactive)
        self.system_instruction = (
            "Bạn là Co-Pilot CRM thông minh, chủ động của Ngân hàng TMCP A. Nhiệm vụ của bạn là hỗ trợ RM (Relationship Manager).\n"
            "QUY TẮC CỐT LÕI:\n"
            "1. Hỗ trợ tiếng Việt tự nhiên, hiểu các thuật ngữ viết tắt trong ngân hàng: KH (Khách hàng), ĐNCV (Đề nghị cho vay), RM (Relationship Manager), CBNV (Cán bộ nhân viên).\n"
            "2. CHỐNG ẢO TƯỞNG SỐ LIỆU (No Hallucination): Tuyệt đối không tự bịa ra số liệu thống kê (như số dư tài khoản, số lượng khách hàng, cơ hội bán hàng) khi chưa gọi tool MCP. Chỉ đưa ra các số liệu chính xác lấy được từ công cụ.\n"
            "3. TỐI ƯU HÓA GỌI CÔNG CỤ (MCP Calls Optimization): Để tiết kiệm hạn ngạch API và tăng tốc độ xử lý, khi RM yêu cầu thông tin về một khách hàng (như hồ sơ, cơ hội, tương tác), hãy ưu tiên gọi duy nhất công cụ hợp nhất `get_comprehensive_customer_data` thay vì gọi riêng lẻ nhiều công cụ.\n"
            "4. HÀNH VI CHỦ ĐỘNG (Proactive): Khi RM xem Profile khách hàng hoặc Cơ hội bán hàng, hãy tự động đối soát thông tin và đề xuất các hành động tiếp theo phù hợp (ví dụ: tư vấn gói sản phẩm, gửi email tri ân, cập nhật tiến độ cơ hội).\n"
            "5. ĐỊNH DẠNG Generative UI: Khi trả về thông tin khách hàng, cơ hội bán hàng, email nháp hoặc lịch sử tương tác, hãy định dạng kết quả dưới dạng JSON có cấu trúc nằm trong khối ```json để Frontend có thể tự động bắt và render thành các card tương tác đẹp mắt."
        )

    def _get_history(self, session_id: str) -> List[Dict[str, str]]:
        if session_id not in self.sessions_history:
            self.sessions_history[session_id] = []
        return self.sessions_history[session_id]

    def _add_to_history(self, session_id: str, role: str, content: str):
        history = self._get_history(session_id)
        history.append({"role": role, "content": content})

    async def generate_response(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Định tuyến và sinh câu trả lời tự động fallback khi gặp lỗi kết nối."""
        # Lưu câu hỏi của RM vào lịch sử local
        self._add_to_history(session_id, "user", user_message)
        chat_history = self._get_history(session_id)
        
        warning_msg = None
        
        # 1. Thử nghiệm gọi Gemini mặc định thông qua Antigravity SDK
        if self.gemini_key and self.gemini_key != "dummy":
            try:
                # Cấu hình Antigravity Agent
                conversation_id = self.sessions_gemini.get(session_id)
                
                # Định nghĩa MCP server cục bộ chạy stdio
                mcp_servers = [
                    types.McpStdioServer(
                        name="BankA-CRM",
                        command="python3",
                        args=[os.path.join(os.path.dirname(__file__), "mcp_server.py")],
                    )
                ]
                
                # Khởi tạo LocalAgentConfig
                config = LocalAgentConfig(
                    model="gemini-3.5-flash",
                    mcp_servers=mcp_servers,
                    system_instructions=self.system_instruction,
                    save_dir=self.save_dir,
                    conversation_id=conversation_id
                )
                
                async with Agent(config) as agent:
                    # Gửi tin nhắn qua Antigravity chat
                    response = await agent.chat(user_message)
                    response_text = await response.text()
                    
                    # Cập nhật conversation_id để duy trì context
                    self.sessions_gemini[session_id] = agent.conversation_id
                    
                    # Lưu câu trả lời vào lịch sử local
                    self._add_to_history(session_id, "model", response_text)
                    
                    return {
                        "response": response_text,
                        "model": "Gemini 3.5 Flash",
                        "error": None
                    }
            except Exception as e:
                # Trích xuất thông điệp lỗi quota 429 một cách rõ ràng và ngắn gọn hơn
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower():
                    warning_msg = "Gemini API Quota Exceeded (HTTP 429). Đã hết hạn mức yêu cầu miễn phí."
                else:
                    warning_msg = f"Gemini API Error: {err_str[:80]}..."
                print(f"Cảnh báo: Lỗi kết nối Gemini, đang tự động fallback sang OpenAI/Anthropic/Ollama: {e}")
                
        # 2. Fallback 1: Gọi OpenAI API (GPT-4o-mini)
        if self.openai_key:
            try:
                # Chuyển đổi mảng chat_history sang cấu trúc OpenAI
                messages = [{"role": "system", "content": self.system_instruction}]
                for msg in chat_history:
                    # Map role 'model' sang 'assistant'
                    role = "assistant" if msg["role"] == "model" else msg["role"]
                    messages.append({"role": role, "content": msg["content"]})
                    
                # Gọi trực tiếp qua OpenAI Client
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.2
                )
                response_text = response.choices[0].message.content
                
                self._add_to_history(session_id, "model", response_text)
                return {
                    "response": response_text,
                    "model": "GPT-4o-mini (Fallback Mode)",
                    "error": None,
                    "warning": warning_msg
                }
            except Exception as e:
                print(f"Cảnh báo: Lỗi kết nối OpenAI fallback: {e}")

        # 3. Fallback 2: Gọi Anthropic API (Claude 3.5 Sonnet)
        if self.anthropic_key:
            try:
                messages = []
                for msg in chat_history:
                    role = "assistant" if msg["role"] == "model" else msg["role"]
                    messages.append({"role": role, "content": msg["content"]})
                    
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    system=self.system_instruction,
                    messages=messages,
                    max_tokens=1000
                )
                response_text = response.content[0].text
                
                self._add_to_history(session_id, "model", response_text)
                return {
                    "response": response_text,
                    "model": "Claude 3.5 Sonnet (Fallback Mode)",
                    "error": None,
                    "warning": warning_msg
                }
            except Exception as e:
                print(f"Cảnh báo: Lỗi kết nối Anthropic fallback: {e}")

        # 4. Fallback 3: Gọi Local Ollama (Chạy offline hoàn toàn)
        try:
            messages = [{"role": "system", "content": self.system_instruction}]
            for msg in chat_history:
                role = "assistant" if msg["role"] == "model" else msg["role"]
                messages.append({"role": role, "content": msg["content"]})
                
            async with httpx.AsyncClient() as client:
                # Gọi API Ollama local
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": "llama3",
                        "messages": messages,
                        "stream": False
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    response_text = data["message"]["content"]
                    
                    self._add_to_history(session_id, "model", response_text)
                    return {
                        "response": response_text,
                        "model": "Local Ollama Llama3 (Offline Mode)",
                        "error": None,
                        "warning": warning_msg
                    }
        except Exception as e:
            print(f"Cảnh báo: Lỗi kết nối Ollama local: {e}")

        # 5. Fallback 4: Triển khai Mock LLM Engine thông minh (Offline Demo Mode)
        # Giúp RM có thể chat demo mượt mà 100% mà không cần kết nối mạng hoặc cung cấp API key!
        try:
            from crm_client import CRMClient
            crm = CRMClient(offline_mode=True)
            user_msg_lower = user_message.lower()
            
            # Mặc định tìm kiếm client_id xuất hiện trong tin nhắn (ví dụ: KH001, KH002, ...)
            client_id = "KH001"
            import re
            match = re.search(r'kh\d{3}', user_msg_lower)
            if match:
                client_id = match.group(0).upper()
                
            # A. Kịch bản 1: Yêu cầu xem hồ sơ khách hàng
            if any(k in user_msg_lower for k in ["hồ sơ", "thông tin", "khách hàng", "tìm kiếm", "profile"]):
                # Thử tìm kiếm theo tên nếu không khớp mã KH
                name_query = user_message
                for k in ["hồ sơ", "thông tin", "khách hàng", "tìm kiếm", "profile", "của", "bản ghi", "cho"]:
                    name_query = name_query.replace(k, "")
                name_query = name_query.strip()
                
                profile = crm.get_client_profile(client_id)
                if name_query and len(name_query) > 2:
                    potential_profile = crm.get_client_profile(name_query)
                    if potential_profile:
                        profile = potential_profile
                
                if profile:
                    response_text = (
                        f"Dạ, tôi đã tìm thấy thông tin chi tiết của khách hàng **{profile['name']}** trên hệ thống CRM.\n"
                        f"Dưới đây là thẻ hồ sơ khách hàng được cập nhật thời gian thực:\n\n"
                        f"```json\n{json.dumps(profile, ensure_ascii=False, indent=2)}\n```\n\n"
                        f"RM có muốn tôi hiển thị thêm **cơ hội bán hàng** hoặc **lịch sử tương tác** của khách hàng này không?"
                    )
                else:
                    response_text = f"Xin lỗi, tôi không tìm thấy khách hàng nào có mã hoặc tên là '{name_query}' trong hệ thống."

            # B. Kịch bản 2: Yêu cầu xem cơ hội bán hàng
            elif any(k in user_msg_lower for k in ["cơ hội", "bán hàng", "opportunity", "gói vay", "sản phẩm vay"]):
                opps = crm.get_opportunities(client_id)
                profile = crm.get_client_profile(client_id)
                response_text = (
                    f"Dạ, đây là danh sách các cơ hội bán hàng hiện tại của khách hàng **{profile['name'] if profile else client_id}**:\n\n"
                    f"```json\n{json.dumps(opps, ensure_ascii=False, indent=2)}\n```\n\n"
                    f"Bạn có thể cập nhật nhanh trạng thái của các cơ hội này trực tiếp trên card bằng cách bấm vào các nút chuyển đổi trạng thái."
                )

            # C. Kịch bản 3: Yêu cầu xem lịch sử tương tác
            elif any(k in user_msg_lower for k in ["tương tác", "lịch sử", "giao tiếp", "timeline"]):
                history = crm.get_interaction_history(client_id)
                profile = crm.get_client_profile(client_id)
                response_text = (
                    f"Dạ, tôi xin gửi dòng thời gian lịch sử tương tác gần nhất của khách hàng **{profile['name'] if profile else client_id}**:\n\n"
                    f"```json\n{json.dumps(history, ensure_ascii=False, indent=2)}\n```"
                )

            # D. Kịch bản 4: Yêu cầu soạn email / thư tư vấn
            elif any(k in user_msg_lower for k in ["soạn email", "viết thư", "gửi thư", "template", "mẫu email"]):
                kb = crm.search_knowledge_base("tiết kiệm" if "tiết kiệm" in user_msg_lower else "vay mua nhà")
                profile = crm.get_client_profile(client_id)
                
                template = kb["email_templates"][0] if kb["email_templates"] else None
                if template:
                    # Thay thế các placeholders trong template
                    client_name = profile["name"] if profile else "Quý khách hàng"
                    rm_name = profile["assigned_rm"] if profile else "Quan hệ khách hàng"
                    rate = "5.9%/năm" if "vay" in template["template_id"] else "6.2%/năm"
                    
                    template_filled = {
                        "template_id": template["template_id"],
                        "subject": template["subject"],
                        "body": template["body"].replace("{client_name}", client_name).replace("{rm_name}", rm_name).replace("{product_rate}", rate)
                    }
                    
                    response_text = (
                        f"Dạ, tôi đã soạn sẵn thư nháp tư vấn sản phẩm cho khách hàng **{client_name}** dựa trên mẫu của ngân hàng.\n"
                        f"Bạn có thể chỉnh sửa nội dung thư trực tiếp bên dưới và click **Gửi Email** để hệ thống tự động ghi nhận tương tác vào CRM:\n\n"
                        f"```json\n{json.dumps(template_filled, ensure_ascii=False, indent=2)}\n```"
                    )
                else:
                    response_text = "Không tìm thấy mẫu email phù hợp trong kho kiến thức."

            # E. Kịch bản 5: Yêu cầu cập nhật trạng thái cơ hội bán hàng
            elif "cập nhật cơ hội" in user_msg_lower or "cập nhật trạng thái" in user_msg_lower:
                # Trích xuất mã cơ hội
                opp_id = "OPP0001"
                import re
                opp_match = re.search(r'opp\d{4}', user_msg_lower)
                if opp_match:
                    opp_id = opp_match.group(0).upper()
                    
                target_stage = "Proposal"
                for stage in ["New", "Contacted", "Proposal", "Won", "Lost"]:
                    if stage.lower() in user_msg_lower:
                        target_stage = stage
                        break
                        
                updated_opp = crm.update_opportunity_status(opp_id, target_stage)
                if updated_opp:
                    response_text = (
                        f"Đã cập nhật trạng thái cơ hội bán hàng **{opp_id}** thành công sang **{target_stage}**.\n"
                        f"Hệ thống đã lưu vết và đồng bộ hóa dữ liệu lên máy chủ CRM ngân hàng."
                    )
                else:
                    response_text = f"Không tìm thấy cơ hội bán hàng có mã {opp_id} trên hệ thống để cập nhật."

            # F. Mặc định: Phản hồi thông tin trợ giúp thông minh
            else:
                response_text = (
                    f"Tôi là AI Co-Pilot CRM Ngân hàng TMCP A. Hệ thống hiện đang chạy ở chế độ **Offline Demo Mode** (không cần API key).\n"
                    f"Bạn có thể gõ các câu lệnh sau để tôi giả lập gọi công cụ CRM và hiển thị Generative UI:\n"
                    f"1. *'Xem hồ sơ khách hàng KH001'*\n"
                    f"2. *'Xem cơ hội bán hàng KH001'*\n"
                    f"3. *'Xem lịch sử tương tác KH001'*\n"
                    f"4. *'Soạn email cho KH001'*\n"
                    f"5. *'Cập nhật cơ hội OPP0001 sang Won'*"
                )
                
            self._add_to_history(session_id, "model", response_text)
            return {
                "response": response_text,
                "model": "Mock LLM Engine (Offline Demo Mode)",
                "error": None,
                "warning": warning_msg
            }
            
        except Exception as mock_err:
            err_msg = f"Hệ thống gặp lỗi nghiêm trọng: {mock_err}"
            self._add_to_history(session_id, "model", err_msg)
            return {
                "response": err_msg,
                "model": "System Emergency (No-LLM Mode)",
                "error": str(mock_err)
            }
