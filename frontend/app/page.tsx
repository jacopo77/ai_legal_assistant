/* eslint-disable @next/next/no-img-element */
"use client";

import { useRef, useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

type Message = { role: "user" | "assistant"; content: string; country?: string };

export default function HomePage() {
  const [question, setQuestion] = useState("");
  const [country, setCountry] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const streamAbortRef = useRef<AbortController | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;
    setMessages((prev) => [...prev, { role: "user", content: question, country }]);
    setLoading(true);

    try {
      const controller = new AbortController();
      streamAbortRef.current = controller;
      const res = await fetch(`${BACKEND_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, country: country || null }),
        signal: controller.signal
      });
      if (!res.ok || !res.body) {
        throw new Error(`Request failed: ${res.status}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let assistant = "";
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        assistant += chunk;
        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { role: "assistant", content: assistant };
          return copy;
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setQuestion("");
      streamAbortRef.current = null;
    }
  };

  const stop = () => {
    if (streamAbortRef.current) {
      streamAbortRef.current.abort();
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-x-hidden">
      <div className="fixed inset-0 glow-bg pointer-events-none" />
      <main className="w-full max-w-[640px] z-10">
        <header className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/20 text-primary mb-4 border border-primary/30">
            <span className="material-symbols-outlined text-4xl font-light">gavel</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-2">
            <span className="text-white">AI Paralegal</span>{" "}
            <span className="text-primary">Assistant</span>
          </h1>
          <p className="text-white text-sm max-w-xs mx-auto opacity-80">
            Legal research and citations optimized for professionals.
          </p>
        </header>

        <div className="glass-card rounded-[2rem] p-5 md:p-8 shadow-2xl">
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
                      onChange={(e) => setCountry(e.target.value)}
                      className="w-full appearance-none bg-slate-950/50 border border-slate-800 focus:border-primary focus:ring-1 focus:ring-primary rounded-2xl px-4 py-3 text-sm text-white transition-all cursor-pointer"
                    >
                      <option className="text-slate-900" value="">
                        Select
                      </option>
                      <option className="text-slate-900" value="US">
                        US Federal
                      </option>
                      <option className="text-slate-900" value="CA-CA">
                        California
                      </option>
                      <option className="text-slate-900" value="US-NY">
                        New York
                      </option>
                      <option className="text-slate-900" value="UK">
                        UK Law
                      </option>
                      <option className="text-slate-900" value="CA">
                        Canada
                      </option>
                    </select>
                    <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-white pointer-events-none text-xl">
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
              {loading ? "Streaming…" : "Ask AI Paralegal"}
            </button>

            <div className="pt-2 space-y-3">
              <div className="flex items-center justify-between px-1">
                <span className="text-[10px] font-bold uppercase tracking-widest text-white">
                  Analysis Preview
                </span>
                <div className="flex gap-1">
                  <span className="h-1 w-4 rounded-full bg-slate-800" />
                  <span className="h-1 w-1 rounded-full bg-slate-800" />
                </div>
              </div>
              <div className="w-full min-h-28 border border-dashed border-slate-700 rounded-2xl flex flex-col items-start justify-start text-white/40 bg-slate-950/30 p-3">
                {messages.length === 0 ? (
                  <div className="w-full h-24 flex flex-col items-center justify-center">
                    <span className="material-symbols-outlined text-3xl mb-1 opacity-40">
                      find_in_page
                    </span>
                    <p className="text-xs italic opacity-80">Ready for inquiry...</p>
                  </div>
                ) : (
                  <div className="space-y-2 text-sm">
                    {messages.map((m, i) => (
                      <div key={i} className="rounded-lg p-2 bg-slate-900/50 border border-slate-800">
                        <div className="text-[10px] uppercase tracking-wider text-white/60 mb-1">
                          {m.role} {m.country ? `· ${m.country}` : ""}
                        </div>
                        <div className="whitespace-pre-wrap text-white/90">{m.content}</div>
                      </div>
                    ))}
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

