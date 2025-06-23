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

# Load product data from JSON
with open("products.json") as f:
    product_data = json.load(f)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "AI Nutritionist Backend"})

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    user_msg = data.get("message", "")
    history = data.get("history", [])

    formatted_history = "\n".join([f"{m['sender'].capitalize()}: {m['text']}" for m in history])
    product_snippets = "\n".join([
        f"- {item['name']}: {item['benefits']}, best for {item['uses']}."
        for item in product_data["products"]
    ])

    prompt = f"""
You are an AI Nutritionist chatbot for a brand called Better Nutrition. Your job is to:
1. Help users realize they may have **micronutrient deficiencies** based on their symptoms or lifestyle.
2. **Focus on dietary staples** like atta, rice, and daliya.
3. **Gradually introduce** the concept of **biofortification** (not suddenly or forcefully).
4. Aim to keep the conversation **around 10 user messages**. Close with a polite summary or invitation to explore products.
5. Politely **recommend Better Nutrition products** if the user is open to solutions. Mention product benefits **only when relevant**.
6. If the user is skeptical or negative, handle it with **empathy and education**, not arguments.
7. If this is the user's first message, greet them briefly. Avoid repeating greetings in follow-ups.

Conversation so far:
{formatted_history}

User just said:
"{user_msg}"

Here are the brand products you can gently mention if appropriate:
{product_snippets}

Now generate the next AI message.
Keep it warm, educational, and human-like. Avoid repetition and don’t push products forcefully. Use emojis if it fits.
"""

    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
