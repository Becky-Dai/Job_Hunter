from flask import Flask, request, jsonify, render_template
import os, json, re, io, uuid, requests
from bs4 import BeautifulSoup
from ddgs import DDGS
import pdfplumber
from docx import Document
from agents import (
    Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel,
    set_tracing_disabled, ModelSettings,
)

set_tracing_disabled(True)

app = Flask(__name__)

deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
deepseek_client = AsyncOpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")
deepseek_model = OpenAIChatCompletionsModel(model="deepseek-chat", openai_client=deepseek_client)

# In-memory session store: sid -> {resume_text, raw_results}
_sessions = {}


def extract_text(file):
    name = file.filename.lower()
    data = file.read()
    if name.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    elif name.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    return data.decode("utf-8", errors="ignore")


def search_jobs(query):
    results = []
    with DDGS() as ddgs:
        results += list(ddgs.text(f"{query} site:au.indeed.com/viewjob", max_results=8, timelimit="w"))
        results += list(ddgs.text(f"{query} site:linkedin.com/jobs", max_results=8, timelimit="w"))
    # Fallback: retry without time limit if nothing found
    if not results:
        with DDGS() as ddgs:
            results += list(ddgs.text(f"{query} site:au.indeed.com/viewjob", max_results=8))
            results += list(ddgs.text(f"{query} site:linkedin.com/jobs", max_results=8))
    return results


_BOT_CHECK_PHRASES = [
    "confirm you are human", "verify you are human", "help us keep seek secure",
    "captcha", "are you a robot", "browser check", "access denied",
]

def fetch_jd(url, fallback=""):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for t in soup(["script", "style", "nav", "header", "footer"]):
            t.decompose()
        text = soup.get_text(separator="\n", strip=True)[:3000]
        if any(p in text.lower() for p in _BOT_CHECK_PHRASES):
            return fallback  # bot-check page, use search snippet instead
        return text
    except Exception:
        return fallback


def enrich_snippet(title, company, base_snippet):
    """Search for extra snippets about this specific job to supplement the JD."""
    try:
        query = f'"{title}" "{company}" job responsibilities requirements'
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        extras = " ".join(r["body"] for r in results if r.get("body"))
        return (base_snippet + "\n\n" + extras).strip()[:3000]
    except Exception:
        return base_snippet


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def search():
    if not deepseek_api_key:
        return jsonify(error="未设置 DEEPSEEK_API_KEY 环境变量"), 500

    file = request.files.get("resume")
    location = request.form.get("location", "").strip()
    job_title = request.form.get("job_title", "").strip()

    if not file or not location or not job_title:
        return jsonify(error="请上传简历并填写地区和职位"), 400

    resume_text = extract_text(file)
    target = f"{location} {job_title}"

    raw = search_jobs(target)
    if not raw:
        return jsonify(error="未找到相关职位，请检查网络或修改搜索条件"), 404

    summary = "\n\n".join(
        f"[{i+1}] 标题: {r['title']}\n来源: {r['href']}\n摘要: {r['body']}"
        for i, r in enumerate(raw)
    )

    ranker = Agent(
        name="Job Ranker",
        model=deepseek_model,
        model_settings=ModelSettings(temperature=0.1),
        instructions=(
            "你是招聘筛选助手，从搜索结果中选出最相关、最值得投递的 5 个职位。\n"
            "入选条件：\n"
            "1. 过去 7 天内发布（若无明确时间信息则默认符合）。\n"
            "2. 仍在接受申请——排除含 closed / no longer accepting / position filled / 已截止 / 已关闭 的结果。\n"
            "3. 来自 5 家不同公司，同一公司只取最匹配的一个。\n"
            "4. 与候选人 resume 和目标职位最相关。\n"
            "只返回纯 JSON 数组，不要任何解释文字。"
        ),
    )

    rank_prompt = f"""
目标职位与地区：{target}

Resume：
{resume_text}

搜索结果：
{summary}

选出 Top 5，只返回如下 JSON，不要其他内容：
[
  {{"rank":1,"index":序号,"title":"职位名","company":"公司名","url":"链接","reason":"一句话选择原因"}},
  {{"rank":2,"index":序号,"title":"职位名","company":"公司名","url":"链接","reason":"一句话选择原因"}},
  {{"rank":3,"index":序号,"title":"职位名","company":"公司名","url":"链接","reason":"一句话选择原因"}},
  {{"rank":4,"index":序号,"title":"职位名","company":"公司名","url":"链接","reason":"一句话选择原因"}},
  {{"rank":5,"index":序号,"title":"职位名","company":"公司名","url":"链接","reason":"一句话选择原因"}}
]
"""

    res = Runner.run_sync(ranker, rank_prompt)
    m = re.search(r'\[.*?\]', res.final_output, re.DOTALL)
    if not m:
        return jsonify(error="筛选失败，请重试"), 500

    jobs = json.loads(m.group())

    sid = str(uuid.uuid4())
    _sessions[sid] = {"resume_text": resume_text, "raw": raw}

    return jsonify(sid=sid, jobs=jobs)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json or {}
    sid = data.get("sid")
    job = data.get("job")

    if not sid or not job or sid not in _sessions:
        return jsonify(error="无效请求，请重新搜索"), 400

    sess = _sessions[sid]
    resume_text = sess["resume_text"]
    raw = sess["raw"]

    idx = job.get("index", 1) - 1
    fallback = raw[idx]["body"] if idx < len(raw) else ""
    jd_text = fetch_jd(job["url"], fallback)
    # If we only have the short snippet, enrich it with an extra search
    if jd_text == fallback:
        jd_text = enrich_snippet(job.get("title", ""), job.get("company", ""), fallback)

    agent = Agent(
        name="DeepSeek Job Application Coach",
        model=deepseek_model,
        model_settings=ModelSettings(temperature=0.2),
        instructions="""
你是一个求职申请分析助手，专门帮助用户分析目标岗位、JD 和 resume 的匹配度。

你的任务：
1. 拆解 JD：
   - 岗位一句话总结
   - 核心职责
   - 必备技能 / 加分技能 / 软技能
   - 隐藏筛选条件

2. 匹配 Resume：
   - 强匹配点
   - 中等匹配点
   - 可以包装但表达不清楚的点
   - 明显缺口
   - recruiter 可能担心的风险

3. 匹配度：0-100 分 + 原因

4. Resume 修改建议：
   - Summary 怎么改
   - Skills 排序
   - Experience bullets 怎么改
   - Projects 怎么重排

5. 补强路线：
   - 缺什么技能
   - 未来 7 天计划
   - 未来 30 天计划

规则：不编造经历；可包装的明确说"可以包装，但不能夸大"；输出中文；具体可执行。
""",
    )

    prompt = f"""
【职位】{job['title']} @ {job.get('company', '')}
【链接】{job['url']}
【选择原因】{job.get('reason', '')}

【JD 内容】
{jd_text}

【Resume】
{resume_text}
"""

    result = Runner.run_sync(agent, prompt)
    return jsonify(analysis=result.final_output)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
