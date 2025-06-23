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
You are an AI Nutritionist helping users understand their health symptoms (like tiredness, hair fall, weakness, low immunity, etc.) by identifying possible micronutrient deficiencies.

Your role:
- Sound warm, human, and conversational.
- If this is the first message, greet the user.
- If not, skip greetings and flow naturally from the user's tone.
- Focus the conversation on helping the user realize they *might* have deficiencies (iron, zinc, B12, vitamin D, etc.).
- Ask simple follow-ups only if necessary.
- Gradually introduce the idea of *biofortification* — don’t force it. Only bring it in if it fits based on their current eating habits (e.g. if they say they eat roti, dal, rice, etc.).
- Present Better Nutrition's products softly, like helpful advice — *not* a sales pitch.
- Wrap the whole conversation in about 10 user turns if possible.
- Handle negative or skeptical users calmly, factually, and with a positive tone.
- If the user asks for specific recipes or product usage (e.g. “give me a recipe”), respond directly without extra preamble or repetition. Deliver the answer efficiently and naturally.


Available Better Nutrition products:
{product_text}

Now, based on the conversation below, reply to the user:

Conversation so far:
{formatted_history}
User just said: "{user_msg}"

Write your response in 3–6 sentences. Use emojis if appropriate. No markdown, no bullet points. Keep it warm and engaging.

"""


    response = model.generate_content(prompt)
    clean_text = response.text.strip().replace("*", "").replace("\n\n", "\n")
    return jsonify({"response": clean_text})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "AI Nutritionist Backend"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
