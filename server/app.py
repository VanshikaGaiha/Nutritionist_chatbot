import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Flask app
app = Flask(__name__)
CORS(app)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Load product data
with open("products.json", "r") as f:
    PRODUCTS = json.load(f)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    user_msg = data.get("message", "")
    history = data.get("history", [])

    formatted_history = "\n".join([f"{m['sender'].capitalize()}: {m['text']}" for m in history])

    # Prepare product text
    product_text = "\n".join(
  [f"- {p['name']} ({', '.join(p['variants'])}, ₹{p['price']}): {p['benefits']}" for p in PRODUCTS]
)


    prompt = f"""
    You are an empathetic AI Nutritionist chatbot helping users with their health concerns.

    Instructions:
    1. Reply concisely (max 2–3 sentences).
    2. Suggest 2–3 smart reply options (follow-up questions or answers the user might click on).
    3. ALWAYS reply in strict JSON format like this:
    {{
      "reply": "Short reply here.",
      "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
    }}
    ⚠️ No additional text, no explanations, no markdown — only this JSON response.

    Better Nutrition Products:
    {product_text}

    Conversation so far:
    {formatted_history}
    User just said: "{user_msg}"
    """

    response = model.generate_content(prompt)

    # Auto-extract JSON safely (even if Gemini adds extra text)
    raw_text = response.text.strip()
    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if match:
        json_string = match.group(0)
        try:
            reply_data = json.loads(json_string)
        except json.JSONDecodeError:
            reply_data = {
                "reply": "Sorry, I couldn't understand that. Let's try again.",
                "suggestions": []
            }
    else:
        reply_data = {
            "reply": "Sorry, I couldn't understand that. Let's try again.",
            "suggestions": []
        }

    return jsonify(reply_data)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "AI Nutritionist Backend"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
