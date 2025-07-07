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
    r"/analyze": {"origins": ["http://localhost:3000", "https://nutritionist-chatbot-frontend.onrender.com/"]},
    r"/health": {"origins": "*"}
})

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load product data safely
try:
    with open("products.json", "r") as f:
        PRODUCTS = json.load(f)
except FileNotFoundError:
    logger.error("ERROR: products.json not found!")
    PRODUCTS = []

if not PRODUCTS:
    logger.warning("No products loaded - running in demo mode")

def process_history(history):
    """Process and validate conversation history"""
    if not history or not isinstance(history, list):
        return []
    
    processed_messages = []
    total_tokens = 0  # Rough estimate
    
    for msg in reversed(history[-10:]):  # Last 10 messages, reversed for recency
        try:
            # Handle different possible formats
            text = msg.get("message") or msg.get("text") or ""
            sender = msg.get("sender") or msg.get("role") or "user"
            
            if not text.strip():
                continue
                
            # Normalize sender names
            role = "user" if sender.lower() in ["user", "human"] else "assistant"
            
            # Rough token estimation (4 chars = ~1 token)
            estimated_tokens = len(text) // 4
            if total_tokens + estimated_tokens > 1500:  # Leave room for system prompt
                break
                
            processed_messages.append({
                "role": role,
                "content": text.strip()
            })
            total_tokens += estimated_tokens
            
        except (KeyError, TypeError, AttributeError):
            continue  # Skip malformed messages
    
    return list(reversed(processed_messages))  # Restore chronological order

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        user_msg = data.get("message", "")
        history = data.get("history", [])

        # Input validation
        if not user_msg or not user_msg.strip():
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if len(user_msg) > 1000:  # Prevent abuse
            return jsonify({"error": "Message too long"}), 400
        
        if history and not isinstance(history, list):
            return jsonify({"error": "Invalid history format"}), 400

        # Process history
        processed_history = process_history(history)
        logger.info(f"Processing {len(history)} history messages")
        logger.info(f"Processed {len(processed_history)} valid messages")

        # Prepare product list with pricing
        product_text = "\n".join([
            f"- {p['name']}: Rich in {p['benefits']} - ₹{p.get('price', 'N/A')}" for p in PRODUCTS
        ])

        # Optimized System Prompt
        SYSTEM_PROMPT = f"""You are an AI Nutritionist. Help users with symptoms like fatigue, hair loss by suggesting food sources and nutrients.

RULES:
- Give both conventional foods AND biofortified options when relevant
- Ask about dietary preferences (veg/non-veg)  
- Provide specific prices from product list when asked
- Keep responses short (2-3 sentences)
- Educate about biofortification naturally

SUGGESTIONS MUST BE:
- Specific to user's symptom/question
- Actionable next steps
- Mix of food advice, product info, and health tips

Products: {product_text}

Always respond in JSON:
{{
  "reply": "Short helpful response",
  "suggestions": ["Specific follow-up 1", "Specific follow-up 2", "Specific follow-up 3"]
}}
"""

        # Build API message chain
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(processed_history)
        messages.append({"role": "user", "content": user_msg})

        # GPT Call with timeout
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=300,
            timeout=30
        )

        ai_content = response.choices[0].message.content.strip()
        logger.info(f"AI Response: {ai_content}")

        # Improved JSON Parsing
        try:
            # Try to extract JSON if wrapped in markdown
            if '```json' in ai_content:
                json_start = ai_content.find('{')
                json_end = ai_content.rfind('}') + 1
                ai_content = ai_content[json_start:json_end]
            
            reply_data = json.loads(ai_content)
            
            # Validate required fields
            if not isinstance(reply_data.get("reply"), str):
                raise ValueError("Invalid reply format")
            if not isinstance(reply_data.get("suggestions"), list):
                reply_data["suggestions"] = []
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON Parse Error: {e}")
            # Better fallback with contextual suggestions
            reply_data = {
                "reply": ai_content.replace('```json', '').replace('```', '').strip(),
                "suggestions": [
                    "What's your current diet like?", 
                    "Any other symptoms?", 
                    "Tell me about your food preferences"
                ]
            }

        return jsonify(reply_data)

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
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)