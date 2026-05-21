# Job Match AI

一个基于 DeepSeek 的求职简历分析工具，帮助你快速了解简历与目标 JD 的匹配程度，提供具体的简历修改建议，并生成个性化的学习提升计划。

A DeepSeek-powered job application assistant that analyzes how well your resume matches a target job description, provides actionable rewrite suggestions, and generates a personalized skill-up learning plan.

---

## 功能 Features

### 分析报告 Analysis Report
- **JD 解析** — 自动拆解职责、必备技能、加分项和隐藏筛选条件
- **匹配分析** — 识别强匹配点、中等匹配点、可包装点和明显缺口
- **匹配评分** — 0–100 分综合评分 + 评分依据
- **简历修改建议** — 针对 Summary、Skills、Experience、Projects 给出具体改写示例

### 学习计划 Learning Plan
- **技能差距分析** — 列出与 JD 要求之间最关键的差距
- **推荐认证 & 课程** — AWS、Google、Coursera 等具体资源 + 预计完成时间
- **7 天每日计划** — 按天拆解任务，含目标、具体行动和完成标准
- **30 天四周计划** — 按周分主题，含里程碑检查点
- **项目建议** — 2–3 个可写进简历的具体项目

### 其他 Other
- **双 Tab 切换** — 分析报告与学习计划独立展示，按需加载
- **一键下载** — 两个 Tab 均可导出为 Markdown 文件

---

- **JD Breakdown** — Extracts responsibilities, required skills, nice-to-haves, and hidden filters
- **Resume Match Analysis** — Identifies strong matches, partial matches, packagable points, and gaps
- **Match Score** — 0–100 score with reasoning
- **Resume Rewrite Suggestions** — Concrete rewrites for Summary, Skills, Experience bullets, and Projects
- **Skill Gap Analysis** — Key gaps between your resume and the JD
- **Certifications & Courses** — Specific resources (AWS, Google, Coursera) with estimated completion time
- **7-Day Daily Plan** — Day-by-day tasks with goals and completion criteria
- **30-Day Weekly Roadmap** — Week-by-week themes with milestone checkpoints
- **Project Suggestions** — 2–3 portfolio projects worth adding to your resume
- **Download** — Export either tab as a Markdown file

---

## 界面预览 UI Overview

```
┌─────────────────┬──────────────────┬────────────────────────────────┐
│   JD 输入        │   简历上传        │  [ 分析报告 ] [ 学习计划 ]      │
│                 │                  │                                │
│  粘贴完整 JD     │  PDF / Word      │  匹配分析 / 每日学习计划        │
│                 │                  │                                │
│                 │  [ 开始分析 ]     │                      [ 下载 ]  │
└─────────────────┴──────────────────┴────────────────────────────────┘
```

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
pip install -r requirements.txt
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
2. **中栏** — 上传你的简历（支持 `.pdf` 和 `.docx`），点击「开始分析」
3. **右栏「分析报告」Tab** — 查看匹配分析和简历修改建议
4. **右栏「学习计划」Tab** — 点击后自动生成个性化学习计划（仅调用一次 API）
5. 点击「下载」导出当前 Tab 的 Markdown 报告

---

1. **Left panel** — Paste the full job description
2. **Middle panel** — Upload your resume and click「开始分析」(Analyze)
3. **Right panel「分析报告」tab** — View match analysis and resume rewrite suggestions
4. **Right panel「学习计划」tab** — Click to generate your personalized learning plan (one API call, cached)
5. Click Download to export the current tab as a Markdown file

---

## 项目结构 Project Structure

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

## 注意事项 Notes

- 本项目使用 DeepSeek API，需保持账户余额充足。/ Requires a funded DeepSeek account.
- 简历文件仅在本地内存中处理，不会持久化或上传至任何第三方服务。/ Resume files are processed in memory only and never persisted or sent to third parties.
- 当前为开发模式，生产部署请使用 Railway / Render 等平台或替换为 Gunicorn。/ For production, deploy via Railway / Render or use a WSGI server like Gunicorn.
