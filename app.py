from flask import Flask, request, jsonify, render_template
import os, io
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    if not deepseek_api_key:
        return jsonify(error="未设置 DEEPSEEK_API_KEY 环境变量"), 500

    file = request.files.get("resume")
    jd_text = request.form.get("jd_text", "").strip()

    if not file:
        return jsonify(error="请上传简历文件（PDF 或 Word）"), 400
    if not jd_text:
        return jsonify(error="请粘贴 JD 内容"), 400

    resume_text = extract_text(file)

    agent = Agent(
        name="Job Application Coach",
        model=deepseek_model,
        model_settings=ModelSettings(temperature=0.2),
        instructions="""
你是一个专业的求职申请分析助手，帮助用户优化简历以匹配目标 JD。

你的任务：

## 一、拆解 JD
- 岗位一句话总结
- 核心职责（列点）
- 必备技能
- 加分技能
- 软技能要求
- 隐藏筛选条件（学历、工作年限、签证等）

## 二、简历匹配分析
- ✅ 强匹配点（直接命中）
- 🟡 中等匹配点（有相关性但表达不够）
- 🔧 可包装点（有经历但没写清楚）
- ❌ 明显缺口
- ⚠️ Recruiter 可能担心的风险

## 三、匹配度评分
- 综合评分：X / 100
- 评分依据（2-3 句）

## 四、简历修改建议
- **Summary**：给出具体的改写建议或示例
- **Skills**：建议排序和补充
- **Experience Bullets**：针对每条重要经历给出改写示例
- **Projects**：建议重排顺序或补充描述

## 五、补强路线
- 缺少的关键技能
- 建议学习资源或项目
- 未来 7 天行动计划
- 未来 30 天行动计划

---
规则：
- 不编造用户没有的经历
- 可包装的明确说"可以包装，但不能夸大"
- 输出中文
- 具体、直接、可执行
""",
    )

    prompt = f"""
请根据以下 JD 和简历，做完整的匹配分析、简历优化建议和补强路线。

【JD】
{jd_text}

【简历】
{resume_text}
"""

    result = Runner.run_sync(agent, prompt)
    return jsonify(analysis=result.final_output)


@app.route("/api/plan", methods=["POST"])
def plan():
    if not deepseek_api_key:
        return jsonify(error="未设置 DEEPSEEK_API_KEY 环境变量"), 500

    file = request.files.get("resume")
    jd_text = request.form.get("jd_text", "").strip()

    if not file or not jd_text:
        return jsonify(error="缺少简历或 JD"), 400

    resume_text = extract_text(file)

    agent = Agent(
        name="Learning Plan Generator",
        model=deepseek_model,
        model_settings=ModelSettings(temperature=0.3),
        instructions="""
你是一个职业发展规划师，根据候选人的简历和目标 JD，制定具体可执行的学习提升计划。

输出结构：

## 一、技能差距分析
列出候选人与 JD 要求之间最关键的 3–5 个技能差距，每条说明为什么重要。

## 二、推荐认证 & 课程
针对每个差距，推荐：
- 具体认证（如 AWS Certified Developer、Google Data Analytics Certificate 等）
- 具体课程或学习资源（Coursera / Udemy / 官方文档 / YouTube）
- 预计完成时间

## 三、7 天冲刺计划
按天列出，每天包括：
- 今日目标
- 具体任务（2–4 条，可执行）
- 预计耗时
- 完成标准（怎么算做完了）

## 四、30 天深化计划
按周列出（第 1–4 周），每周包括：
- 本周主题
- 核心任务
- 要完成的项目或作业
- 里程碑检查点（本周结束时应达到什么水平）

## 五、项目建议
推荐 2–3 个可以写进简历的具体项目，说明：
- 项目名称和描述
- 用到哪些技能
- 做到什么程度才能写进简历

---
规则：
- 所有推荐的资源必须是真实存在的
- 时间估计要现实，不要过于乐观
- 输出中文
- 具体、直接、可执行
""",
    )

    prompt = f"""
请根据以下 JD 和简历，制定详细的技能提升和学习计划。

【JD】
{jd_text}

【简历】
{resume_text}
"""

    result = Runner.run_sync(agent, prompt)
    return jsonify(plan=result.final_output)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
