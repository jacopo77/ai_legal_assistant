# Stitch Prompt (canonical)

System: You are Stitch, an assistant constrained to provide citation-backed legal information. Always cite sources inline as [1], [2], etc. Do not provide legal advice — provide informational responses and recommend consulting a licensed attorney for authoritative guidance. When jurisdiction is supplied, prioritize jurisdiction-specific sources. Include a short "Sources" section with full references and timestamps.

User: {user_question}

Assistant: Answer stepwise: (1) short summary, (2) key points, (3) relevant statutes/cases, (4) sources list.

Stitch Design Prompt — Paralegal Assistant
=========================================

Goal
----
Design a dark, modern, clean landing/chat form for a legal AI assistant. The UI captures:
- Legal question (multiline textarea)
- Jurisdiction (country/region selector)
- Primary CTA button to submit

The design should closely match the attached mock (hero icon, title with blue accent, glass card, rounded corners, subtle glow background, small legal disclaimer).

Implementation constraints
-------------------------
- Use Tailwind CSS classes (we’ll integrate into a Next.js app).
- Typography: Inter.
- Icons: Material Symbols (Outlined).
- Responsive up to ~640px content width; center layout.
- Do not add features beyond what’s listed (no file upload, no chat history yet).
- Provide stable element IDs/attributes so our app can wire behavior:
  - `#legal-question` (textarea)
  - `#jurisdiction` (select)
  - `data-role="submit"` on the primary button (we’ll attach a handler)
- The form should not perform a real submit; leave JS behavior to us.

Visual requirements
-------------------
- Background: deep navy/black with radial glow accents.
- Card: subtle glass effect with blur; rounded (24px+), thin border, shadow.
- Button: vibrant blue primary with glow; rounded (16px+).
- Labels: small uppercase, semibold; inputs with soft borders and focus ring.
- Include a small “Sensitive identifiers are automatically redacted...” note.
- Include an “Analysis Preview” box placeholder below the CTA.
- Footer: tiny uppercase disclaimer centered.
- Bottom navbar (floating pill with 4 icons) as in mock; non-functional for now.

Layout skeleton (reference only)
--------------------------------
- Hero: gavel icon in a rounded square → title “AI Paralegal Assistant” → short subtitle.
- Main card with form:
  - Label + textarea (`#legal-question`)
  - Label + select (`#jurisdiction`) with sample options:
    - US Federal, California, New York, UK Law, Canada
  - Info row (redaction note)
  - Primary CTA (data-role="submit")
  - “Analysis Preview” placeholder box
  - Disclaimer footer
- Floating bottom navbar with 4 circular icon buttons.

Hand‑off notes
--------------
- Export a single HTML file that uses Tailwind classes.
- If using the CDN in the export, that’s fine; we’ll port classes into our Next.js Tailwind setup.
- Keep class names semantic and consistent; no inlined JS for submit.
- Ensure dark mode is default (add `class="dark"` on `html` if needed).

Success criteria
----------------
- Pixel‑close to the provided mock (spacing, radii, colors).
- Clean Tailwind utility composition; accessible color contrast.
- Works on desktop and small mobile widths.

