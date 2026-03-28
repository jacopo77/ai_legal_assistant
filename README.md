# AI Legal Assistant 🏛️⚖️

**ChatGPT for Legal Questions** — Instant answers with citations to real laws, accessible to everyone.

[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)](https://www.typescriptlang.org/)

---

## 🎯 Vision

Create a new market for AI-powered legal Q&A that serves the **50M+ people** who need legal information but can't afford traditional services.

**Not competing with:** Westlaw ($2000/mo for big law firms) or Clio (practice management)  
**Creating:** Free/affordable AI legal assistant for public, solo practitioners, paralegals, small firms, and legal aid nonprofits

**Core Value:** *"10 seconds to get a cited legal answer vs. 2 hours of manual research"*

---

## ✨ Features

- 💬 **Real-time streaming chat** - ChatGPT-style interface with live responses
- 🌍 **Multi-jurisdiction support** - US Federal, California, New York, UK, Canada
- 📚 **Cited answers** - Every response is grounded in ingested source documents
- 🎨 **Beautiful UI** - Modern dark theme with glass morphism design
- ⚡ **Fast & accurate** - RAG (Retrieval-Augmented Generation) with OpenAI embeddings
- 🔄 **Official-source ingestion** - Curated government/legal source ingestion via n8n, official APIs/bulk feeds, and Firecrawl fallback
- 🚀 **Production-ready** - Deployed on Railway (backend) + Vercel (frontend)

---

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Next.js   │─────▶│   FastAPI    │─────▶│  Supabase   │
│  Frontend   │      │   Backend    │      │  PostgreSQL │
│  (Vercel)   │      │  (Railway)   │      │  + pgvector │
└─────────────┘      └──────────────┘      └─────────────┘
                             │
                             ▼
                     ┌──────────────┐
                     │    OpenAI    │
                     │   API (GPT   │
                     │ + Embeddings)│
                     └──────────────┘
                             ▲
                             │
                     ┌──────────────┐
                     │ CuratedSource│
                     │ Registry +   │
                     │ n8nIngestion │
                     └──────────────┘
```

---

## Official Sources Model

This project is a **pre-indexed RAG system**, not a live web search engine.

Question-time behavior:
- the app embeds the user question
- retrieves matching chunks from Supabase
- answers only from those ingested chunks

Ingestion-time behavior:
- `n8n` reads from a curated list of official sources
- official APIs and bulk feeds are preferred where available
- Firecrawl is used as a fallback for official pages without practical API/bulk access

For the current US Federal rollout, the curated source registry lives in [docs/us_federal_official_sources.json](docs/us_federal_official_sources.json).

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- Supabase account (free tier)

### 1. Clone Repository

```bash
git clone https://github.com/jacopo77/ai_legal_assistant.git
cd ai_legal_assistant
```

### 2. Backend Setup

```bash
cd backend

# Create .env file with your keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload --port 8000
```

Test: http://127.0.0.1:8000/healthz should return `{"status":"ok"}`

### 3. Frontend Setup

```bash
cd frontend

# Create environment file
echo "NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000" > .env.local

# Install dependencies
npm install

# Run frontend
npm run dev
```

Open: http://localhost:3000

### 4. Test It!

Ask a question: *"What makes a contract valid?"*  
Select jurisdiction: *US Federal*  
Get instant answer with citations! 🎉

---

## 📁 Project Structure

```
ai_legal_assistant/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints (chat, health, webhooks)
│   │   ├── core/           # Settings & config
│   │   ├── services/       # RAG, embeddings, storage
│   │   └── main.py         # FastAPI app entry point
│   ├── Dockerfile          # Production container
│   ├── railway.toml        # Railway deployment config
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Next.js frontend
│   ├── app/
│   │   ├── page.tsx        # Main chat interface
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Global styles
│   ├── .env.local          # Environment variables
│   └── package.json        # Node dependencies
│
├── docs/                   # Documentation
│   ├── DEPLOYMENT_GUIDE.md # Step-by-step deployment
│   ├── COMMANDS.md         # Quick command reference
│   ├── RAILWAY_AND_N8N_SETUP.md
│   └── us_federal_official_sources.json
│
└── scripts/                # Utility scripts
    └── test_stack.py       # End-to-end testing
```

---

## 🌐 Deployment

### Backend → Railway

1. Create Railway project
2. Connect GitHub repo
3. Set root directory: `backend`
4. Add environment variables:
   - `OPENAI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `ALLOWED_ORIGIN=*`
5. Deploy!

**Full guide:** [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)

### Frontend → Vercel

1. Import from GitHub
2. Set root directory: `frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_BACKEND_URL=https://your-railway-url`
4. Deploy!

---

## 🧪 Testing

### Automated Test Suite

```bash
# Test local stack
python scripts/test_stack.py http://127.0.0.1:8000

# Test production stack
python scripts/test_stack.py https://your-railway-url.railway.app https://your-vercel-url.vercel.app
```

### Manual Testing

```bash
# Test backend health
curl http://127.0.0.1:8000/healthz

# Test database connection
curl http://127.0.0.1:8000/api/health/db

# Test chat endpoint
curl -X POST http://127.0.0.1:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"What is a contract?","country":"US"}'
```

---

## 📚 Documentation

- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Complete deployment walkthrough
- **[Command Reference](docs/COMMANDS.md)** - All commands you'll need
- **[n8n Setup](docs/RAILWAY_AND_N8N_SETUP.md)** - Official-source ingestion setup
- **[US Federal Source Registry](docs/us_federal_official_sources.json)** - Curated official source configuration for v1
- **[Frontend README](frontend/README.md)** - Frontend-specific docs

---

## 🗺️ Roadmap

### ✅ Phase 1: Core Product (COMPLETED)
- [x] Backend RAG system with OpenAI
- [x] Supabase vector storage
- [x] Streaming chat API
- [x] Beautiful chat UI
- [x] Multi-jurisdiction support
- [x] Citation highlighting

### 🚧 Phase 2: Deployment (IN PROGRESS)
- [x] Railway backend deployment config
- [x] Vercel frontend deployment config
- [ ] Deploy to production
- [ ] n8n + Firecrawl document ingestion
- [ ] Ingest 500+ legal documents

### 📅 Phase 3: Content & Quality
- [ ] Add more jurisdictions (EU, Australia)
- [ ] Improve citation formatting (clickable links)
- [ ] Add "Verify this answer" button
- [ ] Quality assurance testing
- [ ] User feedback collection

### 📅 Phase 4: User Accounts & Monetization
- [ ] Authentication (NextAuth.js)
- [ ] Usage tracking per user
- [ ] Free tier: 5 questions/month
- [ ] Premium tier: $20-50/month unlimited
- [ ] Stripe payment integration
- [ ] User dashboard

### 📅 Phase 5: Launch & Growth
- [ ] Landing page with value prop
- [ ] SEO optimization
- [ ] Launch on Product Hunt
- [ ] Build community
- [ ] Analytics & iteration

---

## 🛠️ Tech Stack

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [OpenAI API](https://openai.com/) - GPT-4 + embeddings
- [Supabase](https://supabase.com/) - PostgreSQL + pgvector
- [Railway](https://railway.app/) - Backend hosting

**Frontend:**
- [Next.js 14](https://nextjs.org/) - React framework
- [TypeScript](https://www.typescriptlang.org/) - Type safety
- [Tailwind CSS](https://tailwindcss.com/) - Styling
- [Vercel](https://vercel.com/) - Frontend hosting

**Automation:**
- [n8n](https://n8n.io/) - Workflow automation
- [Firecrawl](https://firecrawl.dev/) - Web scraping

---

## 🤝 Contributing

Contributions welcome! This project is in active development.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## ⚠️ Legal Disclaimer

This AI Legal Assistant provides general legal information only and does not constitute legal advice. Always consult with a licensed attorney for advice on your specific situation.

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/jacopo77/ai_legal_assistant/issues)
- **Documentation:** [docs/](docs/)
- **Email:** ask@legalsearchhub.com

---

## 🎉 Status

**Current Status:** ✅ MVP Built, 🚧 Deployment In Progress

- Local development: ✅ Working
- Backend RAG: ✅ Tested
- Frontend UI: ✅ Complete
- Railway deployment: ⏳ Configured, waiting for platform
- Vercel deployment: ⏳ Ready to deploy
- Production testing: ⏳ Pending

**Last Updated:** March 10, 2026

---

**Built with ❤️ for everyone who needs legal help but can't afford it**
