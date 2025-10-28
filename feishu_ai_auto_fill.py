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


# 兼容飞书表格字段（有时会传对象）
def safe_str(value):
    if isinstance(value, dict):
        return value.get("text", "") or value.get("value", "") or str(value)
    return str(value) if value else ""


@app.route("/feishu_webhook", methods=["POST"])
def feishu_webhook():
    try:
        data = request.get_json(force=True)
        if isinstance(data, str):  # 🔥 关键新增
            import json
            data = json.loads(data)
        print(f"📩 接收到数据: {data}")

        competitor_url = safe_str(data.get("competitor_url"))
        if not competitor_url:
            return jsonify({"error": "缺少竞品链接 competitor_url"}), 400

        # 抓取竞品网页部分内容
        competitor_info = ""
        try:
            resp = requests.get(competitor_url, timeout=6)
            competitor_info = resp.text[:1000]
        except:
            competitor_info = "无法访问竞品链接。"

        # 构造 prompt
        prompt = f"""
        你是一名精通俄语的跨境电商文案专家，请根据以下竞品内容，生成适用于 Ozon 或 Yandex 的俄语产品标题与描述。
        要求如下：
        - 标题（俄语）需控制在 150 字以内。
        - 描述（俄语）需控制在 1000 字以内。
        - 保持自然语气，适合俄语母语消费者阅读。
        - 如果抓取网页失败，也请基于逻辑合理生成内容。

        竞品网页内容（部分）：
        {competitor_info}

        输出格式如下：
        ---
        标题（俄语）：
        描述（俄语）：
        ---
        """

        # 调用 OpenAI 接口
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # 可改为 gpt-4o
            messages=[
                {"role": "system", "content": "你是一名俄语跨境电商文案专家。"},
                {"role": "user", "content": prompt}
            ]
        )

        reply = completion.choices[0].message.content.strip()
        print(f"✅ 生成成功: {reply}")

        # 拆分结果
        title_part = reply.split("标题（俄语）：")[-1].split("描述（俄语）：")[0].strip()
        desc_part = reply.split("描述（俄语）：")[-1].strip()

        return jsonify({
            "result": {
                "title": title_part,
                "desc": desc_part
            }
        })

    except Exception as e:
        print(f"❌ 出错: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/healthz")
def health_check():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
