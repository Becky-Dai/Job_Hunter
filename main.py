from pathlib import Path
from datetime import datetime
import os
import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
    ModelSettings,
)

set_tracing_disabled(True)

deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
if not deepseek_api_key:
    print("错误：请先设置环境变量 DEEPSEEK_API_KEY")
    sys.exit(1)

for fname in ("target.txt", "resume.txt"):
    if not Path(fname).exists():
        print(f"错误：找不到文件 {fname}")
        sys.exit(1)

target_text = Path("target.txt").read_text(encoding="utf-8").strip()
resume_text = Path("resume.txt").read_text(encoding="utf-8").strip()

deepseek_client = AsyncOpenAI(
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com",
)

deepseek_model = OpenAIChatCompletionsModel(
    model="deepseek-chat",
    openai_client=deepseek_client,
)


def search_jobs(query, max_results=15):
    seek_query = f"{query} site:seek.com.au"
    linkedin_query = f"{query} site:linkedin.com/jobs"
    results = []
    with DDGS() as ddgs:
        # timelimit="w" 只返回过去一周内发布的结果
        results += list(ddgs.text(seek_query, max_results=max_results // 2, timelimit="w"))
        results += list(ddgs.text(linkedin_query, max_results=max_results // 2, timelimit="w"))
    return results


def fetch_job_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:3000]
    except Exception:
        return None


# ── Phase 1: 搜索 ──────────────────────────────────────────────────────────────
print("正在搜索相关职位（Seek + LinkedIn）...")
search_results = search_jobs(target_text)

if not search_results:
    print("错误：未找到任何职位，请检查 target.txt 或网络连接")
    sys.exit(1)

search_summary = "\n\n".join([
    f"[{i+1}] 标题: {r['title']}\n来源: {r['href']}\n摘要: {r['body']}"
    for i, r in enumerate(search_results)
])

# ── Phase 2: 筛选 Top 3 ────────────────────────────────────────────────────────
print("正在筛选最相关的 Top 3 职位...")

ranker_agent = Agent(
    name="Job Ranker",
    model=deepseek_model,
    model_settings=ModelSettings(temperature=0.1),
    instructions=(
        "你是招聘筛选助手，根据候选人 resume 和目标职位，从搜索结果中选出最相关、最值得投递的 3 个职位。\n"
        "必须满足以下所有条件才能入选：\n"
        "1. 职位在过去 7 天内发布（摘要或标题中有时间提示如 '1d ago'、'3 days ago'、'今天' 等）；\n"
        "   若摘要没有明确时间信息，默认认为符合（搜索已过滤过去一周）。\n"
        "2. 职位仍在接受申请——排除摘要中出现 'closed'、'no longer accepting'、'position filled'、"
        "'applications closed'、'已截止'、'已关闭' 等字样的结果。\n"
        "3. 三个职位必须来自不同公司——不允许同一家公司出现两次。\n"
        "4. 与候选人 resume 和目标职位最相关。\n"
        "只返回纯 JSON 数组，不要任何解释文字。"
    ),
)

rank_prompt = f"""
目标职位与地区：
{target_text}

Resume：
{resume_text}

搜索结果：
{search_summary}

从上述搜索结果中，选出同时满足以下条件的 Top 3 职位：
- 过去 7 天内发布
- 仍在接受申请（未截止、未关闭）
- 三个职位来自三家不同公司（同一公司只取最匹配的一个）
- 与 resume 和目标职位最相关

只返回如下 JSON，不要其他内容：
[
  {{"rank": 1, "index": 序号, "title": "职位名", "url": "链接", "reason": "选择原因"}},
  {{"rank": 2, "index": 序号, "title": "职位名", "url": "链接", "reason": "选择原因"}},
  {{"rank": 3, "index": 序号, "title": "职位名", "url": "链接", "reason": "选择原因"}}
]
"""

rank_result = Runner.run_sync(ranker_agent, rank_prompt)

json_match = re.search(r'\[.*?\]', rank_result.final_output, re.DOTALL)
if not json_match:
    print("错误：无法解析 Top 3 筛选结果，请重试")
    sys.exit(1)

top3 = json.loads(json_match.group())

# ── Phase 3: 抓取 JD 详情 ──────────────────────────────────────────────────────
print("正在获取职位详情...")
for job in top3:
    idx = job["index"] - 1
    fallback_snippet = search_results[idx]["body"] if idx < len(search_results) else ""
    content = fetch_job_content(job["url"])
    job["jd_text"] = content if content else f"（无法抓取页面，仅有搜索摘要）\n{fallback_snippet}"

# ── Phase 4: 逐个分析 ─────────────────────────────────────────────────────────
analysis_agent = Agent(
    name="DeepSeek Job Application Coach",
    model=deepseek_model,
    model_settings=ModelSettings(temperature=0.2),
    instructions="""
你是一个求职申请分析助手，专门帮助用户分析目标岗位、JD 和 resume 的匹配度。

你的任务：
1. 拆解 JD：
   - 岗位一句话总结
   - 核心职责
   - 必备技能
   - 加分技能
   - 软技能
   - 隐藏筛选条件

2. 匹配 Resume：
   - 强匹配点
   - 中等匹配点
   - 可以包装但表达不清楚的点
   - 明显缺口
   - recruiter 可能担心的风险

3. 给出匹配度：
   - 0-100 分
   - 解释为什么是这个分数

4. 给出 Resume 修改建议：
   - Summary 应该怎么改
   - Skills 应该怎么排序
   - Experience bullets 应该怎么改
   - Projects 应该怎么重排

5. 给出补强路线：
   - 缺什么技能
   - 未来 7 天计划
   - 未来 30 天计划

重要规则：
- 不要编造用户没有的经历。
- 不要假装用户已经掌握某项技能。
- 如果某项经历只能包装，请明确说"可以包装，但不能夸大"。
- 输出中文。
- 具体、直接、可执行。
""",
)

reports = []
for job in top3:
    print(f"正在分析 Top {job['rank']}：{job['title']}...")
    analysis_prompt = f"""
请根据下面的 JD 和 resume，做岗位匹配、简历优化和学习补强分析。

【职位】{job['title']}
【链接】{job['url']}
【选择原因】{job['reason']}

【JD 内容】
{job['jd_text']}

【Resume】
{resume_text}
"""
    result = Runner.run_sync(analysis_agent, analysis_prompt)
    reports.append({
        "rank": job["rank"],
        "title": job["title"],
        "url": job["url"],
        "analysis": result.final_output,
    })

# ── Phase 5: 写入报告 ──────────────────────────────────────────────────────────
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = output_dir / f"deepseek_job_match_report_{timestamp}.md"

lines = [
    f"# 求职分析报告",
    f"\n**目标**：{target_text}  ",
    f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
    "---\n",
]
for r in reports:
    lines += [
        f"## Top {r['rank']}：{r['title']}",
        f"\n**链接**：{r['url']}\n",
        r["analysis"],
        "\n---\n",
    ]

report_content = "\n".join(lines)
report_path.write_text(report_content, encoding="utf-8")

print(report_content)
print(f"\n报告已保存到：{report_path}")
