from mcp.server import fastmcp
from crm_client import CRMClient
import os
import json

# Design Intent (Ý đồ thiết kế):
# Stateless MCP Server đóng vai trò là "cánh tay thực thi" của AI Agent,
# cung cấp các tools được định nghĩa rõ ràng về chức năng và kiểu dữ liệu.
# MCP Server không lưu trữ bất kỳ trạng thái hội thoại nào của người dùng.
# Nó nhận cấu hình OFFLINE_MODE từ biến môi trường để truyền vào CRMClient,
# giúp hệ thống tự động chuyển mạch sang dữ liệu mock cục bộ khi cần thiết.
#
# Nguyên tắc "Define errors out of existence" (Ousterhout):
# Thay vì ném ra các exceptions (lỗi) phức tạp khi không tìm thấy khách hàng hoặc
# khi API lỗi mạng, các tools sẽ trả về thông điệp hướng dẫn rõ ràng dạng chuỗi hoặc JSON rỗng.
# Điều này giúp Agent xử lý luồng bình thường một cách mượt mà và thân thiện,
# không bị crash hệ thống.

# Khởi tạo FastMCP Server
mcp = fastmcp.FastMCP("BankA-CRM")

# Kiểm tra xem cấu hình chạy OFFLINE có được bật không
OFFLINE_MODE = os.environ.get("OFFLINE_MODE", "true").lower() == "true"
CRM_BASE_URL = os.environ.get("CRM_BASE_URL", "https://sandbox.crm.banka.vn")

# Khởi tạo CRM Client sử dụng cấu hình môi trường
crm_client = CRMClient(base_url=CRM_BASE_URL, offline_mode=OFFLINE_MODE)

@mcp.tool()
def get_customer_profile(client_id: str) -> str:
    """Tra cứu và lấy thông tin chi tiết hồ sơ của khách hàng theo mã ID hoặc theo Tên.
    
    Args:
        client_id: Mã định danh của khách hàng (ví dụ: 'KH001') hoặc Họ tên khách hàng cần tìm.
    """
    profile = crm_client.get_client_profile(client_id)
    if not profile:
        return f"Không tìm thấy khách hàng nào khớp với thông tin '{client_id}'. Vui lòng kiểm tra lại."
    return json.dumps(profile, ensure_ascii=False)

@mcp.tool()
def get_interaction_history(client_id: str) -> str:
    """Lấy danh sách lịch sử tương tác (các cuộc gọi, email, gặp mặt) của khách hàng.
    
    Args:
        client_id: Mã định danh khách hàng (ví dụ: 'KH001') hoặc Họ tên khách hàng.
    """
    history = crm_client.get_interaction_history(client_id)
    if not history:
        return f"Không tìm thấy lịch sử tương tác nào của khách hàng '{client_id}'."
    return json.dumps(history, ensure_ascii=False)

@mcp.tool()
def create_interaction(client_id: str, interaction_type: str, content: str, created_by: str = "RM System") -> str:
    """Tạo một bản ghi tương tác mới vào CRM để lưu vết giao tiếp với khách hàng (ví dụ sau khi gửi Email hoặc SMS).
    
    Args:
        client_id: Mã định danh khách hàng (ví dụ: 'KH001').
        interaction_type: Loại tương tác, ví dụ: 'Call', 'Email', 'Meeting', 'SMS'.
        content: Chi tiết nội dung cuộc hội thoại hoặc tóm tắt email/SMS đã gửi.
        created_by: Tên RM thực hiện tác vụ (ví dụ: 'RM Nguyễn Văn Đạt').
    """
    result = crm_client.create_interaction(
        client_id=client_id,
        interaction_type=interaction_type,
        content=content,
        created_by=created_by
    )
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
def get_opportunities(client_id: str) -> str:
    """Lấy danh sách tất cả các cơ hội bán hàng (gói vay, thẻ tín dụng, bảo hiểm) hiện có của khách hàng.
    
    Args:
        client_id: Mã định danh khách hàng (ví dụ: 'KH001') hoặc Họ tên khách hàng.
    """
    opps = crm_client.get_opportunities(client_id)
    if not opps:
        return f"Không tìm thấy cơ hội bán hàng nào cho khách hàng '{client_id}'."
    return json.dumps(opps, ensure_ascii=False)

@mcp.tool()
def update_opportunity_status(opportunity_id: str, stage: str) -> str:
    """Cập nhật tiến trình/trạng thái của một cơ hội bán hàng.
    
    Args:
        opportunity_id: Mã định danh cơ hội bán hàng (ví dụ: 'OPP0001').
        stage: Trạng thái mới cần chuyển đổi, bao gồm: 'New', 'Contacted', 'Proposal', 'Won', 'Lost'.
    """
    valid_stages = ["New", "Contacted", "Proposal", "Won", "Lost"]
    if stage not in valid_stages:
        return f"Trạng thái '{stage}' không hợp lệ. Vui lòng chọn một trong các trạng thái: {', '.join(valid_stages)}."
        
    result = crm_client.update_opportunity_status(opportunity_id, stage)
    if not result:
        return f"Không tìm thấy cơ hội bán hàng nào có mã '{opportunity_id}' để cập nhật."
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
def get_comprehensive_customer_data(client_id: str) -> str:
    """Tra cứu toàn bộ thông tin tổng hợp của một khách hàng bao gồm hồ sơ cá nhân, các cơ hội bán hàng hiện có, và lịch sử tương tác gần đây.
    
    RM nên ưu tiên gọi duy nhất công cụ này thay vì gọi riêng lẻ nhiều công cụ để lấy toàn bộ bức tranh về khách hàng một cách nhanh nhất, giúp giảm số lần gọi API và tiết kiệm hạn ngạch.
    
    Args:
        client_id: Mã định danh của khách hàng (ví dụ: 'KH001') hoặc Họ tên khách hàng cần tìm.
    """
    profile = crm_client.get_client_profile(client_id)
    if not profile:
        return f"Không tìm thấy khách hàng nào khớp với thông tin '{client_id}'. Vui lòng kiểm tra lại."
        
    actual_id = profile["client_id"]
    opps = crm_client.get_opportunities(actual_id)
    history = crm_client.get_interaction_history(actual_id)
    
    dashboard = {
        "profile": profile,
        "opportunities": opps,
        "interactions": history
    }
    return json.dumps(dashboard, ensure_ascii=False)

@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Tra cứu sản phẩm ngân hàng (lãi suất, mô tả gói vay/thẻ) và các mẫu template email tư vấn.
    
    Args:
        query: Từ khóa tìm kiếm liên quan đến sản phẩm (ví dụ: 'vay mua nhà', 'tiết kiệm', 'VIP').
    """
    result = crm_client.search_knowledge_base(query)
    return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()
