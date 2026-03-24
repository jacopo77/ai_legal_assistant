const STEPS = [
  {
    icon: "edit_note",
    number: "01",
    heading: "Ask your question",
    body: "Type your legal situation in plain English and select your jurisdiction — US Federal or any of the 50 states.",
  },
  {
    icon: "travel_explore",
    number: "02",
    heading: "Live source search",
    body: "The AI searches current federal regulations and court opinions in real time — not a static knowledge base.",
  },
  {
    icon: "fact_check",
    number: "03",
    heading: "Cited answer",
    body: "You get a plain-English answer with numbered citations that link directly to the original law or ruling.",
  },
];

export default function HowItWorks() {
  return (
    <section className="bg-white py-20 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Heading */}
        <div className="text-center mb-14">
          <p className="text-xs font-bold uppercase tracking-widest text-blue-500 mb-3">
            How it works
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
            From question to cited answer in seconds
          </h2>
        </div>

        {/* Steps */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {STEPS.map((step) => (
            <div key={step.number} className="relative flex flex-col items-start">
              {/* Step number */}
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-300 mb-4">
                {step.number}
              </span>
              {/* Icon */}
              <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-5">
                <span className="material-symbols-outlined text-blue-600 text-2xl">
                  {step.icon}
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">{step.heading}</h3>
              <p className="text-slate-500 text-sm leading-relaxed">{step.body}</p>
            </div>
          ))}
        </div>

        {/* Divider note */}
        <p className="text-center text-xs text-slate-400 mt-14">
          AI-generated information. Always consult a licensed attorney for advice specific to your situation.
        </p>
      </div>
    </section>
  );
}
