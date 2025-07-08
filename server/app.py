import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate environment variables
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables")

app = Flask(__name__)
CORS(app, resources={
    r"/analyze": {"origins": ["http://localhost:3000", "https://nutritionist-chatbot-frontend.onrender.com"]},
    r"/health": {"origins": "*"}
})

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load product data
try:
    with open("products.json", "r") as f:
        PRODUCTS = json.load(f)
except FileNotFoundError:
    logger.error("ERROR: products.json not found!")
    PRODUCTS = []

if not PRODUCTS:
    logger.warning("No products loaded - running in demo mode")

def process_history(history):
    if not history or not isinstance(history, list):
        return []
    
    processed_messages = []
    total_tokens = 0

    for msg in reversed(history[-10:]):
        try:
            text = msg.get("message") or msg.get("text") or ""
            sender = msg.get("sender") or msg.get("role") or "user"
            if not text.strip():
                continue
            role = "user" if sender.lower() in ["user", "human"] else "assistant"
            estimated_tokens = len(text) // 4
            if total_tokens + estimated_tokens > 1500:
                break
            processed_messages.append({
                "role": role,
                "content": text.strip()
            })
            total_tokens += estimated_tokens
        except (KeyError, TypeError, AttributeError):
            continue

    return list(reversed(processed_messages))

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        user_msg = data.get("message", "")
        history = data.get("history", [])

        if not user_msg or not user_msg.strip():
            return jsonify({"error": "Message cannot be empty"}), 400

        if len(user_msg) > 1000:
            return jsonify({"error": "Message too long"}), 400

        if history and not isinstance(history, list):
            return jsonify({"error": "Invalid history format"}), 400

        processed_history = process_history(history)
        logger.info(f"Processed {len(processed_history)} valid messages")

        product_text = "\n".join([
            f"- {p['name']}: Rich in {p['benefits']} - ₹{p.get('price', 'N/A')}" for p in PRODUCTS
        ])

        # ✅ Updated system prompt — no suggestions, natural guidance
        SYSTEM_PROMPT = f"""
You are a helpful, friendly AI Nutritionist designed to assist users with their dietary symptoms.

🎯 Your goals:
- Identify possible micronutrient deficiencies based on symptoms (e.g., fatigue, hair loss, low stamina)
- Provide food-based solutions first (natural diet, conventional foods)
- Gently introduce biofortification only if relevant — do not push it
- Mention Better Nutrition products naturally if the user seems interested
- Keep replies short (2–3 sentences), friendly, and actionable

🛍️ If recommending a product, include its benefit and price like this:
  "You could also try our Biofortified Ragi Atta (₹170), which supports bone and gut health."

🧠 Style guide:
- Warm, conversational tone — no robotic or overly formal responses
- Avoid any JSON, bullet points, or formatting
- Do not include follow-up suggestions or prompts

🛒 Product List:
{product_text}

Respond ONLY in plain text. One friendly response per user message. No JSON, no markdown, no lists.
"""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(processed_history)
        messages.append({"role": "user", "content": user_msg})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=300,
            timeout=30
        )

        ai_content = response.choices[0].message.content.strip()
        logger.info(f"AI Response: {ai_content}")

        return jsonify({"reply": ai_content})

    except Exception as e:
        if "openai" in str(type(e)).lower():
            logger.error(f"OpenAI API Error: {e}")
            return jsonify({"reply": "I'm having trouble connecting to my knowledge base. Please try again."}), 503
        else:
            logger.error(f"Unexpected Error: {e}")
            return jsonify({"reply": "Something went wrong. Please try again."}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "products_loaded": len(PRODUCTS),
        "max_history_messages": 10,
        "max_tokens_estimate": 2000
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
