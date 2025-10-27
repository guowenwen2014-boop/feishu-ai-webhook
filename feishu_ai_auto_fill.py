from flask import Flask, request, jsonify
from openai import OpenAI
import os
import requests

app = Flask(__name__)

# 从环境变量读取你的 OpenAI 密钥
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "Feishu AI Webhook 已成功部署 💫", 200


@app.route("/feishu_webhook", methods=["POST"])
def feishu_webhook():
    try:
        data = request.get_json()
        product_name = data.get("product_name", "")
        competitor_url = data.get("competitor_url", "")

        # 如果飞书只传了一个字段，也兼容处理
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
        你是一名俄语跨境电商文案专家，请根据以下信息生成适用于Ozon或Yandex的产品标题与描述：
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
            model="gpt-4o-mini",  # 可以改成 gpt-4o 或 gpt-3.5-turbo
            messages=[
                {"role": "system", "content": "你是一个擅长撰写俄语电商文案的AI助手。"},
                {"role": "user", "content": prompt}
            ]
        )

        reply = completion.choices[0].message.content.strip()
        print(f"✅ 生成成功：{reply}")

        return jsonify({"result": reply})

    except Exception as e:
        print(f"❌ 出错：{str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    @app.route("/healthz")
    def health_check():
        return "ok", 200

    app.run(host="0.0.0.0", port=10000, debug=False)
