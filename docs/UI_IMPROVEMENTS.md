# UI Improvements — AI Paralegal Assistant

## Current Status
- ✅ Basic streaming chat interface with dark theme
- ✅ Question input + jurisdiction field
- ✅ Real-time streaming responses
- ⚠️ Minimal styling, needs Stitch design implementation

---

## Priority Improvements

### 🔥 Critical (Do First)

**1. Implement Stitch Design System**
- Apply glass morphism card with `backdrop-blur-xl` and `bg-white/5` border
- Use 24px rounded corners for main card, 16px for inputs/buttons
- Add gradient primary button: `bg-gradient-to-r from-blue-600 to-blue-500`
- Ensure proper contrast ratios (≥4.5:1) for accessibility

**2. Enhanced Form UX**
- Disable submit button until question has content
- Show inline validation hint: "Please enter a question"
- Add loading state with animated spinner during streaming
- Add "Stop Generation" button that appears while streaming

**3. Citation Display**
- Render inline citations as clickable chips: `[1]`, `[2]`
- Show tooltip on hover with source title and URL
- Parse markdown-style citations from streamed response
- Make citations stand out visually with subtle background color

**4. Jurisdiction Selector**
- Replace text input with searchable dropdown (combobox)
- Pre-populate with common jurisdictions: US Federal, California, New York, Canada, UK, etc.
- Add search/filter functionality for long lists
- Allow custom jurisdiction entry as fallback

---

### 🎯 High Priority (Do Next)

**5. Response Display Enhancement**
- Add skeleton loader animation while waiting for first stream chunk
- Format response with proper typography (headings, lists, paragraphs)
- Add copy-to-clipboard button for full response
- Show streaming indicator (animated dots or pulse)

**6. Example Prompts**
- Display 3 sample question chips above textarea:
  - "What are the requirements for forming an LLC in California?"
  - "Can an employer require vaccination proof in New York?"
  - "What is the statute of limitations for breach of contract?"
- Click to populate question field

**7. Mobile Optimization**
- Reduce backdrop blur on mobile for better performance
- Ensure bottom navbar respects safe-area insets
- Handle keyboard overlay gracefully (shift content up)
- Touch-friendly button sizes (min 44x44px)

---

### 💎 Polish (Nice to Have)

**8. Visual Refinements**
- Add subtle hover states on all interactive elements
- Implement pressed state: `active:translate-y-px active:shadow-inner`
- Smooth transitions on all state changes (200ms ease)
- Add floating navbar with logo and minimal nav items

**9. User Feedback**
- Show response latency hint: "Typically responds in 2-5 seconds"
- Add confidence indicator if backend provides it
- Toast notifications for errors (instead of inline text)
- Success confirmation when response completes

**10. Advanced Features**
- Save question history (localStorage)
- Export response as PDF or formatted text
- Share response via unique URL
- Dark/light theme toggle (currently dark only)

---

## Implementation Guidelines

### Design Tokens (Tailwind Config)
```js
colors: {
  glass: 'rgba(255, 255, 255, 0.05)',
  'glass-border': 'rgba(255, 255, 255, 0.1)',
  primary: '#3B82F6',
  'primary-dark': '#2563EB',
}
borderRadius: {
  'card': '24px',
  'input': '16px',
}
```

### Accessibility Checklist
- ✅ All inputs have associated labels with proper `htmlFor`
- ✅ Focus rings visible on all interactive elements
- ✅ Keyboard navigation works throughout
- ✅ Screen reader announcements for streaming updates
- ✅ ARIA labels on icon-only buttons

### Performance Considerations
- Use `font-display: swap` for custom fonts
- Lazy load heavy components below the fold
- Debounce jurisdiction search by 300ms
- Consider virtual scrolling for very long responses

---

## Out of Scope (Remove These)

❌ **Internationalization** - Not needed for MVP; focus on English-speaking jurisdictions first
❌ **Light theme** - Stick with dark theme only to reduce complexity
❌ **Comprehensive theming system** - Use Tailwind utilities directly; don't over-engineer
❌ **Heavy blur reduction media query** - Modern devices handle this fine; premature optimization
❌ **Privacy modal/data handling tooltip** - Add when legal review is complete, not in UI phase

---

## Acceptance Criteria

**MVP Launch Ready When:**
- [ ] Matches Stitch design visually (glass card, proper spacing, colors)
- [ ] Submit button disabled when empty, with clear visual feedback
- [ ] Citations are clickable and show source information
- [ ] Jurisdiction dropdown with 10+ common options + search
- [ ] Mobile-responsive with working keyboard handling
- [ ] Streaming indicator shows while generating response
- [ ] Example prompts populate question field on click
- [ ] All interactive elements have hover/focus states
- [ ] Keyboard navigation works perfectly
- [ ] No console errors or warnings

---

## Next Actions

1. **Update `frontend/pages/index.tsx`** with Stitch design system
2. **Create jurisdiction data file** with common options
3. **Implement citation parsing** in response display
4. **Add example prompts component**
5. **Test on mobile devices** and adjust accordingly

---

*Last updated: 2026-02-23*
*Focus: Ship a polished, functional MVP before adding complexity*
