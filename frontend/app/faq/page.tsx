import Link from "next/link";
import { Metadata } from "next";
import faqs from "../../data/faqs.json";

export const metadata: Metadata = {
  title: "Frequently Asked Legal Questions | Legal Search Hub",
  description:
    "Instant answers to the most commonly asked legal questions — tenant rights, employment law, federal regulations, and small business law — cited from official US government sources.",
  openGraph: {
    title: "Frequently Asked Legal Questions | Legal Search Hub",
    description:
      "Get cited answers to common legal questions on tenant rights, employment, federal regulations, and small business law.",
    url: "https://legalsearchhub.com/faq",
  },
};

const CATEGORY_ORDER = [
  "Tenant & Landlord",
  "Employment Law",
  "Criminal & Traffic Law",
  "Family Law",
  "Business & IP",
  "General Legal",
  "Federal Regulations",
  "Small Business",
];

const CATEGORY_ICONS: Record<string, string> = {
  "Tenant & Landlord": "home",
  "Employment Law": "work",
  "Criminal & Traffic Law": "local_police",
  "Family Law": "family_restroom",
  "Business & IP": "lightbulb",
  "General Legal": "gavel",
  "Federal Regulations": "account_balance",
  "Small Business": "storefront",
};

type Faq = {
  slug: string;
  question: string;
  jurisdiction: string;
  category: string;
  answer: string;
  sources: { citation?: string; url?: string; title?: string }[];
};

export default function FaqIndexPage() {
  const grouped: Record<string, Faq[]> = {};
  for (const faq of faqs as Faq[]) {
    if (!grouped[faq.category]) grouped[faq.category] = [];
    grouped[faq.category].push(faq);
  }

  const totalAnswered = (faqs as Faq[]).filter((f) => f.answer?.trim()).length;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
        <div className="max-w-4xl mx-auto px-4 py-5 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-white/70 hover:text-white transition-colors text-sm">
            <span className="material-symbols-outlined text-base">arrow_back</span>
            Back to Legal Search Hub
          </Link>
          <span className="text-xs text-slate-500">{totalAnswered} answered questions</span>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 py-12">
        {/* Hero */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 text-xs text-indigo-300 mb-5">
            <span className="material-symbols-outlined text-sm">verified</span>
            Cited from official US government sources
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Frequently Asked Legal Questions
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto text-sm leading-relaxed">
            Answers to the most commonly asked legal questions, backed by real citations from
            federal regulations, US court opinions, and official government sources.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 mt-6 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-5 py-2.5 rounded-xl transition-colors"
          >
            <span className="material-symbols-outlined text-base">search</span>
            Ask your own legal question
          </Link>
        </div>

        {/* Category sections */}
        <div className="space-y-10">
          {CATEGORY_ORDER.map((category) => {
            const items = grouped[category];
            if (!items?.length) return null;
            const icon = CATEGORY_ICONS[category] || "gavel";

            return (
              <section key={category}>
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-indigo-400">{icon}</span>
                  <h2 className="text-lg font-semibold text-white">{category}</h2>
                  <span className="ml-auto text-xs text-slate-500">{items.length} questions</span>
                </div>
                <div className="divide-y divide-slate-800 border border-slate-800 rounded-2xl overflow-hidden">
                  {items.map((faq) => (
                    <Link
                      key={faq.slug}
                      href={`/faq/${faq.slug}`}
                      className="flex items-center justify-between gap-4 px-5 py-4 bg-slate-900/40 hover:bg-slate-800/60 transition-colors group"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white/90 group-hover:text-white transition-colors leading-snug">
                          {faq.question}
                        </p>
                        {faq.jurisdiction !== "US" && (
                          <span className="inline-block mt-1 text-[10px] text-indigo-400/70 uppercase tracking-wider">
                            {faq.jurisdiction}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {faq.answer?.trim() ? (
                          <span className="text-[10px] text-emerald-400/70 uppercase tracking-wider hidden sm:block">
                            Answered
                          </span>
                        ) : null}
                        <span className="material-symbols-outlined text-slate-600 group-hover:text-slate-400 transition-colors text-base">
                          chevron_right
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <div className="mt-14 text-center border border-slate-800 rounded-2xl p-8 bg-slate-900/30">
          <p className="text-slate-400 text-sm mb-4">
            Don&apos;t see your question? Ask the AI Paralegal directly.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-6 py-3 rounded-xl transition-colors"
          >
            <span className="material-symbols-outlined text-base">gavel</span>
            Ask a Legal Question
          </Link>
          <p className="mt-5 text-[10px] text-slate-600 uppercase tracking-wider">
            AI-Generated Information. Consult a licensed attorney for official legal advice.
          </p>
        </div>
      </main>
    </div>
  );
}
