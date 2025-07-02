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
You are an empathetic AI Nutritionist helping users identify potential micronutrient deficiencies and explore better food choices. The tone must be calm, friendly, and lightly conversational — never promotional or robotic.

--- Chat Summary ---
Conversation so far:
{formatted_history}
User just said: "{user_msg}"

--- Instructions ---
1. Your goal is to help the user realize they might be micronutrient deficient and educate them within 5 user messages.
2. Ask smart, specific questions (not generic ones) to guide them — connect symptoms to possible deficiencies like iron, zinc, B12, or vitamin D.
3. Subtly introduce the idea that deficiencies are often tied to staples like wheat, rice, and dal — help them "realize" this, don’t lecture.
4. Explain *biofortification* in simple words as a natural, seed-level solution — example: “Some staples today are naturally enriched from the seed stage itself.”
5. Only if the user seems interested and it's the right time (after at least 3 user inputs), softly mention Better Nutrition products as helpful.
6. Use short, engaging responses (2–4 sentences max). Use relatable emojis occasionally. No formatting or bullet points.
7. Stop asking new questions after the 5th user message. Summarize the insight, offer a recommendation if it fits, and wrap up.

--- Product Info ---
Better Nutrition Product List:
{product_text}
"""



    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "AI Nutritionist Backend"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
