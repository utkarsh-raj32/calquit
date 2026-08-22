"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, auth } from "@/lib/api";
import { cn } from "@/lib/utils";

type Message = {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  name?: string;
  tool_call_id?: string;
  isStreaming?: boolean;
};

type ToolIndicator = {
  id: string;
  tool: string;
  input: any;
  status: "running" | "completed";
  output?: string;
};

export default function ChatWindow({ context }: { context: "customer" | "internal" }) {
  const storageKey = `parcelpilot_chat_${context}`;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTools, setActiveTools] = useState<ToolIndicator[]>([]);
  const [hydrated, setHydrated] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load messages from sessionStorage on mount (client-side only)
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(storageKey);
      if (saved) {
        const parsed: Message[] = JSON.parse(saved);
        setMessages(parsed.map((m) => ({ ...m, isStreaming: false })));
      }
    } catch {}
    setHydrated(true);
  }, [storageKey]);

  // Persist messages to sessionStorage on every change (only after initial hydration)
  useEffect(() => {
    if (!hydrated) return;
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(messages));
    } catch {}
  }, [messages, storageKey, hydrated]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeTools]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsGenerating(true);
    setActiveTools([]);

    // Prepare history for API
    const history = [...messages, userMsg].map(({ role, content, name, tool_call_id }) => ({
      role, content, name, tool_call_id
    }));

    const assistantId = (Date.now() + 1).toString();
    setMessages((prev) => [...prev, { id: assistantId, role: "assistant", content: "", isStreaming: true }]);

    try {
      const response = await fetch(api.getChatStreamUrl(), {
        method: "POST",
        headers: api.getHeaders(),
        body: JSON.stringify({ messages: history }),
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => "Stream connection failed");
        throw new Error(errorText || `HTTP ${response.status}: Failed to connect to AI service`);
      }
      if (!response.body) throw new Error("No response body received from server");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6);
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === "token") {
                assistantContent += data.content;
                setMessages((prev) => prev.map((msg) => 
                  msg.id === assistantId ? { ...msg, content: assistantContent } : msg
                ));
              } 
              else if (data.type === "tool_start") {
                const toolId = Date.now().toString() + Math.random().toString(36).substring(7);
                setActiveTools((prev) => [...prev, {
                  id: toolId,
                  tool: data.tool,
                  input: data.input,
                  status: "running"
                }]);
              }
              else if (data.type === "tool_end") {
                setActiveTools((prev) => {
                  const lastRunning = [...prev].reverse().find(t => t.tool === data.tool && t.status === "running");
                  if (lastRunning) {
                    return prev.map(t => t.id === lastRunning.id ? { ...t, status: "completed", output: data.output } : t);
                  }
                  return prev;
                });
              }
              else if (data.type === "done" || data.type === "error") {
                let displayError = data.content;
                if (data.type === "error" && data.content) {
                  if (data.content.includes("RESOURCE_EXHAUSTED") || data.content.includes("429")) {
                    displayError = "⏳ **Google Gemini Rate Limit**: The free-tier request quota is temporarily cooling down. Please wait 15–20 seconds and send your message again.";
                  } else if (data.content.includes("503") || data.content.includes("UNAVAILABLE")) {
                    displayError = "⚠️ **Gemini High Demand**: Model servers are experiencing temporary high traffic. Please retry in a moment.";
                  } else {
                    displayError = `⚠️ **Error**: ${data.content}`;
                  }
                }

                setMessages((prev) => prev.map((msg) => 
                  msg.id === assistantId ? { 
                    ...msg, 
                    isStreaming: false,
                    content: data.type === "error" ? displayError : (msg.content || "")
                  } : msg
                ));
              }
            } catch (e) {
              // Parse error handling without modal interruption
            }
          }
        }
      }
    } catch (error: any) {
      let friendlyConnError = "Unable to connect to AI backend service. Ensure the backend is running.";
      if (error?.message?.includes("Failed to fetch")) {
        friendlyConnError = "⚠️ **Backend Service Notice**: Connecting to backend API... If local, ensure `uvicorn` is running on port 8000.";
      }
      setMessages((prev) => prev.map((msg) => 
        msg.id === assistantId ? { 
          ...msg, 
          isStreaming: false, 
          content: friendlyConnError
        } : msg
      ));
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-none overflow-hidden border-2 border-black">
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <h3 className="text-lg font-medium mb-2 text-black">ParcelPilot AI Support</h3>
              <p>How can I help you today?</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
             msg.role !== "tool" && (
                <div
                  key={msg.id}
                  className={cn(
                    "flex flex-col max-w-[85%] rounded-none px-4 py-3 border-2",
                    msg.role === "user" 
                      ? "bg-black text-white border-black self-end ml-auto" 
                      : "bg-white text-black self-start mr-auto border-black shadow-none"
                  )}
                >
                  {msg.role === "assistant" && context === "internal" && (
                     <div className="text-xs font-bold text-black mb-1 border-b border-black inline-block pb-1">AI Assistant</div>
                  )}
                  <div className={cn("prose max-w-none text-sm", msg.role === "user" ? "text-white prose-p:text-white" : "text-black prose-p:text-black")}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  {msg.isStreaming && (
                    <span className="inline-block w-2 h-4 bg-black animate-pulse ml-1 mt-1"></span>
                  )}
                </div>
             )
          ))
        )}
        
        {/* Active Progress Meter & Reasoning Pipeline */}
        {isGenerating && (
          <div className="flex flex-col space-y-3 self-start mr-auto max-w-[90%] w-full bg-white text-black border-2 border-black p-4">
            <div className="flex items-center justify-between border-b-2 border-black pb-2 text-xs font-bold uppercase tracking-wider">
              <span className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 bg-black animate-ping" />
                <span>Agent Execution Pipeline</span>
              </span>
              <span className="font-mono">
                {activeTools.length === 0 
                  ? "Analyzing Query & Planning..." 
                  : `${activeTools.filter((t) => t.status === "completed").length} / ${activeTools.length} Completed`}
              </span>
            </div>

            {/* Visual Progress Bar */}
            <div className="w-full bg-gray-100 border border-black h-3 relative overflow-hidden">
              <div 
                className="bg-black h-full transition-all duration-300"
                style={{ 
                  width: activeTools.length === 0 
                    ? "25%" 
                    : `${Math.max(30, Math.round((activeTools.filter((t) => t.status === "completed").length / activeTools.length) * 100))}%` 
                }}
              />
            </div>

            {/* Initial Planning State before first tool fires */}
            {activeTools.length === 0 && (
              <div className="flex items-center space-x-2.5 p-2.5 border border-black bg-gray-50 text-xs font-mono">
                <Loader2 className="w-4 h-4 animate-spin text-black" />
                <div className="flex flex-col">
                  <span className="font-bold text-black">Parsing query & checking role permissions...</span>
                  <span className="text-[11px] text-gray-500">Querying ChromaDB vector embeddings & source reliability tiers</span>
                </div>
              </div>
            )}

            {/* Active Tool Steps */}
            {activeTools.length > 0 && (
              <div className="space-y-2 pt-1">
                {activeTools.map((tool, index) => {
                  const isRunning = tool.status === "running";
                  
                  let description = tool.tool.replace(/_/g, " ");
                  if (tool.tool === "document_search") {
                    const q = tool.input?.query || "";
                    description = q ? `Searching knowledge base for "${q}"` : "Searching knowledge base";
                  } else if (tool.tool === "get_order") {
                    description = `Fetching order record: ${tool.input?.order_id || ""}`;
                  } else if (tool.tool === "get_ticket") {
                    description = `Looking up ticket details: ${tool.input?.ticket_id || ""}`;
                  } else if (tool.tool === "calculate_cancellation_eligibility") {
                    description = `Checking cancellation SOP & customer agreement overrides`;
                  } else if (tool.tool === "calculate_service_credit_eligibility") {
                    description = `Calculating carrier delay thresholds & service credit`;
                  } else if (tool.tool === "check_sla_status") {
                    description = `Auditing SLA targets and elapsed time calculation`;
                  } else if (tool.tool === "escalate_ticket") {
                    description = `Triggering ticket escalation to engineering`;
                  }

                  return (
                    <div 
                      key={tool.id} 
                      className={cn(
                        "flex items-start justify-between p-2.5 border text-xs font-mono transition-all",
                        isRunning ? "border-black bg-gray-100 font-bold" : "border-gray-300 bg-white text-gray-700"
                      )}
                    >
                      <div className="flex items-start space-x-2.5">
                        <span className="bg-black text-white px-1.5 py-0.5 text-[10px]">
                          STEP {index + 1}
                        </span>
                        <div className="flex flex-col">
                          <span className="text-black">{description}</span>
                          {tool.input && Object.keys(tool.input).length > 0 && !isRunning && (
                            <span className="text-[11px] text-gray-500 font-mono mt-0.5">
                              Target: {JSON.stringify(tool.input)}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center space-x-1.5 pl-3">
                        {isRunning ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin text-black" />
                            <span className="text-black font-bold uppercase tracking-wider text-[11px]">Searching...</span>
                          </>
                        ) : (
                          <span className="bg-black text-white px-2 py-0.5 text-[11px] font-bold">
                            ✓ COMPLETED
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            
            {activeTools.length > 0 && activeTools.every((t) => t.status === "completed") && (
              <div className="pt-2 border-t border-gray-200 flex items-center space-x-2 text-xs font-mono text-black">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-black" />
                <span>Synthesizing final response with verified source precedence...</span>
              </div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-white border-t-2 border-black">
        <form onSubmit={handleSubmit} className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isGenerating}
            className="w-full bg-white border-2 border-black focus:border-black focus:ring-0 rounded-none pl-4 pr-12 py-3 text-sm text-black placeholder:text-gray-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isGenerating}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-black hover:bg-gray-800 text-white rounded-none disabled:opacity-50 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
