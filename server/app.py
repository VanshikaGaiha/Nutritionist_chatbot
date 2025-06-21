import os
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

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "AI Nutritionist Backend"})

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    user_msg = data.get("message", "")
    history = data.get("history", [])

    formatted_history = "\n".join([f"{m['sender'].capitalize()}: {m['text']}" for m in history])

    prompt = f"""
You are an AI Nutritionist chatbot helping users understand their symptoms through the lens of micronutrient deficiencies and biofortification.

Conversation so far:
{formatted_history}
User just said: "{user_msg}"

Now generate the AI's reply.

Guidelines:
1. If this is the user's first message (no prior history), start with a friendly greeting.
2. Otherwise, skip the greeting and respond in a flowing, conversational tone.
3. Always aim to guide the conversation toward identifying possible micronutrient deficiencies (e.g., iron, vitamin B12, vitamin D, zinc, magnesium).
4. Introduce the concept of biofortification *organically* — only if it fits naturally based on the user’s message or your previous response.
5. Recommend helpful Indian food sources to manage such deficiencies.
6. End with an encouraging nudge to keep chatting — like "Want to explore your diet a bit more?" or "Tell me what you usually eat in a day."
7. Avoid repeating the same facts too soon — stay human, keep it engaging.

Keep the language warm, friendly, and simple. Use emojis where appropriate. Do NOT use markdown or special formatting.
"""

    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
