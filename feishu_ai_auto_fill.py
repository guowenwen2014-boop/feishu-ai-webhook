from flask import Flask, request, jsonify
from openai import OpenAI
import os
import requests

app = Flask(__name__)

# 从环境变量读取 OpenAI 密钥
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "Feishu AI Webhook 已成功部署 💫", 200


@app.route("/feishu_webhook", methods=["POST"])
def feishu_webhook():
    try:
        data = request.get_json(force=True)
        print(f"🪶 接收到数据: {data}")

        # 兼容飞书自动化传递对象形式
        def safe_str(value):
            if isinstance(value, dict):
                return value.get("text", "") or value.get("value", "") or str(value)
            return str(value) if value else ""

        product_name = safe_str(data.get("product_name"))
        competitor_url = safe_str(data.get("competitor_url"))

        # 如果飞书只传了一个字段，也兼容 text
        if not product_name and "text" in data:
            product_name = data["text"]

        # 可选：尝试抓取竞品网页（只取部分文本）
        competitor_info = ""
        if competitor_url:
            try:
                resp = requests.get(competitor_url, timeout=6)
                competitor_info = resp.text[:1000]
            except:
                competitor_info = "无法访问竞品链接。"

        # 构造 prompt
        prompt = f"""
        你是一名俄语跨境电商文案专家，请根据以下信息生成适用于 Ozon 或 Yandex 的产品标题与描述：
        - 产品中文名称：{product_name}
        - 竞品网页内容（可能部分）：{competitor_info}

        输出格式如下：
        ---
        标题（俄语）：
        描述（俄语）：
        ---
        """

        # 调用 OpenAI 新版接口
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # 可改成 gpt-4o
            messages=[
                {"role": "system", "content": "你是一个擅长撰写俄语电商文案的AI助手。"},
                {"role": "user", "content": prompt}
            ]
        )

        reply = completion.choices[0].message.content.strip()
        print(f"✅ 生成成功：{reply}")

        # ✅ 返回结构化 JSON（飞书自动写入表格）
        return jsonify({
            "result": {
                "title": reply.split("标题（俄语）：")[-1].split("描述（俄语）：")[0].strip(),
                "desc": reply.split("描述（俄语）：")[-1].strip()
            }
        })

    except Exception as e:
        print(f"❌ 出错：{str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/healthz")
def health_check():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
