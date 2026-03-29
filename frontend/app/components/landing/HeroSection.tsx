export default function HeroSection() {
  return (
    <section className="bg-white pt-16 pb-12 px-4 text-center">
      <div className="max-w-3xl mx-auto">
        {/* Eyebrow */}
        <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 text-blue-600 text-xs font-semibold uppercase tracking-wider px-4 py-1.5 rounded-full mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse inline-block" />
          Free · No login required · Instant answers
        </div>

        {/* Headline */}
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-900 tracking-tight leading-tight mb-5">
          Know your legal rights{" "}
          <span className="text-blue-600">before you ask a lawyer</span>
        </h1>

        {/* Sub */}
        <p className="text-lg md:text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed mb-10">
          Ask any legal question. Get a plain-English answer with citations to
          the exact law — free, in seconds, no login required.
        </p>

        {/* Trust badges */}
        <div className="flex flex-wrap items-center justify-center gap-3 mb-10">
          {[
            { label: "eCFR", sub: "Federal Regulations" },
            { label: "Federal Register", sub: "Federal Rulemaking" },
            { label: "CourtListener", sub: "Court Opinions" },
            { label: "OpenStates", sub: "State Legislation" },
            { label: "Cornell LII", sub: "US Code" },
          ].map((src) => (
            <div
              key={src.label}
              className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-full px-4 py-2"
            >
              <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
              <span className="text-xs font-semibold text-slate-700">{src.label}</span>
              <span className="text-xs text-slate-400">{src.sub}</span>
            </div>
          ))}
        </div>

        {/* Scroll nudge */}
        <div className="flex flex-col items-center gap-1 text-slate-400">
          <span className="text-xs uppercase tracking-widest font-medium">Search below</span>
          <span className="material-symbols-outlined text-2xl animate-bounce">expand_more</span>
        </div>
      </div>
    </section>
  );
}
