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
You are an AI Nutritionist from Better Nutrition. Help users understand if they may have micronutrient deficiencies and how their everyday food choices can improve their health — without sounding forceful or promotional.

Conversation so far:
{formatted_history}
User just said: "{user_msg}"

Your task:
1. Start friendly only if this is the first user message.
2. Listen to what the user is saying. Don’t push biofortification or products unless it makes sense based on their symptom or question.
3. Help them reflect on possible micronutrient deficiencies — iron, zinc, vitamin D, B12, etc. — especially if they mention tiredness, hair loss, fatigue, poor immunity, etc.
4. If the user talks about food, diet, or staples like atta or rice — then *naturally* introduce the idea of biofortification and Better Nutrition’s products.
5. Mention products casually — only after 4–6 messages, and only when relevant. Avoid any sales tone. Make it sound like useful advice.
6. If the user is skeptical or negative, stay calm and explain benefits kindly and clearly.
7. End each reply with an open question that encourages continued conversation, unless the user is clearly done.

Available products:
{product_text}

Tone: warm, friendly, intelligent, conversational. Use 3–5 sentences. Emojis are okay. No markdown.
"""

    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "AI Nutritionist Backend"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
