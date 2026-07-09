import json
import random
import os

# Danh sách họ, đệm, tên tiếng Việt để sinh tên ngẫu nhiên
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô"]
DEM = ["Văn", "Thị", "Hữu", "Đức", "Minh", "Quang", "Anh", "Hoàng", "Tuấn", "Thành", "Khánh", "Ngọc", "Thu", "Hồng"]
TEN = ["Anh", "Bình", "Cường", "Dũng", "Em", "Phương", "Giang", "Hương", "Hùng", "Hải", "Lan", "Nam", "Phong", "Sơn", "Trang", "Tuấn", "Vy", "Yến"]

PRODUCT_TYPES = ["Tiết kiệm tích lũy", "Vay mua nhà", "Vay mua ô tô", "Thẻ tín dụng VIP", "Bảo hiểm liên kết đầu tư", "Trái phiếu doanh nghiệp"]
STAGES = ["New", "Contacted", "Proposal", "Won", "Lost"]
INTERACTION_TYPES = ["Call", "Email", "Meeting", "SMS"]

# Template nội dung tương tác mô phỏng
INTERACTION_CONTENTS = [
    "Khách hàng hỏi về thủ tục tất toán trước hạn gói vay mua nhà. Đã hướng dẫn chi tiết quy trình.",
    "RM gọi điện giới thiệu chương trình ưu đãi lãi suất vay tiêu dùng tháng 6. Khách hàng hẹn liên hệ lại sau.",
    "Gặp mặt trực tiếp tại chi nhánh tư vấn gói bảo hiểm liên kết đầu tư. Khách hàng quan tâm và yêu cầu gửi bảng minh họa dòng tiền.",
    "SMS thông báo tài khoản thấu chi được phê duyệt hạn mức mới. Khách hàng phản hồi xác nhận.",
    "Khách hàng phàn nàn về việc phí thường niên thẻ tín dụng tăng. Đã ghi nhận ý kiến và chuyển bộ phận hỗ trợ khách hàng.",
    "RM tư vấn chuyển đổi tiền gửi tiết kiệm sang chứng chỉ tiền gửi lãi suất cao hơn. Khách hàng đã đồng ý thực hiện.",
    "Email gửi tài liệu sản phẩm vay mua ô tô kèm bảng tính gốc lãi hàng tháng.",
    "Khách hàng yêu cầu cập nhật lại thông tin địa chỉ thường trú trên hệ thống. Đã xử lý."
]

def generate_vietnamese_name():
    return f"{random.choice(HO)} {random.choice(DEM)} {random.choice(TEN)}"

def generate_data():
    os.makedirs("backend/local_mockup", exist_ok=True)
    
    # 1. Sinh 500 khách hàng (clients.json)
    clients = []
    for i in range(1, 501):
        client_id = f"KH{i:03d}"
        segment = random.choices(["VIP", "Gold", "Standard"], weights=[15, 35, 50])[0]
        balance = round(random.uniform(5000000, 5000000000) if segment == "VIP" else random.uniform(100000, 100000000), 2)
        rm_name = f"RM Nguyễn Văn {random.choice(['Tú', 'Đạt', 'Hùng', 'Linh'])}"
        
        clients.append({
            "client_id": client_id,
            "name": generate_vietnamese_name(),
            "segment": segment,
            "phone": f"09{random.randint(10000000, 99999999)}",
            "email": f"{client_id.lower()}@banka.vn",
            "account_balance": balance,
            "assigned_rm": rm_name
        })
        
    with open("backend/local_mockup/clients.json", "w", encoding="utf-8") as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)
    print("Đã tạo clients.json với 500 khách hàng.")

    # 2. Sinh ~1.000 lịch sử tương tác (interactions.json)
    interactions = []
    idx = 1
    # Đảm bảo mỗi khách hàng có ít nhất 1 tương tác, VIP có nhiều hơn
    for client in clients:
        num_interactions = random.randint(3, 8) if client["segment"] == "VIP" else random.randint(1, 3)
        for _ in range(num_interactions):
            interactions.append({
                "interaction_id": f"INT{idx:05d}",
                "client_id": client["client_id"],
                "type": random.choice(INTERACTION_TYPES),
                "timestamp": f"2026-06-{random.randint(1, 30):02d}T{random.randint(8, 17):02d}:{random.randint(10, 59):02d}:00Z",
                "content": random.choice(INTERACTION_CONTENTS),
                "created_by": client["assigned_rm"]
            })
            idx += 1
            
    with open("backend/local_mockup/interactions.json", "w", encoding="utf-8") as f:
        json.dump(interactions, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo interactions.json với {len(interactions)} bản ghi tương tác.")

    # 3. Sinh ~300 cơ hội bán hàng (opportunities.json)
    opportunities = []
    opp_idx = 1
    # 60% khách hàng có cơ hội bán hàng
    for client in clients:
        if random.random() < 0.6:
            num_opps = random.randint(1, 2)
            for _ in range(num_opps):
                opportunities.append({
                    "opportunity_id": f"OPP{opp_idx:04d}",
                    "client_id": client["client_id"],
                    "product_type": random.choice(PRODUCT_TYPES),
                    "stage": random.choice(STAGES),
                    "expected_value": round(random.uniform(50000000, 2000000000), 2),
                    "updated_at": f"2026-06-{random.randint(10, 30):02d}T10:00:00Z"
                })
                opp_idx += 1
                
    with open("backend/local_mockup/opportunities.json", "w", encoding="utf-8") as f:
        json.dump(opportunities, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo opportunities.json với {len(opportunities)} cơ hội bán hàng.")

    # 4. Sinh tài nguyên sản phẩm & template (knowledge.json)
    knowledge = {
        "products": [
            {
                "product_id": "PROD001",
                "name": "Tiết kiệm Đại Phát",
                "category": "Tiết kiệm",
                "rate": "6.2% / năm kì hạn 12 tháng",
                "description": "Lãi suất ưu việt dành cho kỳ hạn dài hạn, nhận lãi cuối kỳ."
            },
            {
                "product_id": "PROD002",
                "name": "Vay Mua Nhà An Gia",
                "category": "Tín dụng",
                "rate": "5.9% / năm cố định 2 năm đầu",
                "description": "Hỗ trợ hạn mức vay lên tới 80% giá trị tài sản bảo đảm, thời gian vay tối đa 35 năm."
            },
            {
                "product_id": "PROD003",
                "name": "Vay Mua Ô Tô AutoLoan",
                "category": "Tín dụng",
                "rate": "6.5% / năm cố định 1 năm đầu",
                "description": "Hạn mức vay lên tới 85% giá trị xe, giải ngân siêu tốc trong vòng 4 giờ làm việc."
            },
            {
                "product_id": "PROD004",
                "name": "Thẻ tín dụng VIP Platinum",
                "category": "Thẻ",
                "rate": "Hoàn tiền 10% chi tiêu ẩm thực, du lịch",
                "description": "Miễn phí thường niên năm đầu, tích điểm dặm bay Vietnam Airlines, bảo hiểm du lịch toàn cầu."
            },
            {
                "product_id": "PROD005",
                "name": "Bảo hiểm Phú Bảo An Gia",
                "category": "Bảo hiểm liên kết",
                "rate": "Bảo vệ lên đến 150% số tiền bảo hiểm",
                "description": "Sản phẩm bảo hiểm kết hợp đầu tư tài chính an toàn, bảo vệ toàn diện trước rủi ro."
            }
        ],
        "email_templates": [
            {
                "template_id": "TEMP001",
                "title": "Email giới thiệu gói vay mua nhà An Gia",
                "subject": "Giải pháp tài chính vượt trội cho tổ ấm của bạn - Ngân hàng TMCP A",
                "body": "Kính gửi anh/chị {client_name},\n\nTôi là {rm_name}, Relationship Manager tại Ngân hàng TMCP A.\n\nTôi xin gửi tới anh/chị thông tin về gói Vay Mua Nhà An Gia đang được áp dụng với mức lãi suất vô cùng ưu đãi chỉ {product_rate}. \n\nVới gói vay này, anh/chị sẽ được hỗ trợ vay lên đến 80% giá trị căn hộ và thời hạn vay linh hoạt đến 35 năm giúp giảm bớt áp lực tài chính hàng tháng.\n\nAnh/chị vui lòng liên hệ lại với tôi qua số điện thoại này hoặc phản hồi email để được hỗ trợ làm hồ sơ nhanh chóng.\n\nTrân trọng,\n{rm_name}\nNgân hàng TMCP A"
            },
            {
                "template_id": "TEMP002",
                "title": "Email tri ân khách hàng VIP tiết kiệm tích lũy",
                "subject": "Chương trình tri ân đặc quyền dành riêng cho khách hàng VIP - Ngân hàng TMCP A",
                "body": "Kính gửi anh/chị {client_name},\n\nLời đầu tiên, Ngân hàng TMCP A xin gửi lời cảm ơn chân thành tới anh/chị vì đã tin tưởng sử dụng dịch vụ của chúng tôi trong thời gian qua.\n\nLà một khách hàng phân khúc VIP, Ngân hàng xin gửi tới anh/chị chương trình Tiết kiệm tích lũy Đại Phát với mức lãi suất độc quyền lên tới {product_rate} dành riêng cho tài khoản của anh/chị.\n\nHy vọng gói giải pháp tài chính này sẽ giúp gia tăng tài sản tích lũy của anh/chị một cách an toàn và bền vững nhất.\n\nTrân trọng,\n{rm_name}\nNgân hàng TMCP A"
            }
        ]
    }
    
    with open("backend/local_mockup/knowledge.json", "w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    print("Đã tạo knowledge.json chứa sản phẩm và templates email.")

if __name__ == "__main__":
    generate_data()
