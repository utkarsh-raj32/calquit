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
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTools, setActiveTools] = useState<ToolIndicator[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

    try {
      const response = await fetch(api.getChatStreamUrl(), {
        method: "POST",
        headers: api.getHeaders(),
        body: JSON.stringify({ messages: history }),
      });

      if (!response.ok) throw new Error("Stream connection failed");
      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";
      
      const assistantId = (Date.now() + 1).toString();
      setMessages((prev) => [...prev, { id: assistantId, role: "assistant", content: "", isStreaming: true }]);

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
                 setMessages((prev) => prev.map((msg) => 
                  msg.id === assistantId ? { ...msg, isStreaming: false } : msg
                ));
                if(data.type === "error") {
                   console.error("Stream error:", data.content);
                }
              }
            } catch (e) {
              console.error("Error parsing stream chunk", e, dataStr);
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
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
        
        {/* Tool Indicators */}
        {activeTools.length > 0 && (
          <div className="flex flex-col space-y-2 self-start mr-auto max-w-[85%]">
            {activeTools.map((tool) => (
              <div key={tool.id} className="flex items-center space-x-2 text-xs text-black bg-white px-3 py-2 rounded-none border-2 border-black">
                {tool.status === "running" ? (
                  <Loader2 className="w-3 h-3 animate-spin text-black" />
                ) : (
                  <div className="w-3 h-3 rounded-none bg-black" />
                )}
                <span className="font-mono">
                  {tool.tool.replace(/_/g, " ")} 
                  {tool.status === "running" ? "..." : " ✓"}
                </span>
              </div>
            ))}
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
