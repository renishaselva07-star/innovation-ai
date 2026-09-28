import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import SYSTEM_PROMPT, OFF_TOPIC_REPLY

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024  # Keep requests small.

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.1-flash-lite"

client = genai.Client(api_key=API_KEY) if API_KEY else None


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"reply": "Please enter a question."}), 400

    if len(message) > 8000:
        return jsonify({"reply": "Please keep your question under 8,000 characters."}), 400

    if client is None:
        return jsonify({
            "reply": "The chatbot is not configured yet. Add your Gemini API key to the .env file."
        }), 503

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=message.strip(),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=1200,
            ),
        )
        reply = (response.text or "").strip() or OFF_TOPIC_REPLY
        return jsonify({"reply": reply})
    except Exception:
        app.logger.exception("Gemini API request failed")
        return jsonify({
            "reply": "I couldn't get a response right now. Please try again in a moment."
        }), 502


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
