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

    prompt = f"""
You are an AI Nutritionist.

The user is experiencing: {user_msg}

Respond in this structure:

1. Start with a warm, friendly greeting.
2. List up to 3 possible nutritional deficiencies — use line breaks (`\\n`) and make them clear (e.g., "• Iron deficiency: ...").
3. Share 1 interesting health fact.
4. Recommend 3 Indian food remedies with reasoning — one per line using bullet points.
5. End with 1 easy lifestyle tip.

Be plain, use simple language, and **avoid markdown formatting** like * or **. Just use line breaks (`\\n`) and bullet points (•).
Use emojis where it makes sense. Be helpful and encouraging.
"""



    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
