import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load product data safely
try:
    with open("products.json", "r") as f:
        PRODUCTS = json.load(f)
except FileNotFoundError:
    print("ERROR: products.json not found!")
    PRODUCTS = []

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        user_msg = data.get("message", "")
        history = data.get("history", [])

        # Limit history to last 5 messages for faster replies
        trimmed_history = history[-5:]

        # Prepare simple product list
        product_text = "\n".join([
            f"- {p['name']}: Rich in {p['benefits']}" for p in PRODUCTS
        ])

        # System Prompt (Optimized)
        SYSTEM_PROMPT = f"""
You are a friendly, expert AI Nutritionist with deep knowledge of micronutrient deficiencies and biofortification.

🎯 GOALS:
- Naturally help users understand that symptoms like fatigue or hair loss may be linked to hidden micronutrient gaps.
- Slowly introduce biofortification after 1-2 messages — explain it simply, showing it's a natural way to improve nutrition without changing diets.
- Mention Better Nutrition products softly when relevant.

🎨 STYLE:
- Friendly, conversational, never robotic or salesy.
- Educate subtly with phrases like “Nutritionists often find…” or “Recent research suggests…”.
- Keep replies short (max 2–3 lines) + offer 2–3 clickable follow-up suggestions in every reply.

Here are your available products:
{product_text}

Always reply in this JSON format:
{{
  "reply": "Short reply here",
  "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
}}
Do NOT include any explanations or text outside this JSON. Do not write any extra words.
"""

        # Build API message chain
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in trimmed_history:
            messages.append({
                "role": "user" if msg["sender"] == "user" else "assistant",
                "content": msg["text"]
            })
        messages.append({"role": "user", "content": user_msg})

        # GPT Call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=400
        )

        ai_content = response.choices[0].message.content.strip()
        print(f"AI Response: {ai_content}")

        # Try JSON Parsing
        try:
            reply_data = json.loads(ai_content)
            if "reply" not in reply_data:
                reply_data["reply"] = ai_content
            if "suggestions" not in reply_data:
                reply_data["suggestions"] = []
        except json.JSONDecodeError:
            print("⚠️ JSON Parse Error. Using fallback.")
            reply_data = {
                "reply": ai_content,
                "suggestions": []
            }

        return jsonify(reply_data)

    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({
            "reply": "Sorry, I'm having trouble right now.",
            "suggestions": []
        }), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "products_loaded": len(PRODUCTS)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
