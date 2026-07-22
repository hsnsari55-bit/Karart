import React, { useState, useRef, useEffect } from "react";
import Markdown from "react-markdown";
import { ChatMessage } from "../types";
import { Send, Sparkles, Loader2, RefreshCw } from "lucide-react";

interface AIChatPanelProps {
  onSendMessage: (message: string) => Promise<string>;
}

export default function AIChatPanel({ onSendMessage }: AIChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Merhaba! Ben KaRar Mimari Yapay Zekâ Yardımcısıyım. 'GÜZELCE 467 ADA 9 PARSEL' projenizin parsed CAD ve BIM verilerini inceleyerek sorularınızı yanıtlayabilirim.\n\nDuvar kalınlıkları, kapı adetleri, oda dağılımları veya 3D model ihracı hakkında sorularınızı sorabilirsiniz.",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Quick questions for easy user interaction
  const quickQuestions = [
    { label: "Duvar Analizi 🧱", query: "Duvarların kalınlık sınıflandırmasını ve toplam uzunluklarını özetler misin?" },
    { label: "Kapı Sayısı 🚪", query: "Zemin katta kaç adet kapı tespit edildi ve genişlikleri nedir?" },
    { label: "Oda Alanları 📐", query: "Zemin kat odalarının m² alanlarını ve kullanım türlerini söyler misin?" },
    { label: "3D İnşa Metodu 🏗️", query: "KaRar platformu 2D CAD'i 3D BIM modeline (IFC) nasıl dönüştürüyor?" },
  ];

  // Auto scroll chat to bottom
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      role: "user",
      content: textToSend,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      const reply = await onSendMessage(textToSend);
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: reply,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: "Üzgünüm, API isteği sırasında bir hata oluştu: " + err.message,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[550px] bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-zinc-950 border-b border-zinc-800">
        <div className="flex items-center space-x-2">
          <div className="bg-emerald-500/15 p-1.5 rounded-lg text-emerald-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold font-mono tracking-wider text-zinc-100">
              AI DECISION LAYER
            </h3>
            <p className="text-[10px] text-zinc-400 font-mono">
              ACTIVE BLUEPRINT ASSISTANT
            </p>
          </div>
        </div>

        <button
          onClick={() =>
            setMessages([
              {
                role: "assistant",
                content: "Sohbet temizlendi. KaRar AI hazır. Nasıl yardımcı olabilirim?",
                timestamp: new Date(),
              },
            ])
          }
          className="text-zinc-500 hover:text-zinc-300 p-1 rounded hover:bg-zinc-800 transition-colors"
          title="Sohbeti Sıfırla"
          id="btn_chat_reset"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Message History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-zinc-950/40">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-xl px-3.5 py-2 text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-emerald-600 text-white rounded-br-none"
                  : "bg-zinc-800/90 text-zinc-200 border border-zinc-700/60 rounded-bl-none shadow-md"
              }`}
            >
              {msg.role === "assistant" ? (
                <div className="markdown-body prose prose-invert max-w-none text-zinc-100 font-sans prose-sm prose-p:leading-relaxed prose-pre:bg-zinc-900/60 prose-pre:border prose-pre:border-zinc-700/50">
                  <Markdown>{msg.content}</Markdown>
                </div>
              ) : (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              )}
              <span
                className={`block mt-1.5 text-[8px] font-mono text-right ${
                  msg.role === "user" ? "text-emerald-200" : "text-zinc-500"
                }`}
              >
                {msg.timestamp.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-zinc-800/90 border border-zinc-700/60 rounded-xl rounded-bl-none px-3.5 py-2.5 text-xs text-zinc-400 flex items-center space-x-2 shadow-md">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
              <span className="font-mono text-[10px] tracking-wider text-zinc-300">
                KaRar AI Mimar analiz yapıyor...
              </span>
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Suggested Quick Questions */}
      <div className="px-4 py-2 bg-zinc-950 border-t border-zinc-800 flex flex-wrap gap-1.5">
        {quickQuestions.map((q, idx) => (
          <button
            key={idx}
            id={`btn_quick_query_${idx}`}
            onClick={() => handleSend(q.query)}
            className="text-[10px] bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-zinc-100 px-2 py-1 rounded transition-colors font-mono"
          >
            {q.label}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend(inputValue);
        }}
        className="p-3 bg-zinc-950 border-t border-zinc-800 flex items-center space-x-2"
      >
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Mimarideki detayları sorun... (örn: duvar kalınlıkları)"
          className="flex-1 bg-zinc-900 border border-zinc-800 focus:border-emerald-600 rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none transition-colors font-sans"
          id="chat_input_field"
        />
        <button
          type="submit"
          disabled={!inputValue.trim() || isLoading}
          className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white p-2 rounded-lg transition-colors shadow-md"
          id="btn_chat_send"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
