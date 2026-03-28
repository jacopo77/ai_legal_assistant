"use client";

import { useState } from "react";

const FORMSPREE_ENDPOINT = "https://formspree.io/f/mzdkdqlv";

const FEATURES = [
  "Saved research sessions and history",
  "PDF export with professionally formatted citations",
  "Document upload — ask questions against a specific contract",
  "Audit trail and team access for your firm",
  "Priority support and onboarding",
];

export default function ProTierCTA() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setStatus("submitting");
    try {
      const res = await fetch(FORMSPREE_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ email }),
      });
      if (res.ok) {
        setStatus("success");
        setEmail("");
      } else {
        setStatus("error");
      }
    } catch {
      setStatus("error");
    }
  }

  return (
    <section className="bg-white py-20 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-slate-900 rounded-3xl px-8 py-12 md:px-14 md:py-16 text-center relative overflow-hidden">
          {/* Subtle glow */}
          <div className="absolute inset-0 pointer-events-none"
            style={{
              background:
                "radial-gradient(circle at 50% 0%, rgba(37,99,235,0.18) 0%, transparent 60%)",
            }}
          />

          <div className="relative z-10">
            {/* Eyebrow */}
            <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-blue-400 border border-blue-800 bg-blue-950/60 rounded-full px-3 py-1 mb-6">
              Coming soon · For law firms
            </span>

            <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight mb-4">
              Legal research at a fraction of{" "}
              <span className="text-blue-400">Westlaw prices</span>
            </h2>

            <p className="text-slate-400 text-base max-w-xl mx-auto mb-8 leading-relaxed">
              A pro tier built for solo attorneys and small firms (1–5 attorneys) who need real
              legal research capability without a five-figure annual subscription.
            </p>

            {/* Feature list */}
            <ul className="text-left max-w-sm mx-auto space-y-3 mb-10">
              {FEATURES.map((f) => (
                <li key={f} className="flex items-start gap-2.5 text-sm text-slate-300">
                  <span className="material-symbols-outlined text-blue-400 text-base mt-0.5 shrink-0">
                    check_circle
                  </span>
                  {f}
                </li>
              ))}
            </ul>

            {status === "success" ? (
              <div className="flex flex-col items-center gap-2">
                <span className="material-symbols-outlined text-blue-400 text-3xl">check_circle</span>
                <p className="text-white font-semibold text-sm">You&apos;re on the list!</p>
                <p className="text-slate-400 text-xs">We&apos;ll email you when pro launches.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                <input
                  type="email"
                  required
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="flex-1 bg-slate-800 border border-slate-700 focus:border-blue-500 focus:outline-none rounded-2xl px-4 py-3 text-white placeholder-slate-500 text-sm"
                />
                <button
                  type="submit"
                  disabled={status === "submitting"}
                  className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-bold px-6 py-3 rounded-2xl transition-all text-sm whitespace-nowrap"
                >
                  <span className="material-symbols-outlined text-base">mail</span>
                  {status === "submitting" ? "Sending…" : "Notify me"}
                </button>
              </form>
            )}

            {status === "error" && (
              <p className="text-red-400 text-xs mt-3">Something went wrong — please try again.</p>
            )}

            <p className="text-xs text-slate-600 mt-4">
              No commitment. Just an email to let you know when it is ready.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
