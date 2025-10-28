from flask import Flask, request, jsonify
from openai import OpenAI
import os
import requests
import json

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "Feishu AI Webhook 已成功部署 💫", 200

@app.route("/feishu_webhook", methods=["POST"])
def feishu_webhook():
    try:
        # ✅ 兼容所有请求体解析
        raw_data = request.data.decode("utf-8", errors="ignore")
        print(f"🪶 原始请求体: {raw_data}")

        try:
            data = json.loads(raw_data)
        except Exception:
            try:
                data = request.form.to_dict()  # 表单兼容
            except Exception:
                data = {}
        print(f"✅ 解析后数据: {data}")

        # 安全取值函数
        def safe_str(value):
            if isinstance(value, dict):
                return value.get("text") or value.get("value") or str(value)
            return str(value) if value else ""

        product_name = safe_str(data.get("product_name"))
        competitor_url = safe_str(data.get("competitor_url"))

        # 没拿到 product_name 的备用方案
        if not product_name and "text" in data:
            product_name = data["text"]

        # 抓取竞品网页
        competitor_info = ""
        if competitor_url:
            try:
                resp = requests.get(competitor_url, timeout=6)
                competitor_info = resp.text[:1000]
            except:
                competitor_info = "无法访问竞品链接。"

        # Prompt
        prompt = f"""
        你是一名俄语跨境电商文案专家，请根据以下信息生成适用于 Ozon 或 Yandex 的产品标题与描述：
        - 产品中文名称：{product_name}
        - 竞品网页内容（部分）：{competitor_info}

        输出格式如下：
        ---
        标题（俄语）：
        描述（俄语）：
        ---
        """

        # 调用 OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个擅长撰写俄语电商文案的AI助手。"},
                {"role": "user", "content": prompt}
            ]
        )

        reply = completion.choices[0].message.content.strip()
        print(f"✅ 生成成功: {reply}")

        # 提取结果
        result = {
            "title": reply.split("标题（俄语）：")[-1].split("描述（俄语）：")[0].strip(),
            "desc": reply.split("描述（俄语）：")[-1].strip()
        }

        return jsonify({"result": result})

    except Exception as e:
        print(f"❌ 出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/healthz")
def health_check():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
