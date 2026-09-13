import os

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore

from google import genai


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# GEMINI AI CONFIGURATION
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# You can change this model in .env if required.
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
).strip()


client = None

if GEMINI_API_KEY:

    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        print("Gemini AI initialized successfully.")

    except Exception as e:

        print("Gemini initialization error:")
        print(e)

else:

    print("WARNING: GEMINI_API_KEY not found in .env")


# =========================================================
# FIREBASE CONFIGURATION
# =========================================================

db = None

FIREBASE_KEY = os.getenv(
    "FIREBASE_KEY",
    "firebase_key.json"
).strip()


if os.path.exists(FIREBASE_KEY):

    try:

        if not firebase_admin._apps:

            credential = credentials.Certificate(
                FIREBASE_KEY
            )

            firebase_admin.initialize_app(
                credential
            )

        db = firestore.client()

        print("Firebase initialized successfully.")

    except Exception as e:

        print("Firebase initialization error:")
        print(e)

else:

    print(
        "WARNING: firebase_key.json not found. "
        "Firebase chat saving is disabled."
    )


# =========================================================
# FITNESS AI SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are FitnessAI, a helpful fitness education chatbot.

Your main topics are:

- General fitness
- Beginner workouts
- Exercise basics
- Warm-up
- Cool-down
- Cardio
- Strength training basics
- Flexibility
- Mobility
- Hydration
- General healthy nutrition
- Sleep
- Recovery
- Healthy lifestyle habits
- Fitness motivation

IMPORTANT RESPONSE RULES:

1. Answer the user's EXACT question.

2. Do NOT give the same generic answer to every question.

3. If the user asks about sleep, answer about sleep.

4. If the user asks about hydration, answer about hydration.

5. If the user asks about workouts, answer about workouts.

6. If the user asks about warm-up, explain warm-up.

7. If the user asks about recovery, explain recovery.

8. Keep answers simple and easy to understand.

9. Use bullet points when useful.

10. Encourage safe and age-appropriate physical activity.

11. Do not encourage extreme dieting, starvation,
    excessive exercise, rapid weight loss, or unhealthy
    body-image goals.

12. Do not diagnose medical conditions.

13. Do not prescribe medicines or supplements.

14. If the user mentions an injury, severe pain, medical
    condition, or concerning symptoms, recommend talking
    with a parent/guardian and a qualified healthcare
    professional.

15. If the question is unrelated to fitness, politely explain
    that you are a fitness-focused chatbot.

16. Give practical and safe educational information.
"""


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def fallback_reply(message):

    msg = message.lower().strip()

    if any(word in msg for word in ["hello", "hi", "hey"]):

        return (
            "Hello! 👋 I'm FitnessAI.\n\n"
            "You can ask me about workouts, exercise, "
            "hydration, sleep, recovery, warm-ups, "
            "or healthy fitness habits."
        )

    if "sleep" in msg:

        return (
            "Sleep is an important part of fitness and recovery.\n\n"
            "Good sleep can help your body recover after physical "
            "activity and can support your energy and concentration "
            "during the day.\n\n"
            "Try to keep a consistent sleep schedule and give "
            "yourself enough time to rest."
        )

    if "water" in msg or "hydration" in msg:

        return (
            "Hydration is important during physical activity.\n\n"
            "Drink water regularly throughout the day and pay "
            "attention to thirst, especially when exercising or "
            "when the weather is hot."
        )

    if "warm" in msg:

        return (
            "A warm-up prepares your body for physical activity.\n\n"
            "You can start with 5–10 minutes of easy movement, "
            "such as walking, light jogging, and gentle mobility "
            "movements.\n\n"
            "Increase the intensity gradually."
        )

    if "workout" in msg or "exercise" in msg:

        return (
            "For a beginner, start with simple activities such as "
            "walking, bodyweight movements, mobility exercises, "
            "and other comfortable activities.\n\n"
            "Start gradually, focus on good technique, and allow "
            "your body enough time to rest."
        )

    if "recovery" in msg or "rest" in msg:

        return (
            "Recovery is an important part of fitness.\n\n"
            "Give your body enough rest between challenging "
            "activities. Sleep, hydration, balanced meals, and "
            "easy movement can all support recovery."
        )

    return (
        "I'm FitnessAI, a fitness-focused chatbot.\n\n"
        "You can ask me about workouts, exercise, warm-ups, "
        "hydration, sleep, recovery, or healthy fitness habits."
    )


# =========================================================
# GENERATE GEMINI RESPONSE
# =========================================================

def generate_ai_reply(message):

    # -----------------------------------------------------
    # Check API key
    # -----------------------------------------------------

    if not client:

        print("Gemini client is not available.")

        return fallback_reply(message)


    # -----------------------------------------------------
    # Create prompt
    # -----------------------------------------------------

    prompt = f"""
{SYSTEM_PROMPT}

USER QUESTION:

{message}

Now answer the user's question directly.

Make sure the answer is specifically related to what
the user asked and do not repeat a generic answer.
"""


    # -----------------------------------------------------
    # Call Gemini
    # -----------------------------------------------------

    try:

        print()
        print("User question:")
        print(message)

        print()
        print("Sending request to Gemini...")
        print("Model:", GEMINI_MODEL)


        response = client.models.generate_content(

            model=GEMINI_MODEL,

            contents=prompt

        )


        # -------------------------------------------------
        # Check response
        # -------------------------------------------------

        if response and response.text:

            answer = response.text.strip()

            print()
            print("Gemini response received successfully.")

            return answer


        print()
        print("Gemini returned an empty response.")

        return fallback_reply(message)


    except Exception as e:

        print()
        print("================ GEMINI ERROR ================")
        print(repr(e))
        print("==============================================")
        print()

        return (
            "Sorry, Gemini AI could not process your question "
            "right now.\n\n"
            "Please check the terminal for the Gemini error."
        )


# =========================================================
# SAVE CHAT TO FIREBASE
# =========================================================

def save_chat(user_message, bot_message):

    if db is None:

        print(
            "Firebase is not connected. "
            "Chat was not saved."
        )

        return


    try:

        db.collection(
            "fitness_chats"
        ).add({

            "user_message": user_message,

            "bot_message": bot_message,

            "created_at":
                firestore.SERVER_TIMESTAMP

        })

        print("Chat saved to Firebase.")


    except Exception as e:

        print("Firebase chat save error:")
        print(e)


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# CHAT API
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        # ---------------------------------------------
        # Get JSON data
        # ---------------------------------------------

        data = request.get_json()


        if not data:

            return jsonify({

                "reply":
                    "Please enter a message."

            }), 400


        # ---------------------------------------------
        # Get user message
        # ---------------------------------------------

        message = data.get(
            "message",
            ""
        ).strip()


        if not message:

            return jsonify({

                "reply":
                    "Please enter a question."

            }), 400


        # ---------------------------------------------
        # Generate AI answer
        # ---------------------------------------------

        reply = generate_ai_reply(
            message
        )


        # ---------------------------------------------
        # Save conversation
        # ---------------------------------------------

        save_chat(
            message,
            reply
        )


        # ---------------------------------------------
        # Return answer
        # ---------------------------------------------

        return jsonify({

            "reply": reply

        })


    except Exception as e:

        print()
        print("================ SERVER ERROR ================")
        print(repr(e))
        print("==============================================")
        print()


        return jsonify({

            "reply":
                "Something went wrong. "
                "Please try again."

        }), 500


# =========================================================
# START FLASK SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print()
    print("==============================================")
    print("        FITNESS AI CHATBOT")
    print("==============================================")
    print()
    print("Server starting...")
    print()
    print(
        f"Open in browser: "
        f"http://127.0.0.1:{port}"
    )
    print()

    app.run(

        host="0.0.0.0",

        port=port,

        debug=True

    )