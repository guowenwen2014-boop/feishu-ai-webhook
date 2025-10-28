from flask import Flask, request, jsonify
from openai import OpenAI
import os
import requests
import json

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "Feishu AI Webhook 极简版 💫 已部署成功", 200

@app.route("/feishu_webhook", methods=["POST"])
def feishu_webhook():
    try:
        # ✅ 解析飞书传入数据
        data = request.get_json(force=True)
        competitor_url = data.get("competitor_url", "")

        if not competitor_url:
            return jsonify({"error": "缺少竞品链接 competitor_url"}), 400

        # ✅ 获取竞品网页文本内容
        try:
            resp = requests.get(competitor_url, timeout=6)
            competitor_info = resp.text[:2000]  # 限制长度避免超长
        except:
            competitor_info = "无法访问竞品链接。"

        # ✅ 构造 prompt，增加字数限制说明
        prompt = f"""
        你是一名俄语跨境电商文案专家。
        请根据以下网页内容，为 Ozon 平台生成“俄语产品标题”和“俄语产品描述”。
        要求：
        - 俄语标题必须在150个字符以内；
        - 俄语描述必须在1000个字符以内；
        - 内容自然流畅、可读性强；
        - 避免重复、关键词堆砌。

        以下是竞品网页内容（部分）：
        {competitor_info}

        输出格式如下（请严格遵守）：
        ---
        标题（俄语）：
        描述（俄语）：
        ---
        """

        # ✅ 调用 OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个擅长撰写俄语电商文案的AI助手。"},
                {"role": "user", "content": prompt}
            ]
        )

        reply = completion.choices[0].message.content.strip()
        print(f"✅ 生成成功: {reply}")

        # ✅ 拆分结果（飞书自动填入两个单元格）
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
