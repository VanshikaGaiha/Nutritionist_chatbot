import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Setup Flask app
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

    # Format conversation history for context
    formatted_history = "\n".join([f"{msg['sender'].capitalize()}: {msg['text']}" for msg in history])

    prompt = f"""
You are an AI Nutritionist assistant chatting with a user in a casual, friendly way.

Here is the conversation so far:
{formatted_history}
User: {user_msg}

Your job:
- Respond naturally like a person would in an ongoing chat.
- If the user asks a follow-up (like \"sure\", \"what else\", or \"am I eating wrong?\"), build on what you said before.
- If the user is showing interest in their diet, ask clarifying questions or offer personalized advice.
- ONLY repeat explanations like deficiencies or biofortification if they haven’t been explained yet.

Keep responses short, friendly, and feel like a back-and-forth conversation. Use emojis where it fits, avoid repeating full explanations again.
"""

    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
