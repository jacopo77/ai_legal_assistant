const NOTIFY_EMAIL = "david@legalsearchhub.com";

const FEATURES = [
  "Saved research sessions and history",
  "PDF export with professionally formatted citations",
  "Document upload — ask questions against a specific contract",
  "Audit trail and team access for your firm",
  "Priority support and onboarding",
];

export default function ProTierCTA() {
  const subject = encodeURIComponent("Legal Search Hub — Pro Tier Interest");
  const body = encodeURIComponent(
    "Hi,\n\nI am interested in the Legal Search Hub pro tier for law firms. Please notify me when it launches.\n\nFirm name:\nNumber of attorneys:\nPrimary use case:\n"
  );

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

            <a
              href={`mailto:${NOTIFY_EMAIL}?subject=${subject}&body=${body}`}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 py-4 rounded-2xl transition-all text-sm"
            >
              <span className="material-symbols-outlined text-base">mail</span>
              Notify me when pro launches
            </a>

            <p className="text-xs text-slate-600 mt-4">
              No commitment. Just an email to let you know when it is ready.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
