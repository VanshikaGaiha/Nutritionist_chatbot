import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timedelta
import hashlib

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
    r"/analyze": {"origins": [
        "http://localhost:3000", 
        "https://nutritionist-chatbot-frontend.onrender.com"
    ]},
    r"/health": {"origins": "*"},
    r"/session/*": {"origins": [
        "http://localhost:3000", 
        "https://nutritionist-chatbot-frontend.onrender.com"
    ]}
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

# In-memory session storage (use Redis/Database for production)
SESSIONS = {}
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30))  # Configurable timeout

def get_base_system_prompt():
    """Base system prompt that stays consistent"""
    product_text = "\n".join([
        f"- {p['name']}: Rich in {p['benefits']} - ₹{p.get('price', 'N/A')}" for p in PRODUCTS
    ])
    
    return f"""
You are an AI Nutritionist with a specific mission: subtly help users connect their symptoms with potential micronutrient deficiencies, then naturally introduce biofortification as an effortless, science-backed solution—without being promotional or salesy.

🎯 STRATEGIC OBJECTIVE:
Guide the conversation to help users realize:
1. Their symptoms may often relate to micronutrient deficiencies.
2. Even regular, healthy foods may lack nutrients due to soil depletion.
3. Biofortified foods provide these missing nutrients naturally, without changing their diet.
4. This solution feels natural and approachable, not like supplementation.

🧠 PSYCHOLOGICAL APPROACH:
- Always connect symptoms to specific nutrient gaps (e.g., iron, zinc, B12).
- Mention that "even healthy diets" may lack nutrients because of soil depletion.
- Validate their diet positively, but gently introduce the idea of food quality.
- Present biofortification as an interesting, science-backed discovery, not a product.

📝 RESPONSE FORMAT (JSON):
{{
  "reply": "Symptom → nutrient connection + subtle insight about soil/farming or nutrient quality, in 2-3 friendly sentences.",
  "suggestions": ["Short, specific follow-up question about their meals", "Short question about nutrient concerns or symptoms", "Question guiding them toward curiosity about food quality"]
}}

🔍 CONVERSATION FLOW STRATEGY:
**PHASE 1: Symptom Analysis**
- Connect symptoms to likely nutrient gaps immediately.
- Example: "Fatigue is often linked to low iron or B12 levels."

**PHASE 2: Diet Validation + Problem Seeding**
- Praise their diet but plant the idea of soil depletion or nutrient loss.
- Example: "Dal is fantastic for iron! Interestingly, due to soil changes, iron levels in lentils have dropped 25% since the 1960s."

**PHASE 3: Solution Discovery**
- Introduce biofortification as a natural solution discovered by scientists.
- Example: "Some farmers now grow nutrient-rich varieties that naturally contain 2-3x more iron—same taste and cooking, just better nutrition."

🎭 TONE GUIDELINES:
- Friendly, like a well-informed friend sharing interesting facts.
- Never sound salesy or pushy.
- Use natural curiosity phrases like "did you know," "interesting thing is," or "many people don't realize."

🔥 PSYCHOLOGICAL TRIGGERS:
- "Your symptoms make perfect sense because..."
- "Even with a good diet like yours, most people are still missing key nutrients because..."
- "The good news is you don't need to change what you eat—just focus on better-quality versions."
- "Scientists have discovered a natural way to solve this…"

📊 ENGAGEMENT TACTICS:
- Keep follow-up questions short and focused.
- Ask about their meals or specific food habits.
- Guide them to think about nutrient quality naturally.
- If they aren't interested after multiple declines, politely wrap up the conversation with a friendly note.

🚫 AVOID:
- Product promotion or price mentions.
- Direct calls to buy anything.
- Medical diagnosis or advice.
- Making users feel guilty about their diet.

Available product data (for reference only, do not mention unless asked): {product_text}
"""

def generate_session_id(user_identifier=None):
    """Generate a unique session ID"""
    timestamp = str(datetime.now().timestamp())
    user_id = user_identifier or request.remote_addr
    return hashlib.md5(f"{user_id}_{timestamp}".encode()).hexdigest()

def cleanup_expired_sessions():
    """Remove expired sessions"""
    current_time = datetime.now()
    expired_sessions = [
        session_id for session_id, session_data in SESSIONS.items()
        if current_time - session_data['last_activity'] > timedelta(minutes=SESSION_TIMEOUT)
    ]
    for session_id in expired_sessions:
        del SESSIONS[session_id]
    
    if expired_sessions:
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

def get_or_create_session(session_id=None):
    """Get existing session or create new one"""
    cleanup_expired_sessions()
    
    if session_id and session_id in SESSIONS:
        # Update last activity
        SESSIONS[session_id]['last_activity'] = datetime.now()
        return session_id, SESSIONS[session_id]
    
    # Create new session
    new_session_id = generate_session_id()
    SESSIONS[new_session_id] = {
        'messages': [{"role": "system", "content": get_base_system_prompt()}],
        'created_at': datetime.now(),
        'last_activity': datetime.now(),
        'message_count': 0
    }
    
    logger.info(f"Created new session: {new_session_id}")
    return new_session_id, SESSIONS[new_session_id]

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
        session_id = data.get("session_id")
        use_session = data.get("use_session", True)

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
            temperature=0.8,  # Higher creativity for more engaging responses
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

@app.route("/session/new", methods=["POST"])
def create_session():
    """Create a new session explicitly"""
    try:
        session_id, session_data = get_or_create_session()
        return jsonify({
            "session_id": session_id,
            "created_at": session_data['created_at'].isoformat(),
            "message_count": session_data['message_count']
        })
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({"error": "Failed to create session"}), 500

@app.route("/session/<session_id>", methods=["GET"])
def get_session(session_id):
    """Get session information"""
    try:
        cleanup_expired_sessions()
        
        if session_id not in SESSIONS:
            return jsonify({"error": "Session not found"}), 404
            
        session_data = SESSIONS[session_id]
        return jsonify({
            "session_id": session_id,
            "created_at": session_data['created_at'].isoformat(),
            "last_activity": session_data['last_activity'].isoformat(),
            "message_count": session_data['message_count'],
            "active": True
        })
    except Exception as e:
        logger.error(f"Error retrieving session: {e}")
        return jsonify({"error": "Failed to retrieve session"}), 500

@app.route("/session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Delete a session"""
    try:
        if session_id in SESSIONS:
            del SESSIONS[session_id]
            return jsonify({"message": "Session deleted successfully"})
        else:
            return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({"error": "Failed to delete session"}), 500

@app.route("/health", methods=["GET"])
def health():
    cleanup_expired_sessions()
    return jsonify({
        "status": "healthy",
        "products_loaded": len(PRODUCTS),
        "max_history_messages": 10,
        "max_tokens_estimate": 2000,
        "active_sessions": len(SESSIONS),
        "session_timeout_minutes": SESSION_TIMEOUT
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
