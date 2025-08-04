from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()

# משתנים גלובליים למעקב על סריקה פעילה
current_scan_status = {
    "is_running": False,
    "processed": 0,
    "total": 0,
    "current_image": "",
    "start_time": None,
    "errors": 0,
    "can_cancel": True
}


class ScanRequest(BaseModel):
    max_images: Optional[int] = 1000
    force: Optional[bool] = False


class ScanResponse(BaseModel):
    success: bool
    message: str
    processed_count: int
    total_new_images: int
    errors: int
    duration_seconds: float
    scan_needed: bool


def get_user_folder_path():
    config_paths = [
        "user_folder_config.json",
        "pages/config.json"
    ]

    for config_path in config_paths:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                folder_path = config.get('folder') or config.get('user_images_path')

                if folder_path and os.path.exists(folder_path):
                    logger.info(f"📁 נמצאה תיקייה: {folder_path}")
                    return folder_path

        except Exception as e:
            logger.warning(f"⚠️ לא ניתן לקרוא {config_path}: {e}")

    logger.warning("⚠️ לא נמצאה תיקיית משתמש מוגדרת")
    return None


def get_last_scan_time():
    """קריאת זמן הסריקה האחרונה"""
    scan_info_file = "last_scan_info.json"

    try:
        if os.path.exists(scan_info_file):
            with open(scan_info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_scan_str = data.get('last_scan_time')
                if last_scan_str:
                    return datetime.fromisoformat(last_scan_str)
    except Exception as e:
        logger.warning(f"⚠️ לא ניתן לקרוא זמן סריקה אחרון: {e}")

    # ברירת מחדל - לפני 25 שעות
    return datetime.now() - timedelta(hours=25)


def find_new_images_since_last_scan(folder_path, last_scan_time):
    """מציאת תמונות שלא קיימות במסד נתונים"""
    from db.setup import get_db
    from db.user_image_access import image_exists

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
    new_images = []

    try:
        logger.info(f"🔍 סורק תיקייה לתמונות לא מעובדות: {folder_path}")

        db = next(get_db())

        try:
            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('$')]

                for file in files:
                    try:
                        file_path = Path(root) / file

                        if file_path.suffix.lower() not in image_extensions:
                            continue

                        if file_path.stat().st_size == 0:
                            continue

                        normalized_path = str(file_path).replace("\\", "/")
                        if not image_exists(db, normalized_path):
                            new_images.append(normalized_path)

                    except Exception as e:
                        logger.warning(f"⚠️ שגיאה בבדיקת קובץ {file}: {e}")
                        continue

        finally:
            db.close()

        logger.info(f"📸 נמצאו {len(new_images)} תמונות לא מעובדות")
        return new_images

    except Exception as e:
        logger.error(f"❌ שגיאה בסריקת תיקייה: {e}")
        return []


@router.get("/daily_check")
async def daily_check():
    """בדיקה מהירה אם יש תמונות חדשות"""
    try:
        logger.info("🔍 מבצע בדיקה יומית...")

        folder_path = get_user_folder_path()
        if not folder_path:
            return {
                "has_new_images": False,
                "message": "לא הוגדרה תיקיית משתמש",
                "new_images_count": 0
            }

        last_scan = get_last_scan_time()
        new_images = find_new_images_since_last_scan(folder_path, last_scan)

        return {
            "has_new_images": len(new_images) > 0,
            "new_images_count": len(new_images),
            "last_scan": last_scan.isoformat(),
            "folder_path": folder_path,
            "message": f"נמצאו {len(new_images)} תמונות חדשות" if new_images else "אין תמונות חדשות"
        }

    except Exception as e:
        logger.error(f"❌ שגיאה בבדיקה יומית: {e}")
        raise HTTPException(status_code=500, detail=f"שגיאה בבדיקה יומית: {str(e)}")


@router.get("/scan_progress")
async def get_scan_progress():
    """קבלת מידע על התקדמות הסריקה הנוכחית"""
    return {
        "is_running": current_scan_status["is_running"],
        "processed": current_scan_status["processed"],
        "total": current_scan_status["total"],
        "current_image": current_scan_status["current_image"],
        "errors": current_scan_status["errors"],
        "percentage": round((current_scan_status["processed"] / current_scan_status["total"]) * 100, 1) if
        current_scan_status["total"] > 0 else 0,
        "can_cancel": current_scan_status["can_cancel"]
    }


@router.post("/start_async_scan")
async def start_async_scan(request: Optional[ScanRequest] = None, background_tasks: BackgroundTasks = None):
    """התחלת סריקה אסינכרונית שלא חוסמת את השרת"""

    if request is None:
        request = ScanRequest()

    # בדיקה אם כבר רצה סריקה
    if current_scan_status["is_running"]:
        return {
            "success": False,
            "message": "סריקה כבר פעילה",
            "scan_id": None
        }

    try:
        folder_path = get_user_folder_path()
        if not folder_path:
            return {
                "success": False,
                "message": "לא הוגדרה תיקיית משתמש",
                "scan_id": None
            }

        # מציאת תמונות חדשות
        last_scan = get_last_scan_time()
        new_images = find_new_images_since_last_scan(folder_path, last_scan)

        if not new_images and not request.force:
            return {
                "success": True,
                "message": "אין תמונות חדשות לעיבוד",
                "scan_id": None
            }

        # הגבלת מספר תמונות לעיבוד
        images_to_process = new_images[:request.max_images] if request.max_images else new_images

        # עדכון סטטוס התחלתי
        current_scan_status.update({
            "is_running": True,
            "processed": 0,
            "total": len(images_to_process),
            "current_image": "",
            "start_time": datetime.now(),
            "errors": 0,
            "can_cancel": True
        })

        # הפעלת הסריקה ברקע
        background_tasks.add_task(process_images_async, images_to_process)

        logger.info(f"🚀 סריקה אסינכרונית החלה: {len(images_to_process)} תמונות")

        return {
            "success": True,
            "message": f"סריקה החלה ברקע עם {len(images_to_process)} תמונות",
            "scan_id": "async_scan_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "total_images": len(images_to_process)
        }

    except Exception as e:
        logger.error(f"❌ שגיאה בהתחלת סריקה אסינכרונית: {e}")
        current_scan_status["is_running"] = False
        return {
            "success": False,
            "message": f"שגיאה בהתחלת סריקה: {str(e)}",
            "scan_id": None
        }


@router.post("/cancel_scan")
async def cancel_scan():
    """ביטול הסריקה הפעילה"""
    if not current_scan_status["is_running"]:
        return {
            "success": False,
            "message": "אין סריקה פעילה לביטול"
        }

    current_scan_status["can_cancel"] = False
    current_scan_status["is_running"] = False

    return {
        "success": True,
        "message": "סריקה מבוטלת",
        "processed": current_scan_status["processed"]
    }


async def process_images_async(image_paths):
    """עיבוד תמונות אסינכרוני ברקע"""
    try:
        # ייבוא הספריות הנדרשות
        from services.blip_captioner import Blip2Captioner
        from services.text_encoder import encode_text
        from db.setup import get_db
        from db.user_image_access import add_user_image, image_exists

        logger.info(f"🚀 מתחיל עיבוד אסינכרוני של {len(image_paths)} תמונות...")

        captioner = Blip2Captioner.get_instance()
        processed_count = 0
        errors = 0

        db = next(get_db())

        try:
            for i, image_path in enumerate(image_paths, 1):
                # בדיקה אם הסריקה בוטלה
                if not current_scan_status["can_cancel"] or not current_scan_status["is_running"]:
                    logger.info("⏹️ סריקה בוטלה על ידי המשתמש")
                    break

                try:
                    # עדכון סטטוס נוכחי
                    current_scan_status["current_image"] = Path(image_path).name
                    current_scan_status["processed"] = processed_count

                    logger.info(f"🔄 מעבד תמונה {i}/{len(image_paths)}: {Path(image_path).name}")

                    # בדיקה אם התמונה כבר קיימת
                    normalized_path = image_path.replace("\\", "/")
                    if image_exists(db, normalized_path):
                        logger.info(f"⏭️ תמונה כבר קיימת במסד נתונים")
                        continue

                    # יצירת תיאור
                    caption = captioner.generate_caption(image_path)
                    logger.info(f"📝 תיאור נוצר: {caption[:50]}...")

                    # יצירת embedding
                    embedding = encode_text(caption)

                    # שמירה במסד נתונים
                    add_user_image(db, caption, embedding, normalized_path)
                    processed_count += 1

                    # שמירה תקופתית כל 5 תמונות
                    if processed_count % 5 == 0:
                        db.commit()
                        logger.info(f"💾 נשמרו {processed_count} תמונות")

                        # מתן זמן לשרת לטפל בבקשות אחרות
                        await asyncio.sleep(0.1)

                    # מתן זמן לשרת אחרי כל תמונה
                    await asyncio.sleep(0.05)

                except Exception as e:
                    errors += 1
                    current_scan_status["errors"] = errors
                    logger.error(f"❌ שגיאה בעיבוד {image_path}: {e}")
                    continue

            # שמירה סופית
            db.commit()
            logger.info(f"✅ עיבוד אסינכרוני הושלם: {processed_count} הצליחו, {errors} שגיאות")

            # שמירת זמן הסריקה
            save_last_scan_time()

        finally:
            db.close()
            # איפוס סטטוס הסריקה
            current_scan_status.update({
                "is_running": False,
                "processed": processed_count,
                "current_image": "סריקה הושלמה",
                "can_cancel": True
            })

    except Exception as e:
        logger.error(f"❌ שגיאה כללית בעיבוד אסינכרוני: {e}")
        current_scan_status["is_running"] = False


@router.post("/perform_daily_update")
async def perform_daily_update(request: Optional[ScanRequest] = None, background_tasks: BackgroundTasks = None):
    """ביצוע עדכון יומי - מפנה לסריקה אסינכרונית"""

    if request is None:
        request = ScanRequest()

    # אם כבר רצה סריקה, החזר מידע על ההתקדמות
    if current_scan_status["is_running"]:
        return {
            "success": True,
            "message": f"סריקה כבר פעילה: {current_scan_status['processed']}/{current_scan_status['total']}",
            "processed_count": current_scan_status["processed"],
            "total_new_images": current_scan_status["total"],
            "errors": current_scan_status["errors"],
            "duration_seconds": (datetime.now() - current_scan_status["start_time"]).total_seconds() if
            current_scan_status["start_time"] else 0,
            "scan_needed": True
        }

    # הפעלת סריקה אסינכרונית חדשה
    async_result = await start_async_scan(request, background_tasks)

    if async_result["success"]:
        return {
            "success": True,
            "message": "סריקה החלה ברקע - השרת זמין לחיפושים",
            "processed_count": 0,
            "total_new_images": async_result.get("total_images", 0),
            "errors": 0,
            "duration_seconds": 0,
            "scan_needed": True
        }
    else:
        return {
            "success": False,
            "message": async_result["message"],
            "processed_count": 0,
            "total_new_images": 0,
            "errors": 1,
            "duration_seconds": 0,
            "scan_needed": False
        }


def save_last_scan_time():
    """שמירת זמן הסריקה הנוכחי"""
    scan_info_file = "last_scan_info.json"

    try:
        data = {
            'last_scan_time': datetime.now().isoformat(),
            'scan_status': 'completed',
            'version': '1.0'
        }

        with open(scan_info_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info("💾 זמן סריקה נשמר")

    except Exception as e:
        logger.error(f"❌ שגיאה בשמירת זמן סריקה: {e}")


@router.get("/scan_status")
async def get_scan_status():
    """קבלת סטטוס הסריקה הנוכחי"""
    try:
        last_scan = get_last_scan_time()
        folder_path = get_user_folder_path()

        new_images_count = 0
        if folder_path:
            new_images = find_new_images_since_last_scan(folder_path, last_scan)
            new_images_count = len(new_images)

        hours_since_scan = (datetime.now() - last_scan).total_seconds() / 3600

        return {
            "last_scan_time": last_scan.isoformat(),
            "hours_since_scan": round(hours_since_scan, 1),
            "folder_configured": folder_path is not None,
            "folder_path": folder_path,
            "new_images_count": new_images_count,
            "scan_needed": hours_since_scan >= 24 or new_images_count > 0,
            "current_scan": current_scan_status
        }

    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת סטטוס סריקה: {e}")
        raise HTTPException(status_code=500, detail=f"שגיאה בקבלת סטטוס: {str(e)}")


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "daily_scanner",
        "scan_running": current_scan_status["is_running"]
    }