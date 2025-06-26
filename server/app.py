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
You are an empathetic AI Nutritionist guiding users to understand their health symptoms and explore nutritional improvements. Keep the tone friendly, conversational, and non-pushy. The user should *feel heard*, *gently educated*, and *naturally guided* toward better food choices.

Conversation so far:
{formatted_history}
User just said: "{user_msg}"

--- Guidelines ---
1. Do NOT greet if it's not the first user message.
2. Ask questions to understand the user's symptoms — gently nudge them to think about common deficiencies (iron, zinc, B12, vitamin D).
3. Slowly connect deficiencies to daily diet staples like atta, rice, dal — make it feel like an insightful realization, not advice.
4. Introduce *biofortification* as a natural solution — explain simply, e.g., "Did you know some staples are now naturally enriched from the seed level?"
5. Only after 4–6 user inputs, and if the context fits, *softly* mention Better Nutrition products as a smarter option — no forceful pitch.
6. If the user is skeptical or negative, don’t argue. Stay educational and calm — clarify with logic, not persuasion.
7. Keep it short (3–6 sentences), use emojis naturally, and avoid buzzwords or marketing terms. No markdown or formatting.

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
