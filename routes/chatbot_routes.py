import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.setup import get_db
from db.models import SearchHistory, ImageModel
from collections import Counter
import requests

router = APIRouter()

# ✅ קריאה למפתח ה־Gemini מהסביבה
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ בדיקה שהמפתח נטען
if not GEMINI_API_KEY:
    print("❌ [chatbot_routes] ENV variable GEMINI_API_KEY is MISSING")
    raise RuntimeError("❌ Gemini API key not loaded. Make sure it's set in environment or .env.")
else:
    print(f"✅ [chatbot_routes] GEMINI_API_KEY loaded: {GEMINI_API_KEY[:6]}...")

# שלב 1: שליפת הקשר מהמסד
def build_context_from_db(db: Session) -> str:
    count_searches = db.query(func.count(SearchHistory.id)).scalar()
    count_images = db.query(ImageModel.image_path).distinct().count()

    last_search = db.query(SearchHistory).order_by(SearchHistory.timestamp.desc()).first()
    last_query = last_search.query if last_search else "None"

    captions = db.query(ImageModel.caption).all()
    most_common_caption = Counter([c[0] for c in captions if c[0]]).most_common(1)
    common_caption_text = most_common_caption[0][0] if most_common_caption else "None"

    return (
        f"You have {count_images} images in your database.\n"
        f"You have performed {count_searches} searches so far.\n"
        f"Your last search was: \"{last_query}\".\n"
        f"The most common caption is: \"{common_caption_text}\".\n"
    )

# שליחת השאלה עם הקשר אל Gemini
def ask_gemini_with_context(question: str, context: str) -> str:
    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [{
            "parts": [
                {"text": f"{context}\n\nUser asked: {question}"}
            ]
        }]
    }

    response = requests.post(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        json=payload,
        headers=headers
    )

    try:
        data = response.json()
        print("🔎 Gemini raw response:", data)
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"❌ Error from Gemini: {e}\n🔍 Full response: {response.text}"

@router.post("/ask", tags=["Chatbot"])
async def chatbot_answer(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    question = data.get("question", "").strip()

    # שמירה להיסטוריית חיפושים – רק אם יש טקסט תקני
    if question:
        new_search = SearchHistory(query=question)
        db.add(new_search)
        db.commit()

    # בונה הקשר מהמסד ומבצע שיחה
    context = build_context_from_db(db)
    answer = ask_gemini_with_context(question, context)
    return {"answer": answer}

