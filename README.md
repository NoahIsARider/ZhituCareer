<div align="center">

# 🧭 ZhituCareer+

**AI-powered career planning and job-hunting assistant**

A one-stop career analysis platform built on **Flask + multi-agent collaboration (LLM + Playwright real-time market analysis)**, offering career path analysis, intelligent job matching, and course learning recommendations.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)
![ModelScope](https://img.shields.io/badge/LLM-ModelScope%20%2F%20SiliconFlow-4B32C3?style=flat-square)
![Playwright](https://img.shields.io/badge/Playwright-Automation-2EAD33?style=flat-square&logo=playwright&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)

<br>

**⭐ If this project helps you, feel free to give it a Star!**

</div>

---

## ✨ Features

| Feature | Description |
| --- | --- |
| 🎯 **Career Path Analysis** | Generates a personalized career direction based on your profile and real-time market data |
| 💼 **Smart Job Matching** | Matches the most suitable jobs from the job pool based on your skills and search preferences |
| 📊 **Market Trend Insights** | Playwright scrapes job market dynamics in real time, and the AI summarizes industry trends |
| 📚 **Course Recommendations** | Recommends courses and learning paths aligned with your career goals |
| 🔐 **Role-based Access Control** | User / admin dual roles with a dedicated admin panel |
| 🚀 **Out of the Box** | Built-in demo accounts and sample data; deployable within minutes |

---

## 📸 Interface Preview

### Login Page

![Login page](docs/screenshots/login.png)

### User Career Analysis Dashboard

![User dashboard](docs/screenshots/dashboard.png)

### Admin Panel

![Admin panel](docs/screenshots/admin.png)

---

## 🧠 Core Concept: Multi-Agent Collaboration Architecture

ZhituCareer+ uses a modular **agent collaboration architecture** in which multiple agents each do their part and work in sequence:

- **User Profile Agent**: parses education / major / skills / experience / goals and outputs a personal capability profile
- **Market Analysis Agent**: scrapes job market dynamics in real time with Playwright, combined with LLM to produce industry trends
- **Job Recommendation Agent**: combines the personal profile and market analysis to generate structured job-hunting advice
- **Job Matching Agent**: filters the most suitable positions from the job pool by match score
- **Course Matching Agent**: recommends the most relevant courses based on career goals

```
User Profile Agent ──► Market Analysis Agent ──► Job Recommendation Agent ──► Recommendation Results
                          │                            │
                          ▼                            ▼
                 Playwright live scraping      Job Matching Agent / Course Matching Agent
```

<div align="center">
  <img src="agent/agent_structure.jpeg" width="360px">
</div>

---

## 🚀 Quick Start

### Requirements

- Python 3.9+ (recommend [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html))
- An API Key from [ModelScope](https://www.modelscope.cn/) or [SiliconFlow](https://siliconflow.cn/)

### Installation

```bash
# 1. Create and activate a virtual environment
conda create -n zhitu_career python=3.9
conda activate zhitu_career

# 2. Clone the repository
git clone https://github.com/NoahIsARider/ZhituCareer.git
cd ZhituCareer

# 3. Install dependencies
pip install -r requirements.txt
```

### Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API key:

```bash
cp .env.example .env
```

```env
# Required: ModelScope / SiliconFlow API Key
OPENAI_API_KEY=your_api_key_here

# Optional: custom model and API base URL
# LLM_BASE_URL=https://api-inference.modelscope.cn/v1/
# LLM_MODEL=LLM-Research/Meta-Llama-3.1-8B-Instruct

# Optional: change the session secret key in production
# SECRET_KEY=your-secret-key
```

> 💡 All model names and API base URLs can be overridden via environment variables — no code changes needed.
> The app still starts normally without an API key; the AI analysis features will show a clear prompt when invoked.

### Start the Application

```bash
python app.py
```

Visit **http://localhost:5000** and log in with a demo account:

| Role | Phone | Password |
| --- | --- | --- |
| 👑 Admin | `13800000000` | `admin123` |
| 👤 Regular user | `13900000000` | `user123` |

---

## 📖 Usage Guide

### Regular Users

1. After logging in, fill in your **education / major / skills / experience / career goals** on the dashboard
2. Click "Get Career Analysis" and the AI will generate **career direction, job-hunting advice, a skill improvement checklist, and recommended positions**
3. Use "Job Search" to match positions by keyword and city
4. Use "Course Recommendations" to get a learning path aligned with your career goals

### Admins

1. After logging in, view real-time statistics for courses and positions in the "Admin Panel"
2. Use the card actions to **add / edit / delete** course and position data
3. Data is saved to `data/course.json` and `data/jobs.json`

---

## 🗂️ Project Structure

```
ZhituCareer/
├── app.py                  # Flask main app (routing, auth, session management)
├── career_model.py         # Career analysis orchestration (multi-agent pipeline)
├── job_matching.py         # Job matching service
├── course_matching.py      # Course matching service
├── agent/                  # Multi-agent collaboration layer
│   ├── llm_client.py       # LLM client and unified response handling
│   ├── user_profile_agent.py
│   ├── market_analysis_agent.py   # Playwright market scraping
│   ├── job_recommendation_agent.py
│   ├── job_matching_agent.py
│   └── course_matching_agent.py
├── data/                   # Data storage (JSON)
│   ├── users.json          # Users and roles
│   ├── jobs.json           # Job data
│   └── course.json         # Course data
├── templates/              # Frontend pages (Bootstrap 5)
│   ├── login.html          # Login page
│   ├── index.html          # User dashboard
│   └── admin.html          # Admin panel
└── requirements.txt
```

---

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Flask 3 · Python 3.9+ |
| AI Engine | OpenAI-compatible API (ModelScope / SiliconFlow) · Meta-Llama-3.1-8B-Instruct |
| Data Collection | Playwright (headless Chromium) |
| Frontend | Bootstrap 5 · Bootstrap Icons · vanilla ES6 |
| Data Storage | JSON files (seamlessly migratable to SQLite / MySQL, see the [data_base branch](https://github.com/NoahIsARider/ZhituCareer/tree/data_base)) |

---

## 🔧 Configuration

The system is highly configurable, entirely through environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `OPENAI_API_KEY` | empty | **Required**, ModelScope / SiliconFlow API Key |
| `LLM_BASE_URL` | ModelScope v1 | Custom LLM API base URL |
| `LLM_MODEL` | Llama-3.1-8B | Custom inference model |
| `SECRET_KEY` | dev placeholder | Flask session key; must be changed in production |
| `HOST` / `PORT` | `0.0.0.0` / `5000` | Service listen address |
| `FLASK_DEBUG` | `0` | Enable debug mode |

---

## 🤝 Contributing

Any form of contribution is welcome!

- 🐛 Found a bug → submit an [Issue](https://github.com/NoahIsARider/ZhituCareer/issues)
- ✨ New feature / improvement → fork and submit a Pull Request
- 📖 Improve documentation → help more people get started quickly

> Before submitting a PR, please make sure the code passes basic checks and follows the existing code style.

---

## 📄 License

This project is open-sourced under the **MIT License**; see the [LICENSE](LICENSE) file for details.
