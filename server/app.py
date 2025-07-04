import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load product data
with open("products.json", "r") as f:
    PRODUCTS = json.load(f)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    user_msg = data.get("message", "")
    history = data.get("history", [])

    product_text = "\n".join([
        f"- {p['name']} ({', '.join(p['variants'])}): {p['benefits']}" for p in PRODUCTS
    ])

    # Build chat history
    messages = [
        {
            "role": "system",
            "content": (
                "You are a friendly AI Nutritionist. "
                "Reply concisely (max 2-3 lines) with practical, friendly suggestions. "
                "Then suggest 2-3 helpful follow-up buttons the user can click on, based on their message. "
                "Reply ONLY in this exact JSON format:\n"
                "{\n"
                "  \"reply\": \"Short reply here.\",\n"
                "  \"suggestions\": [\"Suggestion 1\", \"Suggestion 2\", \"Suggestion 3\"]\n"
                "}\n"
                "NEVER add extra words or markdown outside this JSON.\n"
                f"\nHere is your product list:\n{product_text}"
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

    try:
        # GPT-3.5 API call
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=400
        )

        ai_content = response['choices'][0]['message']['content'].strip()

        # Parse AI JSON reply safely
        try:
            reply_data = json.loads(ai_content)
            # Fallback if suggestions missing
            if "suggestions" not in reply_data:
                reply_data["suggestions"] = []
        except json.JSONDecodeError:
            reply_data = {
                "reply": "Sorry, I couldn't process that. Let's try again!",
                "suggestions": []
            }

    except Exception as e:
        reply_data = {
            "reply": "Sorry, I'm having trouble reaching the server.",
            "suggestions": []
        }

    return jsonify(reply_data)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "AI Nutritionist GPT-3.5 Backend"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
