import React, { useState, useEffect, useRef } from "react";
import { 
  CustomerProfileCard, 
  InteractionTimeline, 
  OpportunityManager, 
  EmailDraftEditor 
} from "./InteractiveCards";

const BACKEND_URL = "http://localhost:8001";

// Component con phụ trách các nút thao tác nhanh (Copy / Edit) trên tin nhắn
const MessageActionButton = ({ text, onEdit }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Không thể copy văn bản: ", err);
    }
  };

  return (
    <div className="absolute right-2 bottom-1.5 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-slate-900/90 py-0.5 px-2 rounded-md border border-slate-800 shadow-md select-none z-10">
      <button 
        type="button"
        onClick={handleCopy}
        className="text-[10px] text-slate-400 hover:text-sky-400 cursor-pointer font-bold flex items-center gap-1 border-0 bg-transparent"
        title="Sao chép nội dung tin nhắn"
      >
        {copied ? "✅ Đã chép" : "📋 Sao chép"}
      </button>
      {onEdit && (
        <button 
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onEdit();
          }}
          className="text-[10px] text-slate-400 hover:text-sky-400 cursor-pointer font-bold flex items-center gap-1 border-0 bg-transparent pl-1.5 border-l border-slate-800"
          title="Chỉnh sửa và gửi lại tin nhắn này"
        >
          ✏️ Sửa
        </button>
      )}
    </div>
  );
};

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId] = useState(`session_${Math.random().toString(36).substring(2, 10)}`);
  const [loading, setLoading] = useState(false);
  const [activeModel, setActiveModel] = useState("Gemini 3.5 Flash");
  const [warning, setWarning] = useState(null);
  const [showSidebar, setShowSidebar] = useState(true);
  
  // State phục vụ panel Audit Logs (Wow-factor)
  const [auditLogs, setAuditLogs] = useState([]);
  const [showLogsPanel, setShowLogsPanel] = useState(true);
  const [currentClientId, setCurrentClientId] = useState(null);
  
  // State phụ phục vụ việc cập nhật dữ liệu real-time
  const [customerData, setCustomerData] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [interactions, setInteractions] = useState([]);

  const messagesEndRef = useRef(null);

  // Cuộn xuống tin nhắn mới nhất
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load lời chào chào mừng khi mở app
  useEffect(() => {
    // Chào mừng cơ bản, không bịa số liệu
    setMessages([
      {
        role: "model",
        content: "Chào anh/chị Relationship Manager (RM). Tôi là AI Co-Pilot CRM của Ngân hàng TMCP A. Hôm nay tôi có thể hỗ trợ anh/chị thực hiện các tác vụ tra cứu thông tin khách hàng, cập nhật cơ hội bán hàng, soạn thảo email/script tư vấn và tự động lưu vết tương tác. Hãy nhập tên khách hàng hoặc mã định danh của họ để bắt đầu làm việc!",
        model: "Gemini 3.5 Flash"
      }
    ]);
    
    // Tải audit logs lần đầu
    fetchAuditLogs();
    
    // Đặt lịch refresh audit logs mỗi 3 giây để RM thấy log real-time
    const interval = setInterval(fetchAuditLogs, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/audit-logs?limit=10`);
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data.logs || []);
      }
    } catch (e) {
      console.error("Lỗi khi tải audit logs:", e);
    }
  };

  // Hàm cập nhật trạng thái cơ hội bán hàng trực tiếp trên UI
  const handleUpdateOpportunityStatus = async (oppId, newStage) => {
    try {
      setLoading(true);
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: `Cập nhật cơ hội bán hàng ${oppId} sang trạng thái ${newStage}`
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setActiveModel(data.model);
        
        // Thêm câu hỏi và phản hồi của Agent vào lịch sử chat
        setMessages(prev => [
          ...prev,
          { role: "user", content: `RM bấm cập nhật trạng thái cơ hội ${oppId} thành ${newStage}` },
          { role: "model", content: data.response, model: data.model }
        ]);
        
        // Cập nhật lại dữ liệu locally nếu có
        setOpportunities(prev => 
          prev.map(opp => opp.opportunity_id === oppId ? { ...opp, stage: newStage } : opp)
        );
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      fetchAuditLogs();
    }
  };

  // Hàm gửi email và lưu lịch sử tương tác ngược lại CRM
  const handleSendEmail = async (subject, body) => {
    if (!currentClientId) return;
    
    try {
      setLoading(true);
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: `Ghi nhận tương tác Email cho khách hàng ${currentClientId} với tiêu đề: ${subject}`
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setActiveModel(data.model);
        
        setMessages(prev => [
          ...prev,
          { role: "user", content: `Bấm Gửi Email cho khách hàng ${currentClientId}` },
          { role: "model", content: data.response, model: data.model }
        ]);
        
        // Cập nhật local interactions timeline
        const newIntRecord = {
          interaction_id: `INT${Math.floor(Math.random() * 10000)}`,
          client_id: currentClientId,
          type: "Email",
          timestamp: new Date().toISOString(),
          content: `Đã gửi email: ${subject}`,
          created_by: "RM System"
        };
        setInteractions(prev => [newIntRecord, ...prev]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      fetchAuditLogs();
    }
  };

  // Hàm cốt lõi gửi tin nhắn lên Backend API
  const sendChatMessage = async (messageText) => {
    if (!messageText.trim() || loading) return;

    const userMsg = messageText.trim();
    setLoading(true);
    setWarning(null); // Reset cảnh báo cũ
    
    // Đưa tin nhắn của RM vào khung chat ngay lập tức
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMsg
        })
      });

      if (res.ok) {
        const data = await res.json();
        setActiveModel(data.model);
        
        setMessages(prev => [...prev, { 
          role: "model", 
          content: data.response, 
          model: data.model 
        }]);

        // Nạp cảnh báo từ backend nếu có (ví dụ: bị quota limit và phải fallback)
        if (data.warning) {
          setWarning(data.warning);
        }

        // Cố gắng parse dữ liệu có cấu trúc từ response để lưu local state (đồng bộ Generative UI)
        detectAndParseStructuredData(data.response);
      } else {
        setMessages(prev => [...prev, { 
          role: "model", 
          content: "Lỗi kết nối máy chủ API Backend.", 
          model: "System Error" 
        }]);
      }
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { 
        role: "model", 
        content: "Lỗi kết nối mạng, vui lòng thử lại.", 
        model: "Network Error" 
      }]);
    } finally {
      setLoading(false);
      fetchAuditLogs();
    }
  };

  // Gửi tin nhắn chat thông thường từ input form
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    await sendChatMessage(userMsg);
  };

  // Hàm tự động phát hiện JSON trong text để đổ dữ liệu cho các Card Component
  const detectAndParseStructuredData = (text) => {
    try {
      const jsonRegex = /```json\s*([\s\S]*?)\s*```/g;
      const match = jsonRegex.exec(text);
      if (match && match[1]) {
        const parsed = JSON.parse(match[1].trim());
        
        // Nếu là cấu trúc dashboard gộp (profile, opportunities, interactions)
        if (parsed.profile && parsed.opportunities && parsed.interactions) {
          setCustomerData(parsed.profile);
          setCurrentClientId(parsed.profile.client_id);
          setOpportunities(parsed.opportunities);
          setInteractions(parsed.interactions);
        }
        // Nếu là profile khách hàng đơn lẻ
        else if (parsed.client_id && parsed.name && parsed.segment) {
          setCustomerData(parsed);
          setCurrentClientId(parsed.client_id);
          
          // Reset các mảng dữ liệu phụ liên quan
          setOpportunities([]);
          setInteractions([]);
        }
        // Nếu là mảng cơ hội bán hàng
        else if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].opportunity_id) {
          setOpportunities(parsed);
        }
        // Nếu là mảng lịch sử tương tác
        else if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].interaction_id) {
          setInteractions(parsed);
        }
      }
    } catch (e) {
      console.log("Không thể tự động parse JSON (không ảnh hưởng):", e);
    }
  };

  // Hàm parser markdown cơ bản hiển thị đẹp mắt trong React
  const parseMarkdown = (text) => {
    if (!text) return "";
    
    const lines = text.split("\n");
    
    return lines.map((line, lineIndex) => {
      // 1. Nhận diện tiêu đề (Headers)
      const header3Match = line.match(/^###\s+(.*)$/);
      const header2Match = line.match(/^##\s+(.*)$/);
      const header1Match = line.match(/^#\s+(.*)$/);
      
      let isHeader = false;
      let headerLevel = 0;
      let content = line;
      
      if (header3Match) {
        isHeader = true;
        headerLevel = 3;
        content = header3Match[1];
      } else if (header2Match) {
        isHeader = true;
        headerLevel = 2;
        content = header2Match[1];
      } else if (header1Match) {
        isHeader = true;
        headerLevel = 1;
        content = header1Match[1];
      }
      
      // 2. Nhận diện danh sách (List items)
      const orderedListMatch = content.match(/^(\d+)\.\s+(.*)$/);
      const unorderedListMatch = content.match(/^([*\-–])\s+(.*)$/);
      
      let isListItem = false;
      let listPrefix = "";
      
      if (orderedListMatch) {
        isListItem = true;
        listPrefix = orderedListMatch[1] + ". ";
        content = orderedListMatch[2];
      } else if (unorderedListMatch) {
        isListItem = true;
        listPrefix = "• ";
        content = unorderedListMatch[2];
      }
      
      // 3. Phân tích inline styles: Link [text](url), **in đậm**, *'yêu cầu gợi ý'*, *in nghiêng*, `inline code`
      const parseInline = (str) => {
        // Regex để phân tách các định dạng inline
        const inlineRegex = /(\[.*?\]\(.*?\)\s*|\*\*.*?\*\*|\*'.*?'\*|\*`.*?`\*|\*.*?\*|`.*?`)/g;
        const subParts = str.split(inlineRegex);
        
        return subParts.map((part, partIndex) => {
          // Xử lý Link Markdown
          if (part.startsWith("[") && part.includes("](")) {
            const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
            if (linkMatch) {
              const text = linkMatch[1];
              const url = linkMatch[2];
              return (
                <a 
                  key={partIndex} 
                  href={url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-sky-400 hover:text-sky-300 underline font-semibold break-all"
                >
                  {text}
                </a>
              );
            }
          }
          // Xử lý In đậm
          if (part.startsWith("**") && part.endsWith("**")) {
            return (
              <strong key={partIndex} className="font-extrabold text-sky-400">
                {part.slice(2, -2)}
              </strong>
            );
          }
          // Xử lý gợi ý click
          if (
            (part.startsWith("*'") && part.endsWith("'*")) ||
            (part.startsWith("*`") && part.endsWith("`*"))
          ) {
            const command = part.slice(2, -2);
            return (
              <button
                key={partIndex}
                onClick={() => sendChatMessage(command)}
                className="inline-flex items-center gap-1.5 bg-sky-500/10 hover:bg-sky-500/20 active:scale-[0.97] border border-sky-500/30 hover:border-sky-500/50 text-sky-300 px-2 py-0.5 my-0.5 rounded-md text-xs font-semibold cursor-pointer transition-all duration-150 shadow-sm"
                title="Bấm để gửi nhanh yêu cầu này"
              >
                💬 <span className="underline decoration-dotted decoration-sky-500/50">{command}</span>
              </button>
            );
          }
          // Xử lý In nghiêng
          if (part.startsWith("*") && part.endsWith("*")) {
            return (
              <em key={partIndex} className="italic text-slate-300">
                {part.slice(1, -1)}
              </em>
            );
          }
          // Xử lý Code inline
          if (part.startsWith("`") && part.endsWith("`")) {
            return (
              <code key={partIndex} className="bg-slate-950 px-1.5 py-0.5 rounded text-rose-400 font-mono text-[11px] border border-slate-900">
                {part.slice(1, -1)}
              </code>
            );
          }
          return part;
        });
      };
      
      // Render thẻ JSX tương ứng dựa vào Header hay ListItem
      if (isHeader) {
        const headerClasses = 
          headerLevel === 1 ? "text-lg font-bold text-slate-100 mt-4 mb-2 pb-1 border-b border-slate-800/80" :
          headerLevel === 2 ? "text-base font-bold text-slate-200 mt-3 mb-1.5" :
          "text-[13px] font-bold text-sky-300 mt-2.5 mb-1 uppercase tracking-wider";
          
        return (
          <div key={lineIndex} className={headerClasses}>
            {parseInline(content)}
          </div>
        );
      }
      
      if (isListItem) {
        return (
          <div key={lineIndex} className="flex gap-2 ml-4 my-1 text-[13px] leading-relaxed">
            <span className="text-sky-400 font-bold select-none">{listPrefix}</span>
            <span className="flex-1 text-slate-200">{parseInline(content)}</span>
          </div>
        );
      }
      
      return (
        <div key={lineIndex} className="min-h-[1.2rem] my-1 text-[13px] leading-relaxed text-slate-200">
          {parseInline(content)}
        </div>
      );
    });
  };

  // Hàm helper để render tin nhắn có chứa Generative UI
  const renderMessageContent = (msg) => {
    // 1. Phân tách text thông thường và khối code JSON
    const jsonRegex = /```json\s*([\s\S]*?)\s*```/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = jsonRegex.exec(msg.content)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ type: "text", content: msg.content.substring(lastIndex, match.index) });
      }
      parts.push({ type: "json", content: match[1].trim() });
      lastIndex = jsonRegex.lastIndex;
    }

    if (lastIndex < msg.content.length) {
      parts.push({ type: "text", content: msg.content.substring(lastIndex) });
    }

    if (parts.length === 0) {
      return <div className="space-y-1">{parseMarkdown(msg.content)}</div>;
    }

    return (
      <div>
        {parts.map((part, index) => {
          if (part.type === "text") {
            return <div key={index} className="space-y-1 my-1">{parseMarkdown(part.content)}</div>;
          } else {
            try {
              const data = JSON.parse(part.content);
              
              // Render Unified Customer Dashboard (Profile + Opportunities + Interactions)
              if (data.profile && data.opportunities && data.interactions) {
                return (
                  <div key={index} className="space-y-4 my-3 p-1.5 border border-slate-850 rounded-xl bg-slate-900/20">
                    <div className="text-[10px] text-sky-400 font-extrabold uppercase tracking-wider px-2 pt-1 flex items-center gap-1.5">
                      <span>📂</span> Báo cáo tổng hợp hồ sơ RM
                    </div>
                    <CustomerProfileCard data={data.profile} />
                    <OpportunityManager 
                      opportunities={data.opportunities} 
                      onUpdateStatus={handleUpdateOpportunityStatus} 
                    />
                    <InteractionTimeline history={data.interactions} />
                  </div>
                );
              }
              
              // Render Customer Info Card
              if (data.client_id && data.name && data.segment) {
                return <CustomerProfileCard key={index} data={data} />;
              }
              // Render Opportunity Manager Card
              if (Array.isArray(data) && data.length > 0 && data[0].opportunity_id) {
                return (
                  <OpportunityManager 
                    key={index} 
                    opportunities={data} 
                    onUpdateStatus={handleUpdateOpportunityStatus} 
                  />
                );
              }
              // Render Interaction History Timeline
              if (Array.isArray(data) && data.length > 0 && data[0].interaction_id) {
                return <InteractionTimeline key={index} history={data} />;
              }
              // Render Email Draft Editor
              if (data.template_id && data.subject) {
                return (
                  <EmailDraftEditor
                    key={index}
                    template={data}
                    clientName={customerData?.name || "Khách hàng"}
                    rmName={customerData?.assigned_rm || "RM System"}
                    onSendEmail={handleSendEmail}
                  />
                );
              }
              
              // Nếu là cấu trúc JSON khác, hiển thị code block
              return (
                <pre key={index} className="bg-slate-900/80 p-3 rounded border border-slate-800 text-xs font-mono overflow-x-auto text-sky-300">
                  <code>{JSON.stringify(data, null, 2)}</code>
                </pre>
              );
            } catch (e) {
              return (
                <pre key={index} className="bg-slate-900/80 p-3 rounded border border-slate-800 text-xs font-mono overflow-x-auto text-rose-400">
                  <code>{part.content}</code>
                </pre>
              );
            }
          }
        })}
      </div>
    );
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      
      {/* SIDEBAR BÊN TRÁI - LỊCH SỬ CHAT (WOW FEATURE) */}
      <div className={`transition-all duration-300 ease-in-out bg-slate-900/70 border-r border-slate-800/80 flex flex-col h-full ${showSidebar ? "w-64" : "w-0 overflow-hidden border-r-0"}`}>
        <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/40">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            📂 Lịch sử hội thoại
          </span>
          <button 
            type="button"
            onClick={() => setShowSidebar(false)}
            className="text-slate-400 hover:text-slate-200 cursor-pointer p-1 rounded hover:bg-slate-800 text-[10px]"
            title="Thu nhỏ thanh lịch sử"
          >
            ◀
          </button>
        </div>
        
        {/* Danh sách phiên chat */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <button className="w-full text-left p-2.5 rounded-lg text-xs font-medium bg-sky-500/10 text-sky-300 border border-sky-500/20 flex items-center gap-2">
            <span>💬</span>
            <span className="truncate flex-1">Phiên chat hiện tại</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          </button>
          
          <div className="text-[10px] text-slate-500 font-bold px-2.5 pt-3 pb-1 uppercase tracking-wider">Hành động mẫu</div>
          
          <button 
            onClick={() => sendChatMessage("Xem hồ sơ khách hàng KH001")}
            className="w-full text-left p-2 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 flex items-center gap-2 cursor-pointer transition-colors duration-150 border-0 bg-transparent"
          >
            <span>👤</span>
            <span className="truncate">Hồ sơ KH001 Bùi Ngọc Phương</span>
          </button>
          <button 
            onClick={() => sendChatMessage("Xem cơ hội bán hàng KH001")}
            className="w-full text-left p-2 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 flex items-center gap-2 cursor-pointer transition-colors duration-150 border-0 bg-transparent"
          >
            <span>💼</span>
            <span className="truncate">Cơ hội bán hàng KH001</span>
          </button>
          <button 
            onClick={() => sendChatMessage("Soạn email cho KH001")}
            className="w-full text-left p-2 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 flex items-center gap-2 cursor-pointer transition-colors duration-150 border-0 bg-transparent"
          >
            <span>✉️</span>
            <span className="truncate">Soạn email mẫu KH001</span>
          </button>
          <button 
            onClick={() => sendChatMessage("Bạn làm được gì?")}
            className="w-full text-left p-2 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 flex items-center gap-2 cursor-pointer transition-colors duration-150 border-0 bg-transparent"
          >
            <span>❓</span>
            <span className="truncate">Hướng dẫn sử dụng Co-Pilot</span>
          </button>
        </div>
        
        <div className="p-3 border-t border-slate-800 bg-slate-950/20 text-center">
          <button 
            type="button"
            onClick={() => {
              setMessages([{
                role: "model",
                content: "Chào anh/chị Relationship Manager (RM). Tôi là AI Co-Pilot CRM của Ngân hàng TMCP A. Hãy nhập yêu cầu để bắt đầu làm việc!",
                model: "Gemini 3.5 Flash"
              }]);
              setWarning(null);
            }}
            className="w-full bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 py-2 px-3 rounded-lg border border-slate-700 cursor-pointer font-semibold transition-all"
          >
            ➕ Tạo hội thoại mới
          </button>
        </div>
      </div>
      
      {/* 1. KHU VỰC CHAT CHÍNH (LEFT / MIDDLE PANEL) */}
      <div className="flex-1 flex flex-col h-full relative" style={{ borderRight: "1px solid rgba(255, 255, 255, 0.05)" }}>
        
        {/* Header Chat */}
        <header className="flex justify-between items-center px-6 py-4 border-b border-slate-800 bg-slate-900/40 backdrop-blur-md">
          <div className="flex items-center gap-3">
            {!showSidebar && (
              <button 
                type="button"
                onClick={() => setShowSidebar(true)}
                className="text-slate-400 hover:text-slate-200 cursor-pointer p-1 rounded hover:bg-slate-800 text-[10px] mr-1 flex items-center justify-center border border-slate-700 bg-slate-900/40"
                title="Mở rộng thanh lịch sử"
              >
                ▶
              </button>
            )}
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
            <h1 className="text-base font-bold text-slate-100 m-0">BotAutoCRM Co-Pilot</h1>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Badge chỉ thị mô hình LLM đang xử lý thực tế */}
            <span className="bg-sky-500/10 text-sky-300 border border-sky-500/30 text-xs px-3 py-1 rounded-full font-bold">
              ⚡ Mô hình: {activeModel}
            </span>
            
            <button
              onClick={() => setShowLogsPanel(!showLogsPanel)}
              className="px-3 py-1 text-xs rounded border border-slate-700 bg-slate-800 hover:bg-slate-700 cursor-pointer text-slate-300"
            >
              {showLogsPanel ? "👁️ Ẩn Logs Bảo Mật" : "👁️ Hiện Logs Bảo Mật"}
            </button>
          </div>
        </header>

        {warning && (
          <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5 flex items-center justify-between text-xs text-amber-300 gap-2">
            <div className="flex items-center gap-2">
              <span>⚠️</span>
              <span>
                <strong>Hệ thống đang chạy ở chế độ dự phòng (Offline Mode):</strong> {warning}
              </span>
            </div>
            <button 
              onClick={() => setWarning(null)}
              className="text-amber-400 hover:text-amber-200 cursor-pointer font-bold border-0 bg-transparent px-1 text-xs"
            >
              Đóng
            </button>
          </div>
        )}

        {/* Danh sách tin nhắn */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.map((msg, index) => (
            <div 
              key={index}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div 
                className={`max-w-[70%] p-4 pb-7 rounded-2xl relative group ${
                  msg.role === "user" 
                    ? "bg-sky-600 text-white rounded-br-none" 
                    : "bg-slate-900/80 border border-slate-800 text-slate-200 rounded-bl-none"
                }`}
              >
                {/* Tên người gửi */}
                <span className="text-[10px] text-slate-400 font-bold block mb-1">
                  {msg.role === "user" ? "RM (BẠN)" : `AI CO-PILOT (${msg.model || "Gemini"})`}
                </span>
                {renderMessageContent(msg)}
                
                {/* Thao tác nhanh Copy/Edit */}
                <MessageActionButton 
                  text={msg.content} 
                  onEdit={msg.role === "user" ? () => setInput(msg.content) : null} 
                />
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl rounded-bl-none max-w-[70%] flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce"></div>
                <div className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                <div className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                <span className="text-xs text-slate-500 ml-1">Đang suy nghĩ...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Khung nhập tin nhắn */}
        <footer className="p-4 bg-slate-900/20 border-t border-slate-800">
          <form onSubmit={handleSendMessage} className="flex gap-2 max-w-4xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Nhập yêu cầu: 'Xem hồ sơ Nguyễn Văn A', 'Cập nhật cơ hội', 'Soạn email'..."
              disabled={loading}
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-sky-500 hover:bg-sky-400 text-white font-bold px-5 py-3 rounded-xl text-sm cursor-pointer border-0 shadow-lg shadow-sky-500/10"
            >
              Gửi
            </button>
          </form>
        </footer>
      </div>

      {/* 2. PANEL HIỂN THỊ AUDIT LOGS (RIGHT PANEL - WOW FACTOR) */}
      {showLogsPanel && (
        <div className="w-[450px] h-full bg-slate-900/60 flex flex-col h-full animate-fade-in-up" style={{ borderLeft: "1px solid rgba(255, 255, 255, 0.05)" }}>
          <header className="px-5 py-4 border-b border-slate-800 bg-slate-900/90 flex justify-between items-center">
            <h2 className="text-xs font-bold text-slate-400 m-0 uppercase tracking-widest">
              🛡️ Audit Log Bảo Mật (Real-time SQLite)
            </h2>
            <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] px-2 py-0.5 rounded font-bold uppercase">
              ĐÃ ẨN PII
            </span>
          </header>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {auditLogs.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-8">Chưa có log bảo mật nào được ghi nhận.</p>
            ) : (
              auditLogs.map((log) => (
                <div key={log.id} className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 text-xs font-mono space-y-2">
                  <div className="flex justify-between items-center text-[10px] text-slate-500 border-b border-slate-900 pb-1.5">
                    <span>ID: LOG_{log.id} | {log.model_name}</span>
                    <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </div>
                  
                  <div>
                    <span className="text-amber-500/80 block font-bold text-[9px]">PROMPT ĐÃ LỌC BẢO MẬT:</span>
                    <p className="text-slate-300 m-0 bg-slate-900/40 p-1.5 rounded mt-0.5 whitespace-pre-wrap leading-relaxed border border-slate-900">
                      {log.prompt}
                    </p>
                  </div>
                  
                  <div>
                    <span className="text-sky-500/80 block font-bold text-[9px]">PHẢN HỒI AI ĐÃ ẨN PII:</span>
                    <p className="text-slate-300 m-0 bg-slate-900/40 p-1.5 rounded mt-0.5 whitespace-pre-wrap leading-relaxed border border-slate-900 max-h-[100px] overflow-y-auto">
                      {log.response}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

    </div>
  );
}
