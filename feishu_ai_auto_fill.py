from flask import Flask, request, jsonify
import openai
import os

# 从环境变量中读取 OpenAI API Key（Render会自动注入）
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

@app.route("/feishu_webhook", methods=["POST"])
def feishu_webhook():
    try:
        data = request.get_json()
        print("📩 收到来自飞书的请求:", data)

        product_name = data.get("product_name", "")
        competitor_url = data.get("competitor_url", "")

        # 构造提示词
        prompt = f"""
        请参考以下信息，用俄语生成产品标题和描述：
        产品名称：{product_name}
        竞品链接：{competitor_url}
        """

        # 调用 OpenAI 生成
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        ai_text = completion.choices[0].message["content"].strip()
        print("✨ AI 生成内容:", ai_text)

        return jsonify({
            "message": "AI生成成功",
            "result": ai_text
        })

    except Exception as e:
        print("❌ 出错了:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)