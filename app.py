import os
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Lazy import agent so Flask starts fast
_agent_chat = None

def get_agent():
    global _agent_chat
    if _agent_chat is None:
        from agent import chat
        _agent_chat = chat
    return _agent_chat


@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if not os.getenv("GROQ_API_KEY"):
        return jsonify({"error": "GROQ_API_KEY not set in .env file"}), 500

    try:
        chat_fn = get_agent()
        response = chat_fn(user_message, history)
        return jsonify({"response": response, "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "api_key_set": bool(os.getenv("ANTHROPIC_API_KEY"))})


if __name__ == "__main__":
    print("\n🚀 CryptoBot starting...")
    print("📌 Open: http://127.0.0.1:5000\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
