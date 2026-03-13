# 📡 AI Radar — Free Daily AI Digest Agent

> A fully automated Python agent that monitors the AI ecosystem and delivers a curated daily email digest every morning — **completely free**, no server needed.

---

## 📬 What You Get Every Morning

A clean HTML email with 5 sections delivered to your inbox automatically:

| Section | What's Inside |
|---|---|
| 📰 **News Highlights** | 3 biggest AI stories of the day |
| 🏢 **Top Labs Updates** | Google, OpenAI, Anthropic, Meta, Mistral releases |
| 🌍 **Developer Updates** | Framework & tool releases (LangChain, vLLM, Ollama...) |
| 🔓 **Open Source** | Notable open weight models & community highlights |
| 📄 **Notable Papers** | 2-3 must-read research papers with dev takeaways |

---

## 💸 Cost

**$0/month. Forever.**

| Component | Service | Free Limit | Daily Usage |
|---|---|---|---|
| 🤖 AI Filtering | Gemini 1.5 Flash | 1,500 req/day | 1 req |
| ☁️ Scheduling | GitHub Actions | 2,000 min/month | ~2 min |
| 📧 Email Delivery | Brevo SMTP | 300 emails/day | 1 email |
| 📡 Data Sources | RSS + GitHub feeds | Unlimited | ~25 feeds |

---

## 🏗️ How It Works

```
Every morning at 7AM UTC
         ↓
GitHub Actions spins up a free Ubuntu machine
         ↓
Fetches 25+ RSS feeds simultaneously
(Google AI, OpenAI, Anthropic, arXiv, GitHub releases, Reddit...)
         ↓
Sends all items to Gemini 1.5 Flash in one API call
Gemini filters noise → keeps only what matters for developers
         ↓
Renders a clean HTML email
         ↓
Sends via Brevo SMTP → lands in your inbox
         ↓
Ubuntu machine destroyed. Nothing stored. $0 spent.
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- GitHub account (free)
- Google account (for Gemini API)
- Brevo account (free)

### Step 1 — Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/ai-radar.git
cd ai-radar
pip install -r requirements.txt
```

### Step 2 — Get your free API keys

**Gemini API Key** *(2 minutes)*
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API Key** → **Create API Key**
3. Copy the key

**Brevo SMTP Key** *(3 minutes)*
1. Sign up free at [brevo.com](https://brevo.com) — no credit card
2. Go to **SMTP & API** → **SMTP** tab
3. Click **Generate a new SMTP key**
4. Verify your sender email address when prompted

### Step 3 — Configure
```bash
cp .env.example .env
```

Fill in your `.env`:
```env
GEMINI_API_KEY=your_gemini_key_here

BREVO_SMTP_HOST=smtp-relay.brevo.com
BREVO_SMTP_PORT=587
BREVO_SENDER_EMAIL=youremail@gmail.com
BREVO_SMTP_KEY=your_brevo_smtp_key_here
GMAIL_RECIPIENT=youremail@gmail.com
```

### Step 4 — Test locally
```bash
# Preview HTML only — no email sent
python main.py --test

# Send real email
python main.py
```

Open `output/preview.html` in your browser to see the digest.

---

## 🚀 Deploy on GitHub Actions (Free Autopilot)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-radar.git
git push -u origin main
```

### Step 2 — Add GitHub Secrets
Go to: **Repo → Settings → Secrets and variables → Actions → New repository secret**

Add all 6 secrets:

| Secret Name | Value |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key |
| `BREVO_SMTP_HOST` | `smtp-relay.brevo.com` |
| `BREVO_SMTP_PORT` | `587` |
| `BREVO_SENDER_EMAIL` | Your email address |
| `BREVO_SMTP_KEY` | Your Brevo SMTP key |
| `GMAIL_RECIPIENT` | Your email address |

### Step 3 — Trigger a manual test run
```
GitHub repo → Actions tab → AI Radar Daily Digest → Run workflow
```

Watch the live logs. Email arrives within 60 seconds of completion. ✅

### Step 4 — Done
Runs every morning at 7AM UTC automatically. No laptop needed.

---

## 📁 Project Structure

```
ai-radar/
├── main.py                      ← Entry point
├── requirements.txt             ← Python dependencies
├── check_feeds.py               ← Debug RSS feed health
├── .env.example                 ← Environment variable template
├── CLAUDE.md                    ← Context file for Claude Code AI
├── agent/
│   ├── fetchers/
│   │   ├── rss_fetcher.py       ← Fetches all RSS feeds in parallel
│   │   ├── github_fetcher.py    ← Fetches GitHub release feeds
│   │   └── reddit_fetcher.py    ← Optional Reddit fetcher
│   ├── summarizer.py            ← Gemini API filtering & summarization
│   ├── renderer.py              ← Builds HTML email
│   └── notifier.py              ← Sends email via Brevo SMTP
└── .github/
    └── workflows/
        └── daily_digest.yml     ← GitHub Actions cron schedule
```

---

## 📡 Sources Monitored

### 🏢 Top Labs
- Google AI Blog
- OpenAI Blog
- Anthropic Blog
- Meta AI Blog
- Mistral Blog
- DeepMind Blog

### 🌍 Developer Tools & Frameworks
- HuggingFace Blog
- LangChain, vLLM, Ollama, DSPy, LiteLLM, PydanticAI, CrewAI, AutoGen
- llama.cpp, HuggingFace Transformers

### 🔓 Open Source Community
- HuggingFace Papers (daily)
- r/LocalLLaMA
- r/MachineLearning

### 📄 Research Papers
- arXiv cs.AI
- arXiv cs.LG
- arXiv cs.CL

### 📰 Tech News
- TechCrunch AI
- VentureBeat AI
- The Verge AI
- Hacker News (AI posts)
- Wired AI

---

## ⚙️ Customisation

### Add a new RSS source
Open `agent/fetchers/rss_fetcher.py` and add to the relevant list:
```python
DEV_TOOLS_SOURCES = [
    ...
    {"url": "https://your-new-source.com/rss", "category": "devtools", "source": "Source Name"},
]
```

### Change the schedule
Edit `.github/workflows/daily_digest.yml`:
```yaml
# Every day at 7AM UTC
- cron: '0 7 * * *'

# Weekdays only
- cron: '0 7 * * 1-5'

# Twice daily — 7AM and 7PM UTC
- cron: '0 7,19 * * *'

# 7AM India time (IST = UTC+5:30)
- cron: '30 1 * * *'
```

### Tune the AI filter
Edit the `SYSTEM_PROMPT` in `agent/summarizer.py` to change what Gemini keeps or discards. For example to get fewer papers:
```
Papers (max 2 items):
Only keep papers with immediate practical value for LLM engineers.
```

### Check feed health
```bash
python check_feeds.py
```
Shows which RSS feeds are live, returning valid XML, or broken.

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `GEMINI_API_KEY is not set` | Delete and re-add the GitHub secret. Check for typos. |
| Email not arriving | Check `BREVO_SMTP_KEY` secret. Verify sender email in Brevo dashboard. |
| Top Labs section empty | Company hasn't posted recently — normal. 90-day lookback is active. |
| Feed errors in logs | Run `python check_feeds.py` — shows exactly which feeds are broken. |
| Node.js warning in Actions | `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` is set in workflow — safe to ignore until June 2026. |
| Too many irrelevant items | Tighten the Gemini prompt in `agent/summarizer.py`. |

---

## 🔒 Security

- API keys are stored as **encrypted GitHub Secrets** — never in code
- `.env` is in `.gitignore` — never committed to the repo
- Each GitHub Actions run uses a **fresh, isolated Ubuntu machine**
- Secrets are **masked in logs** — never visible even if run fails
- Enable **2FA on your GitHub account** for best security

---

## 🛠️ Built With

- **Python 3.11** — core language
- **feedparser** — RSS parsing
- **requests** — HTTP calls
- **Google Gemini 1.5 Flash** — AI filtering and summarization
- **Brevo SMTP** — email delivery
- **GitHub Actions** — free cloud scheduling

---

## 🤝 Contributing

PRs welcome! Good first contributions:

- 🆕 Add new RSS sources
- 🌍 Add Telegram or Slack delivery option
- 📅 Add weekly summary mode (Friday digest)
- 🐳 Add Docker support for easier local setup
- 🌐 Add web dashboard using GitHub Pages

---

## 📄 License

MIT — free to use, modify, and distribute.

---

## ⭐ If This Helped You

Give it a star on GitHub — it helps others find it.

Built by a developer, for developers. No ads, no tracking, no paywalls.
