# AI Legal Assistant - Frontend

Modern chat interface for the AI Legal Assistant. Built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- 💬 **Real-time streaming chat** - ChatGPT-style interface with streaming responses
- 🌍 **Jurisdiction selector** - Choose US Federal, California, New York, UK, or Canada
- 📑 **Citation highlighting** - Legal citations appear as superscript references [1]
- 🎨 **Beautiful UI** - Modern dark theme with glass morphism effects
- ⚡ **Fast & responsive** - Optimized for mobile and desktop
- ❌ **Error handling** - Clear error messages when backend is unavailable

## Local Development

### Prerequisites

- Node.js 18+ installed
- Backend running on `http://127.0.0.1:8000` (or update `NEXT_PUBLIC_BACKEND_URL`)

### Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment:**
   ```bash
   # .env.local is already created with:
   NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   ```
   http://localhost:3000
   ```

## Deployment to Vercel

### Quick Deploy

1. **Push code to GitHub** (if not already done)

2. **Go to [vercel.com](https://vercel.com)**

3. **Create New Project:**
   - Import from GitHub
   - Select `ai_legal_assistant` repository
   - Set **Root Directory** to `frontend`
   - Add environment variable:
     ```
     NEXT_PUBLIC_BACKEND_URL=https://your-railway-url.up.railway.app
     ```
   - Click **Deploy**

4. **Get your URL:**
   - Vercel will give you a URL like `https://your-app.vercel.app`
   - Update Railway's `ALLOWED_ORIGIN` to include this URL

### Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx        # Root layout with fonts & metadata
│   ├── page.tsx          # Main chat interface
│   └── globals.css       # Global styles & Tailwind
├── public/               # Static assets
├── .env.local            # Environment variables (local)
├── next.config.js        # Next.js configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── package.json          # Dependencies
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_BACKEND_URL` | Backend API URL | `http://127.0.0.1:8000` (local)<br>`https://your-app.railway.app` (production) |

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Icons:** Google Material Symbols
- **Fonts:** Inter (Google Fonts)

## Key Features Explained

### Streaming Responses

The chat uses Server-Sent Events (SSE) to stream responses from the backend in real-time:

```typescript
const reader = res.body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  // Update UI with partial response
}
```

### Citation Highlighting

Legal citations like `[1]` are automatically detected and styled as superscript:

```typescript
const citationRegex = /\[(\d+)\]/g;
// Renders as: "A contract requires consideration [1]"
```

### Error Handling

Connection errors show helpful debug information including the backend URL being used.

## Troubleshooting

### "Failed to connect to backend"

1. Check backend is running: `http://127.0.0.1:8000/healthz` should return `{"status":"ok"}`
2. Check `NEXT_PUBLIC_BACKEND_URL` in `.env.local`
3. Check CORS settings in backend (should allow `http://localhost:3000`)

### Citations not showing

Backend needs to return responses with citation format like: `[1]`, `[2]`, etc.

### Styling issues

1. Run `npm install` to ensure Tailwind CSS is installed
2. Check `tailwind.config.js` includes correct content paths
3. Restart dev server

## Production Checklist

- [ ] Update `NEXT_PUBLIC_BACKEND_URL` to Railway production URL
- [ ] Test chat functionality end-to-end
- [ ] Verify CORS allows Vercel domain
- [ ] Add custom domain (optional)
- [ ] Set up analytics (optional)
- [ ] Add authentication (Phase 3)

## Next Steps

After basic deployment:

1. **Add authentication** - NextAuth.js or Supabase Auth
2. **Usage tracking** - Track questions per user
3. **Freemium model** - 5 questions/month free tier
4. **Payment integration** - Stripe for premium subscriptions
5. **Chat history** - Save/load previous conversations
6. **Mobile app** - React Native version

## License

MIT
