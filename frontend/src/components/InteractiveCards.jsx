import React, { useState } from "react";

// 1. Component hiển thị Hồ sơ Khách hàng VIP/Gold/Standard
export function CustomerProfileCard({ data }) {
  if (!data) return null;
  const isVIP = data.segment === "VIP";
  const isGold = data.segment === "Gold";

  return (
    <div className="glass-panel p-5 my-3 border border-slate-700 animate-fade-in-up" style={{ maxWidth: "550px" }}>
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-lg font-bold text-slate-100 m-0 flex items-center">
          👤 {data.name}
        </h3>
        <span 
          className={`px-3 py-1 text-xs font-bold rounded-full ${
            isVIP ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" : 
            isGold ? "bg-yellow-500/20 text-yellow-300 border border-yellow-500/30" : 
            "bg-blue-500/20 text-blue-300 border border-blue-500/30"
          }`}
        >
          {data.segment}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-3 text-sm text-slate-300">
        <div>
          <span className="text-slate-500 block text-xs">MÃ KHÁCH HÀNG</span>
          <span className="font-mono text-slate-200">{data.client_id}</span>
        </div>
        <div>
          <span className="text-slate-500 block text-xs">SỐ ĐIỆN THOẠI</span>
          <span className="text-slate-200">{data.phone}</span>
        </div>
        <div className="col-span-2">
          <span className="text-slate-500 block text-xs">EMAIL</span>
          <span className="text-slate-200">{data.email}</span>
        </div>
        <div>
          <span className="text-slate-500 block text-xs">SỐ DƯ TÀI KHOẢN</span>
          <span className="text-emerald-400 font-bold font-mono">
            {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(data.account_balance)}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block text-xs">CÁN BỘ QUẢN LÝ (RM)</span>
          <span className="text-sky-300">{data.assigned_rm}</span>
        </div>
      </div>
    </div>
  );
}

// 2. Component hiển thị dòng lịch sử tương tác
export function InteractionTimeline({ history }) {
  if (!history || history.length === 0) return null;

  return (
    <div className="glass-panel p-5 my-3 border border-slate-700 animate-fade-in-up" style={{ maxWidth: "550px" }}>
      <h3 className="text-sm font-bold text-slate-400 mb-4 m-0 uppercase tracking-wider">
        🕒 Lịch sử tương tác
      </h3>
      <div className="relative border-l border-slate-700 pl-4 ml-2">
        {history.map((item, idx) => (
          <div key={item.interaction_id || idx} className="mb-4 relative">
            {/* Dấu chấm mốc thời gian */}
            <span className="absolute -left-[21px] mt-1.5 w-3.5 h-3.5 rounded-full bg-sky-500 border-2 border-slate-900"></span>
            
            <div className="flex justify-between items-center text-xs text-slate-500 mb-1">
              <span className="bg-slate-800/80 px-2 py-0.5 rounded text-sky-300 border border-slate-700/50">
                {item.type}
              </span>
              <span>{item.timestamp ? new Date(item.timestamp).toLocaleString("vi-VN") : "Hôm nay"}</span>
            </div>
            <p className="text-sm text-slate-200 m-0 leading-relaxed">
              {item.content}
            </p>
            <span className="text-[10px] text-slate-500 block mt-1">RM: {item.created_by}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// 3. Component hiển thị cơ hội bán hàng và cập nhật nhanh trạng thái
export function OpportunityManager({ opportunities, onUpdateStatus }) {
  if (!opportunities || opportunities.length === 0) return null;

  const stageColors = {
    "New": "bg-blue-500/10 text-blue-400 border-blue-500/30",
    "Contacted": "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
    "Proposal": "bg-purple-500/10 text-purple-400 border-purple-500/30",
    "Won": "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    "Lost": "bg-rose-500/10 text-rose-400 border-rose-500/30",
  };

  return (
    <div className="glass-panel p-5 my-3 border border-slate-700 animate-fade-in-up" style={{ maxWidth: "550px" }}>
      <h3 className="text-sm font-bold text-slate-400 mb-3 m-0 uppercase tracking-wider">
        💼 Cơ hội bán hàng hiện tại
      </h3>
      {opportunities.map((opp) => (
        <div key={opp.opportunity_id} className="bg-slate-800/30 p-3 rounded-lg border border-slate-800 mb-3 last:mb-0">
          <div className="flex justify-between items-start mb-2">
            <div>
              <span className="text-slate-500 text-xs font-mono block">{opp.opportunity_id}</span>
              <span className="text-sm font-bold text-slate-200">{opp.product_type}</span>
            </div>
            <span className={`px-2 py-0.5 text-xs rounded border ${stageColors[opp.stage] || "bg-slate-500/10"}`}>
              {opp.stage}
            </span>
          </div>
          
          <div className="flex justify-between items-center text-xs text-slate-400 mt-2">
            <span>TRỊ GIÁ: <b className="text-emerald-400 font-mono">{new Intl.NumberFormat('vi-VN').format(opp.expected_value)} VND</b></span>
            <span>Cập nhật: {new Date(opp.updated_at).toLocaleDateString("vi-VN")}</span>
          </div>

          {/* Quick actions để đổi trạng thái */}
          <div className="mt-3 pt-3 border-t border-slate-800/60 flex gap-1.5 flex-wrap">
            <span className="text-[10px] text-slate-500 block w-full mb-1">CẬP NHẬT NHANH TRẠNG THÁI:</span>
            {["Contacted", "Proposal", "Won", "Lost"].map((targetStage) => (
              <button
                key={targetStage}
                onClick={() => onUpdateStatus(opp.opportunity_id, targetStage)}
                className={`px-2 py-1 text-[10px] rounded cursor-pointer transition-all border ${
                  opp.stage === targetStage 
                    ? "bg-slate-700 text-slate-200 border-slate-600 font-bold" 
                    : "bg-slate-900/50 hover:bg-slate-800 text-slate-400 border-slate-800"
                }`}
              >
                {targetStage}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// 4. Component soạn thảo email mẫu nháp, cho phép RM sửa và bấm gửi
export function EmailDraftEditor({ template, clientName, rmName, onSendEmail }) {
  if (!template) return null;

  const [subject, setSubject] = useState(template.subject || "");
  const [body, setBody] = useState(template.body || "");
  const [isSent, setIsSent] = useState(false);

  const handleSend = () => {
    setIsSent(true);
    onSendEmail(subject, body);
  };

  return (
    <div className="glass-panel p-5 my-3 border border-slate-700 animate-fade-in-up" style={{ maxWidth: "550px", width: "100%" }}>
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-bold text-slate-400 m-0 uppercase tracking-wider">
          ✉️ Trình soạn thảo thư nháp
        </h3>
        {isSent && (
          <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full font-bold">
            ĐÃ GỬI & LƯU LỊCH SỬ
          </span>
        )}
      </div>

      <div className="mb-3">
        <label className="text-[10px] text-slate-500 block mb-1">TIÊU ĐỀ THƯ</label>
        <input
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          disabled={isSent}
          className="w-full bg-slate-900/60 border border-slate-800 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
        />
      </div>

      <div className="mb-4">
        <label className="text-[10px] text-slate-500 block mb-1">NỘI DUNG EMAIL</label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          disabled={isSent}
          rows={8}
          className="w-full bg-slate-900/60 border border-slate-800 rounded px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-sky-500 resize-y"
        />
      </div>

      {!isSent && (
        <button
          onClick={handleSend}
          className="w-full py-2.5 px-4 rounded font-bold text-sm cursor-pointer text-white bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 shadow-lg shadow-sky-500/10 border-0"
        >
          🚀 Gửi Email & Lưu Lịch sử
        </button>
      )}
    </div>
  );
}
