# Job Match AI

一个基于 DeepSeek 的求职简历分析工具，帮助你快速了解简历与目标 JD 的匹配程度，并给出具体的改进建议。

A DeepSeek-powered job application assistant that analyzes how well your resume matches a target job description, and provides actionable improvement suggestions.

---

## 功能 Features

- **JD 解析** — 自动拆解职责、必备技能、加分项和隐藏筛选条件
- **匹配分析** — 识别强匹配点、中等匹配点、可包装点和明显缺口
- **匹配评分** — 0–100 分综合评分 + 评分依据
- **简历修改建议** — 针对 Summary、Skills、Experience、Projects 给出具体改写示例
- **补强路线** — 缺口技能 + 7 天 / 30 天行动计划
- **一键下载报告** — 将分析结果导出为 Markdown 文件

---

- **JD Breakdown** — Extracts responsibilities, required skills, nice-to-haves, and hidden filters
- **Resume Match Analysis** — Identifies strong matches, partial matches, packagable points, and gaps
- **Match Score** — 0–100 score with reasoning
- **Resume Rewrite Suggestions** — Concrete rewrites for Summary, Skills, Experience bullets, and Projects
- **Skill-up Roadmap** — Missing skills + 7-day and 30-day action plans
- **Download Report** — Export the full analysis as a Markdown file

---

## 技术栈 Tech Stack

| 层级 | 技术 |
|------|------|
| Backend | Python · Flask |
| AI | DeepSeek API (`deepseek-chat`) via OpenAI-compatible SDK |
| Agent Framework | `openai-agents` |
| Resume Parsing | `pdfplumber` (PDF) · `python-docx` (Word) |
| Frontend | HTML · Tailwind CSS · Marked.js |

---

## 快速开始 Quick Start

### 1. 克隆项目 Clone

```bash
git clone https://github.com/Becky-Dai/Job_Hunter.git
cd Job_Hunter
```

### 2. 安装依赖 Install dependencies

```bash
pip install flask openai-agents pdfplumber python-docx
```

### 3. 配置 API Key

**Windows (PowerShell)**
```powershell
$env:DEEPSEEK_API_KEY = "your_api_key_here"
```

**macOS / Linux**
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

> 在 [platform.deepseek.com](https://platform.deepseek.com) 注册并获取 API Key。
>
> Get your API key at [platform.deepseek.com](https://platform.deepseek.com).

### 4. 启动 Run

```bash
python app.py
```

打开浏览器访问 → Open in browser: **http://localhost:5000**

---

## 使用方法 Usage

1. **左栏** — 将目标职位的完整 JD 粘贴进去
2. **中栏** — 上传你的简历（支持 `.pdf` 和 `.docx`）
3. 点击 **「开始分析」**
4. **右栏** — 查看详细分析报告，点击「下载报告」导出 Markdown

---

1. **Left panel** — Paste the full job description
2. **Middle panel** — Upload your resume (`.pdf` or `.docx`)
3. Click **「开始分析」** (Analyze)
4. **Right panel** — View the full report, click Download to save as Markdown

---

## 项目结构 Project Structure

```
Job_Hunter/
├── app.py                  # Flask backend + DeepSeek agent
├── templates/
│   └── index.html          # Three-panel frontend UI
├── .gitignore
└── README.md
```

---

## 注意事项 Notes

- 本项目使用 DeepSeek API，需保持账户余额充足。/ Requires a funded DeepSeek account.
- 简历文件仅在本地处理，不会上传至任何第三方服务。/ Resume files are processed locally and never sent to third-party services.
- 当前为开发模式，生产部署请替换为 Gunicorn 等 WSGI 服务器。/ For production, replace Flask dev server with a WSGI server like Gunicorn.
