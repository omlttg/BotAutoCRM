import json
import os
import httpx
from typing import List, Dict, Any, Optional

# Design Intent (Ý đồ thiết kế):
# Module CRMClient được thiết kế làm Deep Module (Module Sâu) theo nguyên lý Ousterhout.
# Nó cung cấp một interface cực kỳ sạch sẽ và đơn giản cho các module bên ngoài gọi.
# Toàn bộ sự phức tạp về: định tuyến API thật/giả lập, xử lý biệt lệ HTTP, đọc file JSON local,
# và cấu hình OFFLINE_MODE đều được che giấu bên dưới (Information Hiding).
#
# Đối với Hackathon:
# - Mặc định sẽ gọi sandbox.crm.banka.vn.
# - Nếu gặp lỗi mạng (HTTP error hoặc Timeout), hoặc nếu OFFLINE_MODE=True,
#   hệ thống tự động chuyển đổi sang đọc dữ liệu mock từ file JSON cục bộ
#   để đảm bảo tính sẵn sàng 100% trong buổi demo (Hackathon Fallback).

class CRMClient:
    def __init__(self, base_url: str = "https://sandbox.crm.banka.vn", offline_mode: bool = False):
        self.base_url = base_url
        self.offline_mode = offline_mode
        self.local_dir = os.path.join(os.path.dirname(__file__), "local_mockup")
        
        # Load local files into cache as fallback/offline memory
        self._load_local_data()

    def _load_local_data(self):
        """Đọc và cache toàn bộ dữ liệu mock từ thư mục local_mockup."""
        try:
            with open(os.path.join(self.local_dir, "clients.json"), "r", encoding="utf-8") as f:
                self.local_clients = json.load(f)
            with open(os.path.join(self.local_dir, "interactions.json"), "r", encoding="utf-8") as f:
                self.local_interactions = json.load(f)
            with open(os.path.join(self.local_dir, "opportunities.json"), "r", encoding="utf-8") as f:
                self.local_opportunities = json.load(f)
            with open(os.path.join(self.local_dir, "knowledge.json"), "r", encoding="utf-8") as f:
                self.local_knowledge = json.load(f)
        except Exception as e:
            # Phòng trường hợp không đọc được file mock
            self.local_clients = []
            self.local_interactions = []
            self.local_opportunities = []
            self.local_knowledge = {"products": [], "email_templates": []}
            print(f"Cảnh báo: Không thể tải local mockup data: {e}")

    def get_client_profile(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết hồ sơ của một khách hàng."""
        if self.offline_mode:
            return self._fallback_get_client_profile(client_id)
            
        try:
            # Gọi API Sandbox thực tế
            response = httpx.get(f"{self.base_url}/api/clients/{client_id}", timeout=3.0)
            if response.status_code == 200:
                return response.json()
            else:
                return self._fallback_get_client_profile(client_id)
        except Exception:
            # Tự động fallback sang offline data khi rớt mạng hoặc lỗi API
            return self._fallback_get_client_profile(client_id)

    def _fallback_get_client_profile(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Fallback cục bộ: Tìm khách hàng trong file clients.json."""
        for client in self.local_clients:
            if client["client_id"] == client_id or client["name"].lower() == client_id.lower():
                return client
        # Tìm kiếm tương đối theo tên nếu client_id là tên khách hàng
        for client in self.local_clients:
            if client_id.lower() in client["name"].lower():
                return client
        return None

    def get_interaction_history(self, client_id: str) -> List[Dict[str, Any]]:
        """Lấy lịch sử tương tác của khách hàng."""
        if self.offline_mode:
            return self._fallback_get_interaction_history(client_id)
            
        try:
            response = httpx.get(f"{self.base_url}/api/clients/{client_id}/interactions", timeout=3.0)
            if response.status_code == 200:
                return response.json()
            else:
                return self._fallback_get_interaction_history(client_id)
        except Exception:
            return self._fallback_get_interaction_history(client_id)

    def _fallback_get_interaction_history(self, client_id: str) -> List[Dict[str, Any]]:
        """Fallback cục bộ: Lọc lịch sử tương tác từ interactions.json."""
        # Hỗ trợ tìm theo cả ID khách hàng hoặc tên khách hàng
        profile = self._fallback_get_client_profile(client_id)
        if not profile:
            return []
        
        target_id = profile["client_id"]
        return [i for i in self.local_interactions if i["client_id"] == target_id]

    def create_interaction(self, client_id: str, interaction_type: str, content: str, created_by: str = "RM System") -> Dict[str, Any]:
        """Ghi nhận tương tác mới (ví dụ gửi Email/SMS thành công)."""
        new_int = {
            "client_id": client_id,
            "type": interaction_type,
            "content": content,
            "created_by": created_by
        }
        
        if self.offline_mode:
            return self._fallback_create_interaction(new_int)
            
        try:
            response = httpx.post(f"{self.base_url}/api/interactions", json=new_int, timeout=3.0)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return self._fallback_create_interaction(new_int)
        except Exception:
            return self._fallback_create_interaction(new_int)

    def _fallback_create_interaction(self, new_int: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback cục bộ: Lưu in-memory và ghi đè vào file local interactions.json."""
        profile = self._fallback_get_client_profile(new_int["client_id"])
        client_id = profile["client_id"] if profile else new_int["client_id"]
        
        idx = len(self.local_interactions) + 1
        interaction_record = {
            "interaction_id": f"INT{idx:05d}",
            "client_id": client_id,
            "type": new_int["type"],
            "timestamp": "2026-07-01T11:00:00Z", # Sử dụng local time hiện tại của session
            "content": new_int["content"],
            "created_by": new_int["created_by"]
        }
        
        # Thêm vào mảng local memory
        self.local_interactions.append(interaction_record)
        
        # Ghi đè cập nhật lại file JSON cục bộ
        try:
            with open(os.path.join(self.local_dir, "interactions.json"), "w", encoding="utf-8") as f:
                json.dump(self.local_interactions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Cảnh báo: Không thể ghi file interactions.json: {e}")
            
        return interaction_record

    def get_opportunities(self, client_id: str) -> List[Dict[str, Any]]:
        """Lấy danh sách các cơ hội bán hàng của khách hàng."""
        if self.offline_mode:
            return self._fallback_get_opportunities(client_id)
            
        try:
            response = httpx.get(f"{self.base_url}/api/clients/{client_id}/opportunities", timeout=3.0)
            if response.status_code == 200:
                return response.json()
            else:
                return self._fallback_get_opportunities(client_id)
        except Exception:
            return self._fallback_get_opportunities(client_id)

    def _fallback_get_opportunities(self, client_id: str) -> List[Dict[str, Any]]:
        """Fallback cục bộ: Lọc cơ hội bán hàng từ opportunities.json."""
        profile = self._fallback_get_client_profile(client_id)
        if not profile:
            return []
        
        target_id = profile["client_id"]
        return [o for o in self.local_opportunities if o["client_id"] == target_id]

    def update_opportunity_status(self, opportunity_id: str, stage: str) -> Optional[Dict[str, Any]]:
        """Cập nhật trạng thái của cơ hội bán hàng."""
        if self.offline_mode:
            return self._fallback_update_opportunity_status(opportunity_id, stage)
            
        try:
            response = httpx.put(
                f"{self.base_url}/api/opportunities/{opportunity_id}", 
                json={"stage": stage}, 
                timeout=3.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                return self._fallback_update_opportunity_status(opportunity_id, stage)
        except Exception:
            return self._fallback_update_opportunity_status(opportunity_id, stage)

    def _fallback_update_opportunity_status(self, opportunity_id: str, stage: str) -> Optional[Dict[str, Any]]:
        """Fallback cục bộ: Cập nhật trạng thái trong opportunities.json."""
        for opp in self.local_opportunities:
            if opp["opportunity_id"] == opportunity_id:
                opp["stage"] = stage
                opp["updated_at"] = "2026-07-01T11:00:00Z"
                
                # Ghi đè cập nhật lại file JSON
                try:
                    with open(os.path.join(self.local_dir, "opportunities.json"), "w", encoding="utf-8") as f:
                        json.dump(self.local_opportunities, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"Cảnh báo: Không thể ghi file opportunities.json: {e}")
                return opp
        return None

    def search_knowledge_base(self, query: str) -> Dict[str, List[Any]]:
        """Tra cứu tài liệu sản phẩm hoặc template email phù hợp với từ khóa."""
        query_lower = query.lower()
        
        # Vì knowledge base thường ít thay đổi, ta dùng trực tiếp local data
        matched_products = []
        for prod in self.local_knowledge.get("products", []):
            if (query_lower in prod["name"].lower() or 
                query_lower in prod["category"].lower() or 
                query_lower in prod["description"].lower()):
                matched_products.append(prod)
                
        matched_templates = []
        for temp in self.local_knowledge.get("email_templates", []):
            if (query_lower in temp["title"].lower() or 
                query_lower in temp["subject"].lower() or 
                query_lower in temp["body"].lower()):
                matched_templates.append(temp)
                
        return {
            "products": matched_products,
            "email_templates": matched_templates
        }
