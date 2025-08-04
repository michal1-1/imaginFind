from fastapi import APIRouter, Request, HTTPException
import json
import os
from pathlib import Path
import logging

# הגדרת לוגר
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/set_user_folder")
async def set_user_folder(request: Request):
    """
    מגדיר את נתיב התיקייה האישית של המשתמש
    """
    try:
        # קבלת הנתונים מהבקשה
        data = await request.json()
        folder_path = data.get("path", "")

        logger.info(f"📁 מקבל בקשה לשמירת תיקייה: {folder_path}")

        # ולידציה של הנתיב
        if not folder_path or folder_path.strip() == "":
            logger.warning("❌ נתיב ריק התקבל")
            return {
                "success": False,
                "error": "נתיב התיקייה לא יכול להיות ריק",
                "message": "נתיב התיקייה לא יכול להיות ריק"
            }

        # בדיקה שהתיקייה קיימת
        if not os.path.exists(folder_path):
            logger.warning(f"❌ התיקייה לא קיימת: {folder_path}")
            return {
                "success": False,
                "error": f"התיקייה לא קיימת: {folder_path}",
                "message": f"התיקייה לא קיימת: {folder_path}"
            }

        # בדיקה שזו באמת תיקייה
        if not os.path.isdir(folder_path):
            logger.warning(f"❌ הנתיב אינו תיקייה: {folder_path}")
            return {
                "success": False,
                "error": f"הנתיב אינו תיקייה תקינה: {folder_path}",
                "message": f"הנתיב אינו תיקייה תקינה: {folder_path}"
            }

        # בדיקת הרשאות כתיבה לתיקייה הנוכחית
        config_path = "user_folder_config.json"
        try:
            # ניסיון שמירה
            config_data = {
                "folder": folder_path,
                "last_updated": str(Path().absolute()),
                "status": "active"
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 תיקייה נשמרה בהצלחה: {folder_path}")

            # בדיקה כמה תמונות יש בתיקייה (אופציונלי)
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
            image_count = 0

            try:
                for file_path in Path(folder_path).iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                        image_count += 1

                logger.info(f"📸 נמצאו {image_count} תמונות בתיקייה")

            except Exception as count_error:
                logger.warning(f"⚠️ לא ניתן לספור תמונות: {count_error}")
                image_count = -1

            # החזרת תגובה מוצלחת
            return {
                "success": True,
                "message": "נתיב התיקייה נשמר בהצלחה",
                "folder_path": folder_path,
                "image_count": image_count,
                "config_saved": True
            }

        except PermissionError:
            logger.error("❌ אין הרשאה לכתיבה")
            return {
                "success": False,
                "error": "אין הרשאה לכתיבת קובץ ההגדרות",
                "message": "אין הרשאה לכתיבת קובץ ההגדרות"
            }
        except Exception as save_error:
            logger.error(f"❌ שגיאה בשמירה: {save_error}")
            return {
                "success": False,
                "error": f"שגיאה בשמירת ההגדרות: {str(save_error)}",
                "message": f"שגיאה בשמירת ההגדרות: {str(save_error)}"
            }

    except json.JSONDecodeError:
        logger.error("❌ שגיאה בפענוח JSON")
        return {
            "success": False,
            "error": "פורמט הבקשה לא תקין",
            "message": "פורמט הבקשה לא תקין"
        }
    except Exception as e:
        logger.error(f"❌ שגיאה כללית: {e}")
        return {
            "success": False,
            "error": f"שגיאה כללית: {str(e)}",
            "message": f"שגיאה כללית: {str(e)}"
        }


@router.get("/get_user_folder")
async def get_user_folder():
    """
    מחזיר את נתיב התיקייה האישית הנוכחית
    """
    try:
        config_path = "user_folder_config.json"

        if not os.path.exists(config_path):
            return {
                "success": False,
                "message": "לא הוגדרה תיקייה עדיין",
                "folder_path": None
            }

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        folder_path = config_data.get("folder", "")

        if not folder_path:
            return {
                "success": False,
                "message": "לא נמצא נתיב בקובץ ההגדרות",
                "folder_path": None
            }

        # בדיקה שהתיקייה עדיין קיימת
        if not os.path.exists(folder_path):
            return {
                "success": False,
                "message": "התיקייה השמורה לא קיימת יותר",
                "folder_path": folder_path,
                "exists": False
            }

        return {
            "success": True,
            "message": "תיקייה נמצאה",
            "folder_path": folder_path,
            "exists": True
        }

    except Exception as e:
        logger.error(f"❌ שגיאה בקריאת התיקייה: {e}")
        return {
            "success": False,
            "error": f"שגיאה בקריאת ההגדרות: {str(e)}",
            "message": f"שגיאה בקריאת ההגדרות: {str(e)}"
        }