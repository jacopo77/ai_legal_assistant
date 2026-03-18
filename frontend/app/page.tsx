/* eslint-disable @next/next/no-img-element */
"use client";

import { useRef, useState, useEffect } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

type Source = { n: number; citation: string | null; url: string; title: string | null };
type Message = { role: "user" | "assistant"; content: string; country?: string; error?: boolean; sources?: Source[] };

export default function HomePage() {
  const [question, setQuestion] = useState("");
  const [country, setCountry] = useState("");
  const [jurisdictionWarning, setJurisdictionWarning] = useState(false);
  const jurisdictions = [
    { value: "US", label: "US Federal" },
    { value: "Alabama", label: "Alabama" },
    { value: "Alaska", label: "Alaska" },
    { value: "Arizona", label: "Arizona" },
    { value: "Arkansas", label: "Arkansas" },
    { value: "California", label: "California" },
    { value: "Colorado", label: "Colorado" },
    { value: "Connecticut", label: "Connecticut" },
    { value: "Delaware", label: "Delaware" },
    { value: "Florida", label: "Florida" },
    { value: "Georgia", label: "Georgia" },
    { value: "Hawaii", label: "Hawaii" },
    { value: "Idaho", label: "Idaho" },
    { value: "Illinois", label: "Illinois" },
    { value: "Indiana", label: "Indiana" },
    { value: "Iowa", label: "Iowa" },
    { value: "Kansas", label: "Kansas" },
    { value: "Kentucky", label: "Kentucky" },
    { value: "Louisiana", label: "Louisiana" },
    { value: "Maine", label: "Maine" },
    { value: "Maryland", label: "Maryland" },
    { value: "Massachusetts", label: "Massachusetts" },
    { value: "Michigan", label: "Michigan" },
    { value: "Minnesota", label: "Minnesota" },
    { value: "Mississippi", label: "Mississippi" },
    { value: "Missouri", label: "Missouri" },
    { value: "Montana", label: "Montana" },
    { value: "Nebraska", label: "Nebraska" },
    { value: "Nevada", label: "Nevada" },
    { value: "New Hampshire", label: "New Hampshire" },
    { value: "New Jersey", label: "New Jersey" },
    { value: "New Mexico", label: "New Mexico" },
    { value: "New York", label: "New York" },
    { value: "North Carolina", label: "North Carolina" },
    { value: "North Dakota", label: "North Dakota" },
    { value: "Ohio", label: "Ohio" },
    { value: "Oklahoma", label: "Oklahoma" },
    { value: "Oregon", label: "Oregon" },
    { value: "Pennsylvania", label: "Pennsylvania" },
    { value: "Rhode Island", label: "Rhode Island" },
    { value: "South Carolina", label: "South Carolina" },
    { value: "South Dakota", label: "South Dakota" },
    { value: "Tennessee", label: "Tennessee" },
    { value: "Texas", label: "Texas" },
    { value: "Utah", label: "Utah" },
    { value: "Vermont", label: "Vermont" },
    { value: "Virginia", label: "Virginia" },
    { value: "Washington", label: "Washington" },
    { value: "West Virginia", label: "West Virginia" },
    { value: "Wisconsin", label: "Wisconsin" },
    { value: "Wyoming", label: "Wyoming" },
  ];
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const stored = sessionStorage.getItem("chat_history");
      return stored ? (JSON.parse(stored) as Message[]) : [];
    } catch {
      return [];
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const streamAbortRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Persist chat history to sessionStorage (cleared automatically when tab closes)
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      sessionStorage.setItem("chat_history", JSON.stringify(messages));
    } catch {
      // sessionStorage full or unavailable — ignore
    }
  }, [messages]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    if (!country) {
      setJurisdictionWarning(true);
      setTimeout(() => setJurisdictionWarning(false), 4000);
      return;
    }

    const userQuestion = question;
    setQuestion("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", content: userQuestion, country }]);
    setLoading(true);

    try {
      const controller = new AbortController();
      streamAbortRef.current = controller;
      const res = await fetch(`${BACKEND_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userQuestion, country: country || null }),
        signal: controller.signal
      });
      
      if (!res.ok) {
        throw new Error(`Backend error: ${res.status} ${res.statusText}`);
      }
      
      if (!res.body) {
        throw new Error("No response body from server");
      }
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let assistant = "";
      let sources: Source[] = [];
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        assistant += chunk;

        // Detect and strip SOURCES_DATA marker appended by the backend
        const markerIdx = assistant.indexOf("\n\nSOURCES_DATA:");
        let displayText = assistant;
        if (markerIdx !== -1) {
          displayText = assistant.slice(0, markerIdx);
          try {
            const jsonStr = assistant.slice(markerIdx + "\n\nSOURCES_DATA:".length);
            sources = JSON.parse(jsonStr) as Source[];
          } catch {
            // incomplete chunk — wait for more data
          }
        }

        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { role: "assistant", content: displayText, sources };
          return copy;
        });
      }
    } catch (err: any) {
      console.error("Chat error:", err);
      if (err.name === 'AbortError') {
        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = {
            role: "assistant",
            content: "Response stopped by user.",
            error: true,
          };
          return copy;
        });
      } else {
        const errorMsg = err.message || "Failed to connect to backend. Please try again.";
        setError(errorMsg);
        setMessages((prev) => [...prev, { 
          role: "assistant", 
          content: `Error: ${errorMsg}`,
          error: true 
        }]);
      }
    } finally {
      setLoading(false);
      streamAbortRef.current = null;
    }
  };

  const stop = () => {
    if (streamAbortRef.current) {
      streamAbortRef.current.abort();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError("");
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("chat_history");
    }
  };

  const renderContent = (content: string, sources?: Source[]) => {
    const citationRegex = /\[(\d+)\]/g;

    const renderInline = (text: string, keyPrefix: string) => {
      const parts = text.split(citationRegex);
      return parts.map((part, i) => {
        if (i % 2 === 1) {
          const num = parseInt(part, 10);
          const source = sources?.find((s) => s.n === num);
          if (source?.url) {
            return (
              <a
                key={`${keyPrefix}-${i}`}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                title={source.citation || source.title || ""}
                className="text-primary font-bold ml-0.5 hover:underline"
              >
                <sup>[{part}]</sup>
              </a>
            );
          }
          return (
            <sup key={`${keyPrefix}-${i}`} className="text-primary font-bold ml-0.5">
              [{part}]
            </sup>
          );
        }
        return <span key={`${keyPrefix}-${i}`}>{part}</span>;
      });
    };

    // Split body from trailing Note: disclaimer
    const noteIdx = content.indexOf(" Note:");
    if (noteIdx !== -1) {
      const body = content.slice(0, noteIdx);
      const note = content.slice(noteIdx);
      return (
        <>
          <span>{renderInline(body, "body")}</span>
          <span className="block mt-3 text-[10px] text-white/40 italic leading-relaxed">
            {renderInline(note, "note")}
          </span>
        </>
      );
    }

    return <span>{renderInline(content, "content")}</span>;
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-x-hidden">
      <div className="fixed inset-0 glow-bg pointer-events-none" />

      {/* Jurisdiction warning popup */}
      {jurisdictionWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60" onClick={() => setJurisdictionWarning(false)} />
          <div className="relative bg-slate-900 border border-green-500/60 rounded-2xl p-6 max-w-sm w-full shadow-2xl text-center animate-in fade-in zoom-in duration-200">
            <span className="material-symbols-outlined text-green-400 text-5xl mb-3 block">
              gavel
            </span>
            <h3 className="text-white font-bold text-lg mb-2">Choose a Jurisdiction First</h3>
            <p className="text-white/70 text-sm mb-5">
              Legal answers vary significantly by location. Please select a jurisdiction — US Federal, your state, or another location — before searching.
            </p>
            <button
              onClick={() => { setJurisdictionWarning(false); document.getElementById("jurisdiction")?.focus(); }}
              className="w-full bg-green-500 hover:bg-green-400 text-slate-900 font-bold py-3 rounded-xl transition-all"
            >
              Select Jurisdiction
            </button>
          </div>
        </div>
      )}
      <main className="w-full max-w-[640px] z-10">
        <header className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/20 text-primary mb-4 border border-primary/30">
            <span className="material-symbols-outlined text-4xl font-light">gavel</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-2">
            <span className="text-white">Legal Search</span>{" "}
            <span className="text-primary">Hub</span>
          </h1>
          <p className="text-white text-sm max-w-xs mx-auto opacity-80">
            Instant answers to legal questions, backed by real US federal law.
          </p>
        </header>

        <div className="glass-card rounded-[2rem] p-5 md:p-8 shadow-2xl">
          {error && (
            <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm flex items-start gap-2">
              <span className="material-symbols-outlined text-lg mt-0.5">error</span>
              <div>
                <div className="font-semibold mb-1">Connection Error</div>
                <div className="opacity-90">{error}</div>
                <div className="text-xs mt-2 opacity-70">
                  Backend URL: {BACKEND_URL}
                </div>
              </div>
            </div>
          )}
          
          <form className="space-y-5" onSubmit={onSubmit}>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-grow space-y-2">
                  <label
                    htmlFor="legal-question"
                    className="block text-xs font-semibold uppercase tracking-wider text-white ml-1"
                  >
                    Legal question
                  </label>
                  <textarea
                    id="legal-question"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Describe the legal situation..."
                    rows={3}
                    className="w-full bg-slate-950/50 border border-slate-800 focus:border-primary focus:ring-1 focus:ring-primary rounded-2xl p-4 text-white placeholder-white/50 resize-none transition-all text-sm custom-scrollbar"
                  />
                </div>
                <div className="md:w-48 space-y-2">
                  <label
                    htmlFor="jurisdiction"
                    className="block text-xs font-semibold uppercase tracking-wider text-white ml-1"
                  >
                    Jurisdiction
                  </label>
                  <div className="relative">
                    <select
                      id="jurisdiction"
                      value={country}
                      onChange={(e) => { setCountry(e.target.value); setJurisdictionWarning(false); }}
                      className={`w-full appearance-none bg-slate-950/50 border rounded-2xl px-4 py-3 text-sm transition-all cursor-pointer focus:ring-1 focus:ring-primary ${
                        !country
                          ? "border-green-500/80 text-green-400 font-semibold uppercase tracking-wider focus:border-green-400"
                          : "border-slate-800 text-white focus:border-primary"
                      }`}
                    >
                      <option value="" disabled className="text-slate-500">
                        Select
                      </option>
                      {jurisdictions.map((j) => (
                        <option key={j.value} className="text-slate-900" value={j.value}>
                          {j.label}
                        </option>
                      ))}
                    </select>
                    <span className={`material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-xl ${!country ? "text-green-400" : "text-white"}`}>
                      unfold_more
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] text-white/70 px-1">
                <span className="material-symbols-outlined text-[14px]">info</span>
                Sensitive identifiers are automatically redacted for security.
              </div>
            </div>
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="w-full bg-primary hover:bg-blue-500 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-2 glow-button transition-all active:scale-[0.98] disabled:opacity-60"
            >
              <span className="material-symbols-outlined font-bold">gavel</span>
              {loading ? "Streaming…" : "Search Legal Hub"}
            </button>

            <div className="pt-2 space-y-3">
              <div className="flex items-center justify-between px-1">
                <span className="text-[10px] font-bold uppercase tracking-widest text-white">
                  Chat History
                </span>
                {messages.length > 0 && (
                  <button
                    type="button"
                    onClick={clearChat}
                    className="text-[10px] text-slate-400 hover:text-white uppercase tracking-wider transition-colors"
                  >
                    Clear
                  </button>
                )}
              </div>
              <div className="w-full min-h-32 max-h-96 overflow-y-auto border border-dashed border-slate-700 rounded-2xl flex flex-col items-start justify-start text-white/40 bg-slate-950/30 p-3 custom-scrollbar">
                {messages.length === 0 ? (
                  <div className="w-full h-28 flex flex-col items-center justify-center">
                    <span className="material-symbols-outlined text-3xl mb-1 opacity-40">
                      find_in_page
                    </span>
                    <p className="text-xs italic opacity-80">Ready for your legal question...</p>
                  </div>
                ) : (
                  <div className="w-full space-y-3 text-sm">
                    {messages.map((m, i) => (
                      <div 
                        key={i} 
                        className={`rounded-lg p-3 ${
                          m.role === "user" 
                            ? "bg-primary/10 border border-primary/30 ml-auto max-w-[85%]" 
                            : m.error
                            ? "bg-red-500/10 border border-red-500/30"
                            : "bg-slate-900/70 border border-slate-800"
                        }`}
                      >
                        <div className="text-[10px] uppercase tracking-wider text-white/60 mb-1.5 flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-xs">
                            {m.role === "user" ? "person" : "gavel"}
                          </span>
                          {m.role === "user" ? "You" : "Legal Search Hub"}
                          {m.country && <span className="opacity-60">· {m.country}</span>}
                        </div>
                        <div className="whitespace-pre-wrap text-white/90 leading-relaxed">
                          {m.error ? m.content : renderContent(m.content, m.sources)}
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>
            </div>
            <footer className="pt-1">
              <p className="text-[9px] text-center text-slate-500 leading-relaxed uppercase tracking-[0.05em]">
                AI-Generated Information. Consult a licensed attorney for official legal advice.
              </p>
            </footer>
          </form>
        </div>

        <nav className="fixed bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-slate-900/90 backdrop-blur-xl border border-white/5 rounded-full px-3 py-2 shadow-2xl">
          <button className="flex items-center justify-center w-11 h-11 rounded-full text-primary bg-primary/10">
            <span className="material-symbols-outlined">search</span>
          </button>
          <button className="flex items-center justify-center w-11 h-11 rounded-full text-slate-500 hover:text-white transition-colors">
            <span className="material-symbols-outlined">description</span>
          </button>
          <button className="flex items-center justify-center w-11 h-11 rounded-full text-slate-500 hover:text-white transition-colors">
            <span className="material-symbols-outlined">history</span>
          </button>
          <button className="flex items-center justify-center w-11 h-11 rounded-full text-slate-500 hover:text-white transition-colors">
            <span className="material-symbols-outlined">person</span>
          </button>
        </nav>
      </main>
    </div>
  );
}

