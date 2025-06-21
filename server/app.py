import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
CORS(app)

# Gemini API setup
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

    # Build conversation history as text
    formatted_history = ""
    for turn in history:
        if turn["sender"] == "user":
            formatted_history += f"User: {turn['text']}\n"
        else:
            formatted_history += f"AI: {turn['text']}\n"

    prompt = f"""
You are a warm, helpful AI Nutritionist in a chat conversation. Use the full chat history below to understand context and provide helpful responses. Focus on micronutrient deficiencies and natural dietary solutions. Introduce the concept of biofortification **only if relevant to the user's concern or question**, not randomly.

Chat History:
{formatted_history}
User: {user_msg}

Respond with:
• A friendly opening.
• Up to 3 micronutrient deficiencies related to the symptoms (with explanations).
• A simple, clear explanation of biofortification only if appropriate.
• 2–3 Indian food suggestions as remedies (with reasons).
• One practical tip or lifestyle advice.
Avoid markdown. Use line breaks and emojis where useful. Be natural and conversational.
"""

    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")

    return jsonify({"response": clean_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
