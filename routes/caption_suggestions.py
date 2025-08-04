from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.setup import get_db
import logging

router = APIRouter()

# הגדרת logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/suggest_captions")
def suggest_captions(prefix: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    try:
        logger.info(f"🔍 מחפש הצעות עבור: '{prefix}'")

        # שאילתה משופרת עם ILIKE וטיפול בחיפוש מדויק יותר
        query_coco = text("""
                          SELECT caption
                          FROM images
                          WHERE caption ILIKE :prefix
                          GROUP BY caption
                          ORDER BY LENGTH(caption), caption
                          LIMIT 8
                          """)

        query_user = text("""
                          SELECT caption
                          FROM user_images
                          WHERE caption ILIKE :prefix
                          GROUP BY caption
                          ORDER BY LENGTH(caption), caption
                          LIMIT 8
                          """)

        results_coco = db.execute(query_coco, {"prefix": f"%{prefix}%"}).fetchall()
        results_user = db.execute(query_user, {"prefix": f"%{prefix}%"}).fetchall()

        logger.info(f"📊 נמצאו {len(results_coco)} תוצאות COCO ו-{len(results_user)} תוצאות משתמש")

        captions = set()

        for row in results_coco:
            if row[0] and len(row[0].strip()) > 0:
                captions.add(row[0].strip())

        # הוספת תוצאות משתמש
        for row in results_user:
            if row[0] and len(row[0].strip()) > 0:
                captions.add(row[0].strip())

        # המרה לרשימה וסידור לפי אורך
        suggestions = sorted(list(captions), key=lambda x: (len(x), x.lower()))[:10]

        logger.info(f"✅ מחזיר {len(suggestions)} הצעות: {suggestions[:3]}...")

        return suggestions

    except Exception as e:
        logger.error(f"❌ שגיאה בחיפוש הצעות: {str(e)}")
        # במקרה של שגיאה, נחזיר רשימה ריקה במקום להחזיר שגיאה
        return []


@router.get("/test_suggestions")
def test_suggestions(db: Session = Depends(get_db)):
    """endpoint לבדיקת קיום נתונים בטבלאות"""
    try:
        # בדיקת מספר רשומות בטבלאות
        coco_count = db.execute(text("SELECT COUNT(*) FROM images")).fetchone()[0]
        user_count = db.execute(text("SELECT COUNT(*) FROM user_images")).fetchone()[0]

        # דוגמאות תיאורים
        sample_coco = db.execute(text("SELECT caption FROM images WHERE caption IS NOT NULL LIMIT 5")).fetchall()
        sample_user = db.execute(text("SELECT caption FROM user_images WHERE caption IS NOT NULL LIMIT 5")).fetchall()

        return {
            "coco_images_count": coco_count,
            "user_images_count": user_count,
            "sample_coco_captions": [row[0] for row in sample_coco],
            "sample_user_captions": [row[0] for row in sample_user]
        }

    except Exception as e:
        logger.error(f"❌ שגיאה בבדיקת טבלאות: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))