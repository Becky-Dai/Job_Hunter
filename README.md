# Job Match AI

A DeepSeek-powered job application assistant that analyzes how well your resume matches a target job description, provides actionable rewrite suggestions, and generates a personalized skill-up learning plan.

基于 DeepSeek 的求职简历分析工具，帮助你了解简历与目标 JD 的匹配程度，提供具体的简历修改建议，并生成个性化学习计划。

---

## Features 功能

### Analysis Report 分析报告
- **JD Breakdown** — Extracts responsibilities, required skills, nice-to-haves, and hidden filters
- **Resume Match Analysis** — Identifies strong matches, partial matches, packagable points, and gaps
- **Match Score** — 0–100 score with reasoning
- **Resume Rewrite Suggestions** — Concrete rewrites for Summary, Skills, Experience bullets, and Projects

### Learning Plan 学习计划
- **Skill Gap Analysis** — Key gaps between your resume and the JD
- **Certifications & Courses** — Specific resources (AWS, Google, Coursera) with estimated completion time
- **7-Day Daily Plan** — Day-by-day tasks with goals and completion criteria
- **30-Day Weekly Roadmap** — Week-by-week themes with milestone checkpoints
- **Project Suggestions** — 2–3 portfolio projects worth adding to your resume

### Other 其他
- **Tabbed Output** — Analysis and learning plan load independently, results cached after first fetch
- **Download** — Export either tab as a Markdown file

---

## UI Overview 界面预览

```
┌─────────────────┬──────────────────┬────────────────────────────────┐
│   Paste JD      │  Upload Resume   │  [ Analysis ] [ Learning Plan ]│
│                 │                  │                                │
│  Full JD text   │  PDF / Word      │  Match analysis / Daily plan   │
│                 │                  │                                │
│                 │  [ Analyze ]     │                   [ Download ] │
└─────────────────┴──────────────────┴────────────────────────────────┘
```

---

## Tech Stack 技术栈

| Layer | Technology |
|-------|------------|
| Backend | Python · Flask |
| AI | DeepSeek API (`deepseek-chat`) via OpenAI-compatible SDK |
| Agent Framework | `openai-agents` |
| Resume Parsing | `pdfplumber` (PDF) · `python-docx` (Word) |
| Frontend | HTML · Tailwind CSS · Marked.js |

---

## Quick Start 快速开始

### 1. Clone

```bash
git clone https://github.com/Becky-Dai/Job_Hunter.git
cd Job_Hunter
```

### 2. Install dependencies 安装依赖

```bash
pip install -r requirements.txt
```

### 3. Set API Key 配置 API Key

**Windows (PowerShell)**
```powershell
$env:DEEPSEEK_API_KEY = "your_api_key_here"
```

**macOS / Linux**
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

> Get your API key at [platform.deepseek.com](https://platform.deepseek.com).
>
> 在 [platform.deepseek.com](https://platform.deepseek.com) 注册并获取 API Key。

### 4. Run 启动

```bash
python app.py
```

Open in browser → 打开浏览器访问: **http://localhost:5000**

---

## Usage 使用方法

1. **Left panel** — Paste the full job description
2. **Middle panel** — Upload your resume (`.pdf` or `.docx`) and click **Analyze**
3. **Right panel「分析报告」tab** — View match analysis and resume rewrite suggestions
4. **Right panel「学习计划」tab** — Click to generate your personalized learning plan (one API call, cached)
5. Click **Download** to export the current tab as a Markdown file

---

1. **左栏** — 粘贴完整 JD
2. **中栏** — 上传简历（`.pdf` 或 `.docx`），点击「开始分析」
3. **右栏「分析报告」Tab** — 查看匹配分析和简历修改建议
4. **右栏「学习计划」Tab** — 点击后自动生成学习计划（仅调用一次 API，结果缓存）
5. 点击「下载」导出当前 Tab 的 Markdown 报告

---

## Project Structure 项目结构

```
Job_Hunter/
├── app.py                  # Flask backend + two DeepSeek agents
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Three-panel frontend UI with tabbed output
├── .gitignore
└── README.md
```

---

## Notes 注意事项

- Requires a funded DeepSeek account. / 需保持 DeepSeek 账户余额充足。
- Resume files are processed in memory only and never persisted or sent to third parties. / 简历文件仅在内存中处理，不会持久化或上传至第三方。
- For production, deploy via Railway / Render or use a WSGI server like Gunicorn. / 生产部署建议使用 Railway / Render 或 Gunicorn。
