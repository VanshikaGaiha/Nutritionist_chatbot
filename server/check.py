import google.generativeai as genai

# Replace this with your actual API key
API_KEY = "AIzaSyBzx8oXyNVuq7I7RcO-1LOEXD1cRjnu9n0"

# Configure the API key
genai.configure(api_key=API_KEY)

# List all available models and their supported methods
try:
    models = genai.list_models()

    print("\n✅ Available Models and Supported Methods:\n")
    for model in models:
        print(f"📌 Model ID: {model.name}")
        print(f"   Supported Methods: {model.supported_generation_methods}\n")

except Exception as e:
    print("❌ Error fetching models:", e)