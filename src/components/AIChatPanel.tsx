import React, { useState, useRef, useEffect } from "react";
import Markdown from "react-markdown";
import { ChatMessage } from "../types";
import { Send, Sparkles, Loader2, RefreshCw, AlertTriangle, Bug, Terminal, Filter } from "lucide-react";

interface AIChatPanelProps {
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  onSendMessage: (message: string) => Promise<string>;
  onRetryStep?: (stepId: string) => void;
}

export default function AIChatPanel({
  messages,
  setMessages,
  onSendMessage,
  onRetryStep,
}: AIChatPanelProps) {
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [filterErrorsOnly, setFilterErrorsOnly] = useState(false);
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
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const visibleMessages = filterErrorsOnly
    ? messages.filter((m) => m.isError)
    : messages;

  const errorCount = messages.filter((m) => m.isError).length;

  return (
    <div className="flex flex-col h-[580px] bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-zinc-950 border-b border-zinc-800">
        <div className="flex items-center space-x-2">
          <div className="bg-emerald-500/15 p-1.5 rounded-lg text-emerald-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-bold font-mono tracking-wider text-zinc-100">
                AI DECISION & DEBUGGING LAYER
              </h3>
              {errorCount > 0 && (
                <span className="bg-red-500/20 text-red-400 text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border border-red-500/30 animate-pulse flex items-center space-x-1">
                  <AlertTriangle className="w-3 h-3" />
                  <span>{errorCount} HATA YAKALANDI</span>
                </span>
              )}
            </div>
            <p className="text-[10px] text-zinc-400 font-mono">
              REAL-TIME API ERROR CAPTURE & BLUEPRINT DIAGNOSTICS
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Error Filter Toggle */}
          <button
            onClick={() => setFilterErrorsOnly((prev) => !prev)}
            className={`px-2 py-1 rounded text-[10px] font-mono font-bold flex items-center space-x-1 border transition-all ${
              filterErrorsOnly
                ? "bg-red-950/60 text-red-400 border-red-800"
                : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-200"
            }`}
            title="Sadece Hata Loglarını Göster"
            id="btn_filter_errors_toggle"
          >
            <Filter className="w-3 h-3" />
            <span>{filterErrorsOnly ? "Hata Filtresi Aktif" : "Hatalar"}</span>
          </button>

          <button
            onClick={() =>
              setMessages([
                {
                  role: "assistant",
                  content: "Sohbet ve hata logları temizlendi. KaRar AI hazır. Nasıl yardımcı olabilirim?",
                  timestamp: new Date(),
                },
              ])
            }
            className="text-zinc-500 hover:text-zinc-300 p-1.5 rounded hover:bg-zinc-800 transition-colors"
            title="Sohbeti Sıfırla"
            id="btn_chat_reset"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Message History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-zinc-950/40">
        {visibleMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-zinc-500 font-mono text-xs space-y-2">
            <Bug className="w-8 h-8 text-zinc-600" />
            <span>Henüz yakalanmış bir hata logu yok.</span>
          </div>
        ) : (
          visibleMessages.map((msg, idx) => {
            const isErr = msg.isError;
            return (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[90%] rounded-xl px-4 py-3 text-xs leading-relaxed transition-all shadow-md ${
                    msg.role === "user"
                      ? "bg-emerald-600 text-white rounded-br-none"
                      : isErr
                      ? "bg-red-950/40 text-red-100 border border-red-500/40 rounded-bl-none shadow-red-950/20"
                      : "bg-zinc-800/90 text-zinc-200 border border-zinc-700/60 rounded-bl-none"
                  }`}
                >
                  {/* Error Header Badge */}
                  {isErr && (
                    <div className="flex items-center justify-between pb-2 mb-2 border-b border-red-500/30 text-red-400 font-mono text-[10px] font-bold">
                      <span className="flex items-center space-x-1.5">
                        <Bug className="w-3.5 h-3.5 text-red-400" />
                        <span>API ADIM HATA LOGU {msg.stepId ? `[${msg.stepId.toUpperCase()}]` : ""}</span>
                      </span>
                      {msg.statusCode && (
                        <span className="bg-red-500/20 px-1.5 py-0.5 rounded border border-red-500/30">
                          STATUS {msg.statusCode}
                        </span>
                      )}
                    </div>
                  )}

                  {msg.role === "assistant" || msg.role === "system" ? (
                    <div className="markdown-body prose prose-invert max-w-none text-zinc-100 font-sans prose-sm prose-p:leading-relaxed prose-pre:bg-zinc-950/80 prose-pre:border prose-pre:border-red-500/20 prose-pre:text-red-200">
                      <Markdown>{msg.content}</Markdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  )}

                  {/* Diagnostic action buttons for captured errors */}
                  {isErr && (
                    <div className="mt-3 pt-2 border-t border-red-500/20 flex flex-wrap gap-2">
                      <button
                        onClick={() =>
                          handleSend(
                            `Aşağıdaki adım hatasını analiz et ve çözüm öner: \n\n${msg.content}`
                          )
                        }
                        className="bg-red-900/60 hover:bg-red-800 text-red-200 border border-red-700/60 px-2.5 py-1 rounded text-[10px] font-mono font-bold flex items-center space-x-1.5 transition-colors"
                        id={`btn_analyze_error_${idx}`}
                      >
                        <Terminal className="w-3 h-3 text-red-300" />
                        <span>🔍 AI ile Hatayı Analiz Et</span>
                      </button>

                      {msg.stepId && onRetryStep && (
                        <button
                          onClick={() => onRetryStep(msg.stepId!)}
                          className="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 px-2.5 py-1 rounded text-[10px] font-mono font-bold flex items-center space-x-1.5 transition-colors"
                          id={`btn_retry_step_${idx}`}
                        >
                          <RefreshCw className="w-3 h-3 text-emerald-400" />
                          <span>🔄 Adımı Tekrar Çalıştır</span>
                        </button>
                      )}
                    </div>
                  )}

                  <span
                    className={`block mt-2 text-[8px] font-mono text-right ${
                      msg.role === "user"
                        ? "text-emerald-200"
                        : isErr
                        ? "text-red-400/80"
                        : "text-zinc-500"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </span>
                </div>
              </div>
            );
          })
        )}

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
          placeholder="Mimarideki detayları veya hata çözümlerini sorun..."
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
