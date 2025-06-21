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
You are an AI Nutritionist who specializes in identifying micronutrient deficiencies and educating users about biofortification.

The user is experiencing: {user_msg}

Your response should:
1. Greet the user warmly.
2. Identify up to 3 relevant micronutrient deficiencies linked to their concern.
3. Explain the concept of biofortification simply and clearly.
4. End with an encouraging or practical tip related to daily nutrition.

Important:
• Do NOT recommend or mention any specific products.
• Do NOT use markdown (e.g. *, **).
• Use simple line breaks (\\n) and bullet points (•) for formatting.
• Keep the tone helpful, friendly, and conversational.
• Use emojis sparingly to maintain a human tone.
"""




    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
