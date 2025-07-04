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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load product data with error handling
try:
    with open("products.json", "r") as f:
        PRODUCTS = json.load(f)
except FileNotFoundError:
    print("ERROR: products.json not found!")
    PRODUCTS = []

# Your custom system prompt
SYSTEM_PROMPT = """You are a knowledgeable nutrition assistant with expertise in micronutrients and emerging agricultural solutions.

CORE KNOWLEDGE:
- Understand that many symptoms relate to micronutrient deficiencies
- Know that nutrient absorption from food varies greatly (iron from plants: 2-20%, from meat: 15-35%)
- Aware that soil depletion affects crop nutrient content
- Familiar with biofortification as a natural solution where crops are bred/grown to have higher nutrient levels
- Understand that biofortification allows people to get more nutrients without changing their diet

CONVERSATION STYLE:
- Be genuinely helpful and educational
- Connect symptoms to potential nutrient gaps naturally
- Share interesting facts about nutrition absorption when relevant
- Introduce biofortification organically when discussing nutrient challenges
- Use phrases like "recent research shows..." or "nutritionists are finding..."
- Never sound scripted or salesy

GOAL: Help users understand their symptoms while naturally educating them about biofortification as an innovative solution to common nutritional challenges.
"""

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        user_msg = data.get("message", "")
        history = data.get("history", [])

        print(f"Received message: {user_msg}")
        print(f"API Key present: {bool(client.api_key)}")

        product_text = "\n".join([
            f"- {p['name']} ({', '.join(p['variants'])}, Price: ₹{p['price']}): {p['benefits']}"
            for p in PRODUCTS
        ])

        # Build chat history
        messages = [
            {
                "role": "system",
                "content": f"""{SYSTEM_PROMPT}

Here are Better Nutrition's products you can mention if relevant:
{product_text}

Reply in 2-3 lines with helpful advice. Always provide 2-3 interactive follow-up suggestions.

Try to respond in this JSON format, but if you can't, just give a natural response:
{{
  "reply": "Your helpful response here.",
  "suggestions": ["Interactive question 1", "Follow-up topic 2", "Related question 3"]
}}
"""
            }
        ]

        # Add past conversation
        for msg in history:
            messages.append({
                "role": "user" if msg["sender"] == "user" else "assistant",
                "content": msg["text"]
            })

        messages.append({"role": "user", "content": user_msg})

        # API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=400
        )

        ai_content = response.choices[0].message.content.strip()
        print(f"AI Response: {ai_content}")

        # Parse AI JSON reply safely
        try:
            reply_data = json.loads(ai_content)
            if "reply" not in reply_data:
                reply_data["reply"] = ai_content
            if "suggestions" not in reply_data:
                reply_data["suggestions"] = []
        except json.JSONDecodeError:
            print(f"JSON Parse Error, using AI fallback: {ai_content}")
            # AI fallback attempt
            try:
                fallback_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Convert the following nutritionist response into proper JSON format. "
                                "Extract the main reply and create 3 relevant follow-up suggestions. "
                                "Return ONLY valid JSON in this format:\n"
                                "{\n"
                                "  \"reply\": \"main response here\",\n"
                                "  \"suggestions\": [\"suggestion 1\", \"suggestion 2\", \"suggestion 3\"]\n"
                                "}"
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Original user question: {user_msg}\n\nNutritionist response: {ai_content}"
                        }
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                fallback_content = fallback_response.choices[0].message.content.strip()
                reply_data = json.loads(fallback_content)
            except Exception as fallback_error:
                print(f"Fallback AI call failed: {fallback_error}")
                reply_data = {
                    "reply": ai_content,
                    "suggestions": []
                }

        return jsonify(reply_data)

    except Exception as e:
        print(f"ERROR in analyze: {str(e)}")
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
