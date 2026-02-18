UI Improvements Log — Paralegal Assistant
========================================

Design sources
--------------
- Stitch export HTML: `frontend/design/code.html`
- Screenshot (place here): `frontend/public/design/screen.png`
  - If your screenshot isn’t there yet, add it and keep this filename so docs and reviewers have a stable path.

Scope
-----
Track UX/UI refinements for the landing/chat form while keeping parity with the Stitch design (dark theme, glass card, blue accent, floating navbar). These improvements are implementation‑focused and fit our Next.js + Tailwind stack.

Improvements
------------
- Accessibility
  - Associate labels and inputs (ids already present).
  - Add `aria-label`s where helpful and ensure visible `:focus-visible` rings.
  - Maintain ≥4.5:1 contrast on text over glass surfaces.

- Form UX
  - Disable the primary CTA until the textarea has content; show a small inline hint on empty submit.
  - Make jurisdiction a searchable combobox (client‑side filter) for long lists.
  - Keep a prominent “Stop” control while streaming responses.

- Analysis Preview
  - Show a skeleton state during initial load/stream.
  - Render citation chips like `[1] [2]` with hover tooltips (title/URL) once available.

- Visual polish
  - Unify radii: card 24px; inputs/select/CTA 16px; consistent `border-white/10`.
  - CTA gradient and pressed state (`active:translate-y-px`, subtle inner shadow).
  - Slightly reduce blur on mobile for legibility; increase inner padding at `md:`.

- Bottom navbar
  - Respect safe‑area insets; hide/shift when the keyboard is open on mobile.

- Content helpers
  - Add 2–3 example prompt chips above the textarea (client‑side only).
  - Add a tiny latency/model hint under the CTA (e.g., “Streaming ~2–5s”).

- Theming/tokens
  - Extract color/radius/spacing tokens in Tailwind theme for consistency.
  - Default dark; support light fallback without breaking contrast.

- Internationalization
  - Make labels/placeholders translatable; localize jurisdiction options per country later.

- Performance
  - Preload Inter; prefer `font-display: swap`.
  - Reduce heavy blur/backdrop effects for low‑end devices via media query/class.

- Compliance UX
  - Convert the redaction note to an info tooltip with a short “Data handling” modal.
  - Link to a privacy page once available.

Acceptance checks
-----------------
- Matches the screenshot for spacing, radii, and color accents.
- Keyboard/tab navigation is clear; focus rings visible on all controls.
- CTA disabled state and pressed/hover states are obvious.
- Mobile: card stays legible; navbar doesn’t collide with keyboard; safe‑area respected.

Implementation notes
--------------------
- Keep HTML hooks from Stitch:
  - `#legal-question` (textarea), `#jurisdiction` (select)
  - Primary button has `data-role="submit"` in design; functional page may use onSubmit.
- Tailwind utilities live in `app/globals.css` and `tailwind.config.js`.
- Searchable combobox can be implemented with a simple client‑side filter; no extra deps required.

Open questions
--------------
- Final jurisdiction taxonomy (countries vs. states/regions)?
- Exact citation chip behavior (click to open source vs. hover tooltip only)?
- Preferred light‑theme palette if/when enabled?

Changelog
---------
- 2026‑02‑18: Initial pass captured from design review (this document).
