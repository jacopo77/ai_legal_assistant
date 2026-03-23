import Link from "next/link";
import { notFound } from "next/navigation";
import { Metadata } from "next";
import faqs from "../../../data/faqs.json";

type Source = {
  n?: number;
  citation?: string | null;
  url?: string;
  title?: string | null;
};

type Faq = {
  slug: string;
  question: string;
  jurisdiction: string;
  category: string;
  answer: string;
  sources: Source[];
};

// Pre-render a static page for every slug at build time
export function generateStaticParams() {
  return (faqs as Faq[]).map((faq) => ({ slug: faq.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const faq = (faqs as Faq[]).find((f) => f.slug === params.slug);
  if (!faq) return {};

  const description = faq.answer
    ? faq.answer.slice(0, 160).replace(/\*\*/g, "")
    : `Cited legal answer to: ${faq.question}`;

  return {
    title: `${faq.question} | Legal Search Hub`,
    description,
    openGraph: {
      title: faq.question,
      description,
      url: `https://legalsearchhub.com/faq/${faq.slug}`,
    },
  };
}

// Render [1] citation markers as links if a matching source exists
function renderAnswer(answer: string, sources: Source[]) {
  const parts = answer.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) {
      const num = parseInt(match[1], 10);
      const src = sources.find((s) => s.n === num || sources.indexOf(s) + 1 === num);
      if (src?.url) {
        return (
          <a
            key={i}
            href={src.url}
            target="_blank"
            rel="noopener noreferrer"
            title={src.citation || src.title || ""}
            className="text-indigo-400 font-bold hover:underline"
          >
            <sup>{part}</sup>
          </a>
        );
      }
      return (
        <sup key={i} className="text-indigo-400 font-bold">
          {part}
        </sup>
      );
    }
    // Render **bold** markdown
    const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
    return boldParts.map((bp, j) => {
      if (bp.startsWith("**") && bp.endsWith("**")) {
        return <strong key={`${i}-${j}`}>{bp.slice(2, -2)}</strong>;
      }
      return bp;
    });
  });
}

export default function FaqDetailPage({ params }: { params: { slug: string } }) {
  const faq = (faqs as Faq[]).find((f) => f.slug === params.slug);
  if (!faq) notFound();

  const categoryFaqs = (faqs as Faq[])
    .filter((f) => f.category === faq.category && f.slug !== faq.slug && f.answer?.trim())
    .slice(0, 4);

  // FAQ Schema JSON-LD — triggers Google rich snippets in search results
  const faqSchema = faq.answer?.trim()
    ? {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: [
          {
            "@type": "Question",
            name: faq.question,
            acceptedAnswer: {
              "@type": "Answer",
              text: faq.answer.replace(/\*\*/g, "").replace(/\[\d+\]/g, ""),
            },
          },
        ],
      }
    : null;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* FAQ Schema for Google */}
      {faqSchema && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
        />
      )}

      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
        <div className="max-w-3xl mx-auto px-4 py-5 flex items-center justify-between">
          <Link
            href="/faq"
            className="flex items-center gap-2 text-white/70 hover:text-white transition-colors text-sm"
          >
            <span className="material-symbols-outlined text-base">arrow_back</span>
            All FAQs
          </Link>
          <span className="text-xs text-slate-500 bg-slate-800 rounded-full px-3 py-1">
            {faq.category}
          </span>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 py-10">
        {/* Jurisdiction badge */}
        {faq.jurisdiction !== "US" && (
          <div className="mb-4">
            <span className="text-xs text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-3 py-1 uppercase tracking-wider">
              {faq.jurisdiction} State Law
            </span>
          </div>
        )}

        {/* Question */}
        <h1 className="text-2xl sm:text-3xl font-bold text-white leading-snug mb-8">
          {faq.question}
        </h1>

        {/* Answer */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 sm:p-8">
          {faq.answer?.trim() ? (
            <>
              <div className="flex items-center gap-2 mb-5">
                <div className="w-7 h-7 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-indigo-400 text-sm">balance</span>
                </div>
                <span className="text-xs text-indigo-300 font-medium uppercase tracking-wider">
                  AI Paralegal Answer
                </span>
              </div>
              <div className="text-white/90 leading-relaxed text-sm whitespace-pre-wrap">
                {renderAnswer(faq.answer, faq.sources)}
              </div>

              {/* Sources */}
              {faq.sources?.length > 0 && (
                <div className="mt-6 pt-5 border-t border-slate-700/50">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-3">
                    Sources
                  </p>
                  <div className="space-y-2">
                    {faq.sources.map((src, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-indigo-400 text-xs font-bold shrink-0 mt-0.5">
                          [{src.n ?? i + 1}]
                        </span>
                        {src.url ? (
                          <a
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-slate-400 hover:text-indigo-300 hover:underline transition-colors break-all"
                          >
                            {src.citation || src.title || src.url}
                          </a>
                        ) : (
                          <span className="text-xs text-slate-400">
                            {src.citation || src.title || "Official source"}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-6">
              <p className="text-slate-400 text-sm mb-4">
                This question hasn&apos;t been answered yet.
              </p>
              <Link
                href={`/?q=${encodeURIComponent(faq.question)}`}
                className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-5 py-2.5 rounded-xl transition-colors"
              >
                <span className="material-symbols-outlined text-base">search</span>
                Ask this question now
              </Link>
            </div>
          )}
        </div>

        {/* Disclaimer */}
        <p className="mt-4 text-[10px] text-slate-600 text-center uppercase tracking-wider">
          AI-Generated Information. Consult a licensed attorney for official legal advice.
        </p>

        {/* CTA */}
        <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-6 py-3 rounded-xl transition-colors"
          >
            <span className="material-symbols-outlined text-base">gavel</span>
            Ask your own legal question
          </Link>
          <Link
            href="/faq"
            className="inline-flex items-center justify-center gap-2 border border-slate-700 hover:border-slate-500 text-white/70 hover:text-white text-sm font-medium px-6 py-3 rounded-xl transition-colors"
          >
            <span className="material-symbols-outlined text-base">list</span>
            Browse all FAQs
          </Link>
        </div>

        {/* Related questions */}
        {categoryFaqs.length > 0 && (
          <div className="mt-12">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Related questions in {faq.category}
            </h2>
            <div className="divide-y divide-slate-800 border border-slate-800 rounded-2xl overflow-hidden">
              {categoryFaqs.map((related) => (
                <Link
                  key={related.slug}
                  href={`/faq/${related.slug}`}
                  className="flex items-center justify-between gap-4 px-5 py-4 bg-slate-900/40 hover:bg-slate-800/60 transition-colors group"
                >
                  <p className="text-sm text-white/80 group-hover:text-white transition-colors">
                    {related.question}
                  </p>
                  <span className="material-symbols-outlined text-slate-600 group-hover:text-slate-400 transition-colors text-base shrink-0">
                    chevron_right
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
