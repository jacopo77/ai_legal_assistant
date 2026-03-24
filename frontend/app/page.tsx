/* eslint-disable @next/next/no-img-element */
"use client";

import { useRef, useState, useEffect } from "react";
import AdBanner from "./components/AdBanner";
import HeroSection from "./components/landing/HeroSection";
import HowItWorks from "./components/landing/HowItWorks";
import CoverageSection from "./components/landing/CoverageSection";
import ProTierCTA from "./components/landing/ProTierCTA";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

// Replace these with your actual affiliate tracking links once approved
const LEGALZOOM_URL = "https://www.legalzoom.com/?utm_source=legalsearchhub&utm_medium=referral";
const ROCKETLAWYER_URL = "https://www.rocketlawyer.com/?utm_source=legalsearchhub&utm_medium=referral";

const EXAMPLE_PROMPTS = [
  "Can my employer deny my FMLA leave request?",
  "What are my tenant rights if my landlord won't make repairs in Texas?",
  "Does the ADA require my employer to provide workplace accommodations?",
  "What counts as workplace discrimination under Title VII?",
];

const FAILURE_PATTERNS = [
  "does not specifically address",
  "no relevant snippets",
  "cannot provide a definitive answer",
  "additional information may be needed",
  "i cannot provide",
  "does not provide specific",
  "context does not",
  "not able to provide",
  "unable to provide",
  "no information available",
];

const LANDLORD_TENANT_KEYWORDS = ["landlord", "tenant", "rent", "eviction", "evict", "lease", "habitability", "repair", "heat", "hot water", "deposit", "security deposit"];
const BUSINESS_KEYWORDS = ["llc", "corporation", "incorporate", "business formation", "form a business", "start a business", "articles of incorporation"];
const SUPPORTED_STATES = ["Texas", "California", "Florida", "New York"];

function isFailureResponse(content: string): boolean {
  const lower = content.toLowerCase();
  return FAILURE_PATTERNS.some((p) => lower.includes(p));
}

function getGuidance(question: string, jurisdiction: string): { heading: string; message: string; retryQuestion?: string } {
  const lower = question.toLowerCase();
  const isLandlordTenant = LANDLORD_TENANT_KEYWORDS.some((kw) => lower.includes(kw));
  const isBusiness = BUSINESS_KEYWORDS.some((kw) => lower.includes(kw));
  const isStateTopicUnderFederal = jurisdiction === "US" && (isLandlordTenant || isBusiness);

  if (isStateTopicUnderFederal && isLandlordTenant) {
    return {
      heading: "This is a state law question",
      message: "Landlord-tenant rights — repairs, habitability, eviction — are governed by state law, not federal law. This app has full coverage for Texas, California, Florida, and New York.",
      retryQuestion: question,
    };
  }
  if (isStateTopicUnderFederal && isBusiness) {
    return {
      heading: "This is a state law question",
      message: "Business formation (LLC, corporation) is handled at the state level. This app has coverage for Texas, California, Florida, and New York.",
      retryQuestion: question,
    };
  }
  if (SUPPORTED_STATES.includes(jurisdiction) && !isLandlordTenant && !isBusiness) {
    return {
      heading: "Try US Federal for this topic",
      message: "State coverage is focused on landlord-tenant rights and business formation. For employment, civil rights, ADA, FMLA, or Title VII questions, select US Federal as your jurisdiction.",
      retryQuestion: question,
    };
  }
  return {
    heading: "Try rephrasing your question",
    message: "This app covers US employment law (FMLA, ADA, FLSA, Title VII, OSHA), civil rights (Section 1983, Fair Housing Act), and landlord-tenant and business formation law for Texas, California, Florida, and New York. Try adding more detail — your role, the specific law, and what outcome you need.",
  };
}

function exportToPDF(content: string, question: string, sources?: Source[], jurisdiction?: string): void {
  const sourcesHtml = sources && sources.length > 0
    ? `<div class="sources"><strong>Sources</strong><ol>${sources.map(s =>
        `<li><a href="${s.url}" target="_blank">${s.citation || s.title || s.url}</a></li>`
      ).join("")}</ol></div>`
    : "";
  const cleanContent = content
    .replace(/\[(\d+)\]/g, "<sup>[$1]</sup>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>");
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Legal Research — Legal Search Hub</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Georgia, serif; font-size: 13px; line-height: 1.75; color: #1a1a1a; padding: 48px 56px; max-width: 720px; margin: 0 auto; }
    h1 { font-size: 20px; color: #0f2d5c; margin-bottom: 6px; }
    .meta { font-size: 11px; color: #666; border-bottom: 1px solid #ddd; padding-bottom: 12px; margin-bottom: 20px; }
    .question { background: #f0f4ff; border-left: 3px solid #2563eb; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px; font-size: 13px; }
    .answer p { margin-bottom: 12px; }
    sup { font-size: 10px; color: #2563eb; }
    .sources { margin-top: 24px; font-size: 11px; color: #444; border-top: 1px solid #eee; padding-top: 16px; }
    .sources ol { padding-left: 20px; margin-top: 8px; }
    .sources li { margin-bottom: 6px; }
    .sources a { color: #2563eb; }
    .footer { margin-top: 32px; font-size: 10px; color: #999; border-top: 1px solid #eee; padding-top: 12px; }
  </style>
</head>
<body>
  <h1>Legal Research Summary</h1>
  <div class="meta">Legal Search Hub &nbsp;|&nbsp; Jurisdiction: ${jurisdiction || "US Federal"} &nbsp;|&nbsp; ${new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</div>
  ${question ? `<div class="question"><strong>Question:</strong> ${question}</div>` : ""}
  <div class="answer"><p>${cleanContent}</p></div>
  ${sourcesHtml}
  <div class="footer">AI-Generated Information. This is not legal advice. Consult a licensed attorney for guidance specific to your situation. &nbsp;|&nbsp; legalsearchhub.com</div>
  <script>window.onload = function() { window.print(); }</script>
</body>
</html>`;
  const win = window.open("", "_blank", "width=820,height=640");
  if (win) { win.document.write(html); win.document.close(); }
}

function emailSummary(question: string, content: string, sources?: Source[], jurisdiction?: string): void {
  const sourcesText = sources && sources.length > 0
    ? "\n\nSources:\n" + sources.map(s => `- ${s.citation || s.title || s.url}: ${s.url}`).join("\n")
    : "";
  const body = `Legal Research Summary — Legal Search Hub\n\nQuestion: ${question || "(not specified)"}\nJurisdiction: ${jurisdiction || "US Federal"}\nDate: ${new Date().toLocaleDateString()}\n\n---\n\n${content}${sourcesText}\n\n---\nAI-Generated Information. This is not legal advice. Consult a licensed attorney.\nlegalsearchhub.com`;
  window.location.href = `mailto:?subject=Legal Research - Legal Search Hub&body=${encodeURIComponent(body)}`;
}

type Source = { n: number; citation: string | null; url: string; title: string | null };
type Message = { role: "user" | "assistant"; content: string; country?: string; error?: boolean; sources?: Source[] };

export default function HomePage() {
  const [question, setQuestion] = useState("");
  const [country, setCountry] = useState("");
  const [jurisdictionWarning, setJurisdictionWarning] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

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
    } catch { return []; }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const streamAbortRef = useRef<AbortController | null>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const chatSectionRef = useRef<HTMLElement>(null);
  const didPageScrollRef = useRef(false);

  // Detect shared URL params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    const j = params.get("j");
    if (q) setQuestion(decodeURIComponent(q));
    if (j) setCountry(decodeURIComponent(j));
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try { sessionStorage.setItem("chat_history", JSON.stringify(messages)); } catch { /* ignore */ }
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0) {
      didPageScrollRef.current = false;
      return;
    }
    // Once per question: scroll the page so the dark section is at the top.
    if (!didPageScrollRef.current && chatSectionRef.current) {
      didPageScrollRef.current = true;
      const top = chatSectionRef.current.getBoundingClientRect().top + window.pageYOffset;
      window.scrollTo({ top, behavior: "smooth" });
    }
    // Always: scroll inside the container to follow the latest content
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleShare = (question: string, jurisdiction: string, idx: number) => {
    const url = `${window.location.origin}/?q=${encodeURIComponent(question)}&j=${encodeURIComponent(jurisdiction)}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    }).catch(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    });
  };

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
    didPageScrollRef.current = false;
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

      if (!res.ok) throw new Error(`Backend error: ${res.status} ${res.statusText}`);
      if (!res.body) throw new Error("No response body from server");

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

        const markerIdx = assistant.indexOf("\n\nSOURCES_DATA:");
        let displayText = assistant;
        if (markerIdx !== -1) {
          displayText = assistant.slice(0, markerIdx);
          try {
            const jsonStr = assistant.slice(markerIdx + "\n\nSOURCES_DATA:".length);
            sources = JSON.parse(jsonStr) as Source[];
          } catch { /* incomplete chunk */ }
        }

        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { role: "assistant", content: displayText, sources };
          return copy;
        });
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { role: "assistant", content: "Response stopped by user.", error: true };
          return copy;
        });
      } else {
        const errorMsg = err.message || "Failed to connect to backend. Please try again.";
        setError(errorMsg);
        setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${errorMsg}`, error: true }]);
      }
    } finally {
      setLoading(false);
      streamAbortRef.current = null;
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError("");
    if (typeof window !== "undefined") sessionStorage.removeItem("chat_history");
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
              <a key={`${keyPrefix}-${i}`} href={source.url} target="_blank" rel="noopener noreferrer"
                title={source.citation || source.title || ""} className="text-primary font-bold ml-0.5 hover:underline">
                <sup>[{part}]</sup>
              </a>
            );
          }
          return <sup key={`${keyPrefix}-${i}`} className="text-primary font-bold ml-0.5">[{part}]</sup>;
        }
        return <span key={`${keyPrefix}-${i}`}>{part}</span>;
      });
    };

    const noteIdx = content.indexOf(" Note:");
    if (noteIdx !== -1) {
      const body = content.slice(0, noteIdx);
      const note = content.slice(noteIdx);
      return (
        <>
          <span>{renderInline(body, "body")}</span>
          <span className="block mt-3 text-[10px] text-white/40 italic leading-relaxed">{renderInline(note, "note")}</span>
        </>
      );
    }
    return <span>{renderInline(content, "content")}</span>;
  };

  return (
    <>
      {/* Jurisdiction warning popup — fixed overlay, works across all sections */}
      {jurisdictionWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60" onClick={() => setJurisdictionWarning(false)} />
          <div className="relative bg-slate-900 border border-green-500/60 rounded-2xl p-6 max-w-sm w-full shadow-2xl text-center">
            <span className="material-symbols-outlined text-green-400 text-5xl mb-3 block">gavel</span>
            <h3 className="text-white font-bold text-lg mb-2">Choose a Jurisdiction First</h3>
            <p className="text-white/70 text-sm mb-5">
              Legal answers vary significantly by location. Please select a jurisdiction — US Federal, your state, or another location — before searching.
            </p>
            <button onClick={() => { setJurisdictionWarning(false); document.getElementById("jurisdiction")?.focus(); }}
              className="w-full bg-green-500 hover:bg-green-400 text-slate-900 font-bold py-3 rounded-xl transition-all">
              Select Jurisdiction
            </button>
          </div>
        </div>
      )}

      {/* White hero landing section */}
      <HeroSection />

      {/* Dark chat tool section */}
      <section ref={chatSectionRef} className="bg-[#0B0E14] py-14 px-4 relative overflow-hidden">
        <div className="absolute inset-0 glow-bg pointer-events-none" />
        <div className="relative z-10 w-full max-w-[760px] mx-auto">

          {/* Section label */}
          <div className="text-center mb-8">
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-1">
              Legal Search Hub
            </p>
            <p className="text-white/50 text-xs">
              Select a jurisdiction, then ask your question
            </p>
          </div>

          {/* Search card */}
          <div className="glass-card rounded-[2rem] p-5 md:p-8 shadow-2xl">
            {error && (
              <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm flex items-start gap-2">
                <span className="material-symbols-outlined text-lg mt-0.5">error</span>
                <div>
                  <div className="font-semibold mb-1">Connection Error</div>
                  <div className="opacity-90">{error}</div>
                </div>
              </div>
            )}

            <form className="space-y-5" onSubmit={onSubmit}>
              <div className="flex flex-col gap-4">
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-grow space-y-2">
                    <label htmlFor="legal-question" className="block text-xs font-semibold uppercase tracking-wider text-white/80 ml-1">
                      Legal Question
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
                    <label htmlFor="jurisdiction" className="block text-xs font-semibold uppercase tracking-wider text-white/80 ml-1">
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
                        <option value="" disabled className="text-slate-500">Select</option>
                        {jurisdictions.map((j) => (
                          <option key={j.value} className="text-slate-900" value={j.value}>{j.label}</option>
                        ))}
                      </select>
                      <span className={`material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-xl ${!country ? "text-green-400" : "text-white"}`}>
                        expand_more
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 text-[10px] text-white/60 px-1">
                  <span className="material-symbols-outlined text-[14px]">lock</span>
                  Personal sensitive details are automatically removed to protect your privacy.
                </div>
              </div>
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="w-full bg-primary hover:bg-blue-500 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-2 glow-button transition-all active:scale-[0.98] disabled:opacity-60"
              >
                <span className="material-symbols-outlined font-bold">gavel</span>
                {loading ? "Searching…" : "Search Legal Hub"}
              </button>
            </form>
          </div>

          {/* AdSense banner — only renders when NEXT_PUBLIC_ADSENSE_CLIENT_ID is set */}
          <AdBanner />

          {/* Results / empty state — fixed height container scrolls internally, page never moves */}
          <div ref={messagesContainerRef} className="mt-4 max-h-[60vh] overflow-y-auto custom-scrollbar">
            {messages.length === 0 ? (
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 text-center mb-3">
                  Try a sample prompt
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {EXAMPLE_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => setQuestion(prompt)}
                      className="text-left text-sm text-white/60 hover:text-white bg-slate-900/40 hover:bg-slate-800/60 border border-slate-800 hover:border-slate-600 rounded-2xl px-4 py-3 transition-all leading-snug"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between px-1 mb-4">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-white/30">Results</span>
                  <button type="button" onClick={clearChat} className="text-[10px] text-slate-500 hover:text-white uppercase tracking-wider transition-colors">
                    Clear
                  </button>
                </div>
                <div className="space-y-4">
                  {messages.map((m, i) => {
                    const prevMessage = i > 0 ? messages[i - 1] : null;
                    const showGuidance =
                      m.role === "assistant" && !m.error &&
                      isFailureResponse(m.content) && prevMessage?.role === "user";
                    const guidance = showGuidance
                      ? getGuidance(prevMessage!.content, prevMessage!.country || "")
                      : null;
                    const isCompletedAnswer = m.role === "assistant" && !m.error && m.content.length > 40 && (!loading || i < messages.length - 1);
                    const userMsg = m.role === "assistant" && prevMessage?.role === "user" ? prevMessage : null;

                    return (
                      <div key={i} className="space-y-2">
                        <div
                          className={`rounded-2xl p-4 md:p-5 ${
                            m.role === "user"
                              ? "glass-card border border-primary/20 ml-8"
                              : m.error
                              ? "bg-red-500/10 border border-red-500/30"
                              : "glass-card border border-slate-700/60"
                          }`}
                        >
                          <div className="text-[10px] uppercase tracking-wider text-white/50 mb-2 flex items-center gap-1.5">
                            <span className="material-symbols-outlined text-xs">
                              {m.role === "user" ? "person" : "gavel"}
                            </span>
                            {m.role === "user" ? "You" : "Legal Search Hub"}
                            {m.country && <span className="opacity-60">· {m.country}</span>}
                          </div>
                          <div className="text-sm text-white/90 leading-relaxed whitespace-pre-wrap">
                            {m.error ? m.content : renderContent(m.content, m.sources)}
                          </div>
                        </div>

                        {/* Guidance card with affiliate CTAs */}
                        {guidance && (
                          <div className="rounded-2xl p-4 md:p-5 bg-amber-500/8 border border-amber-500/30">
                            <div className="flex items-start gap-3">
                              <span className="material-symbols-outlined text-amber-400 text-xl mt-0.5 shrink-0">lightbulb</span>
                              <div className="flex-1 min-w-0">
                                <p className="text-amber-300 font-semibold text-sm mb-1">{guidance.heading}</p>
                                <p className="text-white/70 text-sm leading-relaxed">{guidance.message}</p>
                                {guidance.retryQuestion && (
                                  <button
                                    type="button"
                                    onClick={() => setQuestion(guidance.retryQuestion!)}
                                    className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-amber-300 hover:text-amber-200 uppercase tracking-wider transition-colors"
                                  >
                                    <span className="material-symbols-outlined text-sm">edit</span>
                                    Re-enter this question with a new jurisdiction
                                  </button>
                                )}
                                {/* Affiliate CTAs */}
                                <div className="mt-4 pt-3 border-t border-amber-500/20">
                                  <p className="text-[10px] uppercase tracking-wider text-white/30 mb-2">Get professional help</p>
                                  <div className="flex flex-col sm:flex-row gap-2">
                                    <a
                                      href={LEGALZOOM_URL}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="flex items-center gap-1.5 text-xs text-white/50 hover:text-white border border-slate-700 hover:border-slate-500 rounded-xl px-3 py-2 transition-all"
                                    >
                                      <span className="material-symbols-outlined text-sm">open_in_new</span>
                                      LegalZoom — Online legal services
                                    </a>
                                    <a
                                      href={ROCKETLAWYER_URL}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="flex items-center gap-1.5 text-xs text-white/50 hover:text-white border border-slate-700 hover:border-slate-500 rounded-xl px-3 py-2 transition-all"
                                    >
                                      <span className="material-symbols-outlined text-sm">open_in_new</span>
                                      RocketLawyer — Attorney consultations
                                    </a>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* White / light landing sections below the tool */}
      <HowItWorks />
      <CoverageSection />
      <ProTierCTA />
      <FaqPreview />

      {/* Site footer */}
      <footer className="bg-slate-50 border-t border-slate-200 py-10 px-4 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-center gap-2 mb-3">
            <span className="material-symbols-outlined text-blue-600 text-lg">gavel</span>
            <span className="font-bold text-slate-800 text-sm">Legal Search Hub</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed max-w-lg mx-auto mb-4">
            AI-generated information only. This is not legal advice. Always consult a licensed
            attorney for guidance specific to your situation.
          </p>
          <div className="flex items-center justify-center gap-5 text-xs text-slate-400">
            <a href="/faq" className="hover:text-blue-600 transition-colors">FAQ</a>
            <span>·</span>
            <span>legalsearchhub.com</span>
            <span>·</span>
            <span>© {new Date().getFullYear()}</span>
          </div>
        </div>
      </footer>
    </>
  );
}

function FaqPreview() {
  const [open, setOpen] = useState(false);

  const PREVIEW_QUESTIONS = [
    { slug: "can-my-landlord-enter-without-permission", question: "Can my landlord enter without permission?" },
    { slug: "can-i-be-fired-without-warning-for-no-reason", question: "Can I be fired without warning / for no reason?" },
    { slug: "what-is-minimum-wage", question: "What is minimum wage?" },
    { slug: "can-my-landlord-evict-me-without-going-to-court", question: "Can my landlord evict me without going to court?" },
    { slug: "how-to-get-paid-while-on-fmla", question: "How to get paid while on FMLA" },
    { slug: "what-can-my-landlord-keep-my-security-deposit-for", question: "What can my landlord keep my security deposit for?" },
    { slug: "is-my-employer-required-to-give-me-breaks-or-lunch", question: "Is my employer required to give me breaks or lunch?" },
    { slug: "how-to-trademark-a-name", question: "How to trademark a name" },
  ];

  return (
    <section className="bg-white py-16 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="border border-slate-200 rounded-2xl overflow-hidden">
          <button
            onClick={() => setOpen((v) => !v)}
            className="w-full flex items-center justify-between px-6 py-5 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors group"
            aria-expanded={open}
          >
            <span className="flex items-center gap-2 text-sm font-semibold">
              <span className="material-symbols-outlined text-blue-500 text-base">quiz</span>
              Frequently Asked Legal Questions
            </span>
            <span className={`material-symbols-outlined text-base text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}>
              expand_more
            </span>
          </button>

          {open && (
            <div className="border-t border-slate-200 divide-y divide-slate-100">
              {PREVIEW_QUESTIONS.map((q) => (
                <a
                  key={q.slug}
                  href={`/faq/${q.slug}`}
                  className="flex items-center justify-between gap-3 px-6 py-4 text-sm text-slate-600 hover:text-blue-600 hover:bg-blue-50/50 transition-all group"
                >
                  <span>{q.question}</span>
                  <span className="material-symbols-outlined text-slate-300 group-hover:text-blue-400 transition-colors text-base shrink-0">
                    chevron_right
                  </span>
                </a>
              ))}
              <div className="px-6 py-4 bg-slate-50">
                <a
                  href="/faq"
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:text-blue-500 transition-colors"
                >
                  View all frequently asked legal questions
                  <span className="material-symbols-outlined text-base">arrow_forward</span>
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
