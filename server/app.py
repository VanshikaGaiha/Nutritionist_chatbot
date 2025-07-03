import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

with open("products.json", "r") as f:
    PRODUCTS = json.load(f)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    user_msg = data.get("message", "")
    history = data.get("history", [])

    formatted_history = "\n".join([f"{m['sender'].capitalize()}: {m['text']}" for m in history])
    product_text = "\n".join(
        [f"- {p['name']} ({', '.join(p['variants'])}): {p['benefits']}" for p in PRODUCTS]
    )

    prompt = f"""
You are an empathetic AI Nutritionist helping users with their health concerns.

Instructions:
1. Reply in max 2–3 sentences.
2. Suggest 2–3 clickable follow-ups.
3. Always respond in strict JSON format:
{{
  "reply": "Your reply here.",
  "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
}}
⚠️ No extra text, no markdown.

Better Nutrition Products:
{product_text}

Conversation so far:
{formatted_history}
User just said: "{user_msg}"
"""

    response = model.generate_content(prompt)
    try:
        reply_data = json.loads(response.text.strip())
    except json.JSONDecodeError:
        reply_data = {
            "reply": "Sorry, I couldn't understand that.",
            "suggestions": []
        }

    # Auto add Buy Now button after 5 user messages
    user_msgs = sum(1 for msg in history if msg["sender"] == "user")
    reply_data["buy_now"] = user_msgs >= 5

    return jsonify(reply_data)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
