const BENEFITS = [
  {
    icon: "savings",
    heading: "Save attorney time",
    body: "Get clear answers to basic legal questions without a $300/hour consultation. Understand your situation before you pick up the phone.",
  },
  {
    icon: "verified",
    heading: "See the actual law",
    body: "Every answer links directly to the statute, regulation, or court ruling it came from. No guesses — read the source yourself.",
  },
  {
    icon: "location_on",
    heading: "Your state, your rights",
    body: "Jurisdiction-specific answers for all 50 states and US Federal law. What applies in Texas is not the same as what applies in California.",
  },
  {
    icon: "bolt",
    heading: "Answers in seconds",
    body: "No forms, no waiting rooms, no callbacks. Ask your question and get a cited answer in the time it takes to read this sentence.",
  },
];

export default function BenefitsStrip() {
  return (
    <section className="bg-slate-900 py-20 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-14">
          <p className="text-xs font-bold uppercase tracking-widest text-blue-400 mb-3">
            Why Legal Search Hub
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
            The answer — and the law behind it
          </h2>
          <p className="text-slate-400 text-base max-w-xl mx-auto mt-4 leading-relaxed">
            Most legal tools either give you raw statutes you can&apos;t parse, or AI
            guesses you can&apos;t verify. We give you both: plain English and the
            exact citation.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {BENEFITS.map((b) => (
            <div
              key={b.heading}
              className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6 flex flex-col gap-4"
            >
              <div className="w-11 h-11 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
                <span className="material-symbols-outlined text-blue-400 text-xl">{b.icon}</span>
              </div>
              <div>
                <h3 className="font-bold text-white text-base mb-2">{b.heading}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{b.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
