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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
