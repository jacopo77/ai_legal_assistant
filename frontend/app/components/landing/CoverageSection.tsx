const SOURCES = [
  {
    icon: "gavel",
    name: "eCFR",
    description: "Electronic Code of Federal Regulations — all current federal rules and regulations.",
    href: "https://www.ecfr.gov",
  },
  {
    icon: "newspaper",
    name: "Federal Register",
    description: "Official journal of federal rulemaking — proposed rules, final rules, and agency notices.",
    href: "https://www.federalregister.gov",
  },
  {
    icon: "balance",
    name: "CourtListener",
    description: "Free law project database of federal and state court opinions from across the US.",
    href: "https://www.courtlistener.com",
  },
  {
    icon: "account_balance",
    name: "OpenStates",
    description: "State legislature bill and statute search covering all 50 US states in real time.",
    href: "https://openstates.org",
  },
];


export default function CoverageSection() {
  return (
    <section className="bg-slate-50 py-20 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Heading */}
        <div className="text-center mb-14">
          <p className="text-xs font-bold uppercase tracking-widest text-blue-500 mb-3">
            Coverage
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight mb-4">
            All 50 states and US Federal law
          </h2>
          <p className="text-slate-500 text-base max-w-xl mx-auto">
            Every answer cites the specific law, regulation, or ruling — not a
            paraphrase. Click any citation to read the original source.
          </p>
        </div>

        {/* Source cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-5 mb-14">
          {SOURCES.map((src) => (
            <a
              key={src.name}
              href={src.href}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white border border-slate-200 rounded-2xl p-6 flex flex-col gap-3 hover:border-blue-300 hover:shadow-sm transition-all group"
            >
              <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center">
                <span className="material-symbols-outlined text-blue-600 text-xl">{src.icon}</span>
              </div>
              <div>
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="font-bold text-slate-900 text-sm">{src.name}</span>
                  <span className="material-symbols-outlined text-slate-300 group-hover:text-blue-400 transition-colors text-sm">open_in_new</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">{src.description}</p>
              </div>
            </a>
          ))}
        </div>

      </div>
    </section>
  );
}
