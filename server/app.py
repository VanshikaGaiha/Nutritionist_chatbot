import os
import json
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
    [f"- {p['name']} ({p['weight']}): {p['benefits']}" for p in PRODUCTS]
    )


    prompt = f"""
You are an AI Nutritionist working for Better Nutrition. Your job is to help users discover if they might have micronutrient deficiencies and learn about food-based solutions — including, when relevant, biofortified staples from Better Nutrition.

Conversation so far:
{formatted_history}
User just said: "{user_msg}"

Your reply must follow these rules:

1. If this is the user's **first message**, greet them.
2. After that, **do not greet again** — just respond in a flowing, chatty tone.
3. Pay close attention to what the user is saying — don’t force biofortification or product suggestions.
4. **Focus first** on understanding symptoms. Ask curious follow-ups (e.g., “How often do you feel that?” or “What do you usually eat in a day?”)
5. If the user shares staples like rice, atta, dal — then **gradually** introduce biofortification and products. Only **after 4–6 user turns**.
6. When recommending Better Nutrition products, explain how they’re **different in context** (e.g., “biofortified with more iron to help with fatigue”).
7. If the user is skeptical or questions the product, respond calmly and educationally — **never defensive**.
8. End with an open question to keep the conversation going. Never ask the user to “buy” or “try now”.

Better Nutrition Products (for reference):
{product_text}

Style: 3–5 sentences, warm, helpful, curious. Use emojis where natural. Don’t use markdown.
"""


    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "AI Nutritionist Backend"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
