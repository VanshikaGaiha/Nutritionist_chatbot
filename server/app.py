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
        [f"- {p['name']} ({', '.join(p['variants'])}): {p['benefits']}" for p in PRODUCTS]
    )

    prompt = f"""
You are an AI Nutritionist helping users understand possible micronutrient deficiencies and how their diet can improve with biofortified foods.

Conversation so far:
{formatted_history}
User just said: "{user_msg}"

--- Guidelines for your reply ---
1. Start with a warm, conversational tone.
2. Only greet the user if this is the *first* message.
3. Guide the user to think about symptoms as signs of micronutrient deficiencies (like zinc, iron, B12, vitamin D).
4. Gradually explain the concept of biofortification — naturally enriched staples like rice, atta, daliya, etc.
5. If the user is receptive and the context fits (after ~4–6 user messages), you may softly recommend Better Nutrition products.
6. Do not force product promotion. Make it feel like helpful advice.
7. If the user is negative or skeptical, calmly explain facts and keep an educational tone.

Available Better Nutrition products:
{product_text}

Respond in 3-6 sentences. Add emojis where suitable. Do not use markdown or special formatting.
"""

    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "AI Nutritionist Backend"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
