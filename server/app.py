import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure OpenAI - Updated to new format
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load product data with error handling
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

        print(f"Received message: {user_msg}")  # Debug log
        print(f"API Key present: {bool(client.api_key)}")  # Debug log

        # Prepare product text with prices
        product_text = "\n".join([
            f"- {p['name']} ({', '.join(p['variants'])}, Price: ₹{p['price']}): {p['benefits']}" 
            for p in PRODUCTS
        ])

        # Build chat history
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an empathetic AI Nutritionist specialized in micronutrient deficiencies. "
                    "Gently make users aware that common symptoms like fatigue, hair loss, or low energy may relate to hidden micronutrient deficiencies. "
                    "Subtly introduce the benefits of biofortification (foods naturally enhanced with Iron, Zinc, etc.) without sounding forceful.\n\n"
                    "Reply concisely (max 2-3 lines) with friendly, clear advice.\n\n"
                    "Always suggest 2-3 clickable follow-up options based on the user's query.\n\n"
                    "STRICTLY reply ONLY in this JSON format:\n"
                    "{\n"
                    "  \"reply\": \"Short reply here.\",\n"
                    "  \"suggestions\": [\"Suggestion 1\", \"Suggestion 2\", \"Suggestion 3\"]\n"
                    "}\n\n"
                    "NEVER add extra words or markdown outside this JSON.\n\n"
                    f"Here are Better Nutrition's products you can mention if relevant:\n{product_text}"
                )
            }
        ]

        # Add past conversation
        for msg in history:
            messages.append({
                "role": "user" if msg["sender"] == "user" else "assistant",
                "content": msg["text"]
            })

        messages.append({"role": "user", "content": user_msg})

        # Updated OpenAI API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=400
        )

        ai_content = response.choices[0].message.content.strip()
        print(f"AI Response: {ai_content}")  # Debug log

        # Parse AI JSON reply safely
        try:
            reply_data = json.loads(ai_content)
            if "suggestions" not in reply_data:
                reply_data["suggestions"] = []
        except json.JSONDecodeError:
            print(f"JSON Parse Error: {ai_content}")  # Debug log
            reply_data = {
                "reply": "Sorry, I couldn't process that. Let's try again!",
                "suggestions": []
            }

        return jsonify(reply_data)

    except Exception as e:
        print(f"ERROR in analyze: {str(e)}")  # Debug log
        return jsonify({
            "reply": "Sorry, I'm having trouble processing your request.",
            "suggestions": []
        }), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy", 
        "service": "AI Nutritionist GPT-3.5 Backend",
        "api_key_present": bool(client.api_key),
        "products_loaded": len(PRODUCTS)
    })

if __name__ == "__main__":
    print("Starting server...")
    print(f"API Key present: {bool(client.api_key)}")
    print(f"Products loaded: {len(PRODUCTS)}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)