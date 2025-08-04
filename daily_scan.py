import os
import sys
import json
import logging
import traceback
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))
log_file = script_dir / "daily_scan.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
class SmartProcessingStrategy:
    def __init__(self):
        self.max_time_budget = 2 * 3600
        self.target_completion_days = 3
        self.min_batch_size = 10
        self.max_batch_size = 300
    def calculate_optimal_batch_size(self, total_images, avg_processing_time=None):
        daily_target = total_images / self.target_completion_days
        time_based_batch = min(daily_target, self.max_batch_size)
        if avg_processing_time:
            time_budget_batch = self.max_time_budget / avg_processing_time
            time_based_batch = min(time_based_batch, time_budget_batch)
        system_factor = self.get_system_performance_factor()
        adjusted_batch = time_based_batch * system_factor
        final_batch = max(self.min_batch_size,
                          min(adjusted_batch, self.max_batch_size, total_images))
        return int(final_batch)
    def get_system_performance_factor(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_factor = 1.2 if cpu_percent < 30 else (0.8 if cpu_percent > 70 else 1.0)
            memory = psutil.virtual_memory()
            memory_factor = 1.2 if memory.percent < 60 else (0.7 if memory.percent > 85 else 1.0)
            current_hour = datetime.now().hour
            time_factor = 1.3 if 0 <= current_hour <= 6 else 1.0
            performance_factor = (cpu_factor + memory_factor + time_factor) / 3
            logger.info(f"🔧 מקדם ביצועים: {performance_factor:.2f} "
                        f"(CPU: {cpu_percent}%, RAM: {memory.percent}%)")
            return performance_factor
        except Exception as e:
            logger.warning(f"{e}")
            return 1.0

    def should_continue_processing(self, start_time, processed_count, total_count):
        elapsed_time = time.time() - start_time
        if elapsed_time > self.max_time_budget:
            logger.info(f"⏰ הגיע למגבלת זמן: {elapsed_time / 3600:.1f} שעות")
            return False
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            if cpu_percent > 85 or memory_percent > 90:
                logger.info(f"🔥 מערכת עמוסה מדי: CPU {cpu_percent}%, RAM {memory_percent}%")
                return False
        except:
            pass

        return True


def get_user_folder_path():
    """קריאת נתיב התיקייה מקובץ ההגדרות"""
    config_paths = [
        script_dir / "user_folder_config.json",
        script_dir / "pages" / "config.json"
    ]

    for config_path in config_paths:
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                folder_path = config.get('folder') or config.get('user_images_path')

                if folder_path and Path(folder_path).exists():
                    logger.info(f"📁 נמצאה תיקייה: {folder_path}")
                    return folder_path

        except Exception as e:
            logger.warning(f"⚠️ לא ניתן לקרוא {config_path}: {e}")

    logger.warning("⚠️ לא נמצאה תיקיית משתמש מוגדרת")
    return None


def get_last_scan_time():
    """קריאת זמן הסריקה האחרונה"""
    scan_info_file = script_dir / "last_scan_info.json"

    try:
        if scan_info_file.exists():
            with open(scan_info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_scan_str = data.get('last_scan_time')
                if last_scan_str:
                    return datetime.fromisoformat(last_scan_str)
    except Exception as e:
        logger.warning(f"⚠️ לא ניתן לקרוא זמן סריקה אחרון: {e}")

    # ברירת מחדל - לפני 25 שעות
    return datetime.now() - timedelta(hours=25)


def save_last_scan_time():
    """שמירת זמן הסריקה הנוכחי"""
    scan_info_file = script_dir / "last_scan_info.json"

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


def find_new_images(folder_path, last_scan_time):
    """מציאת תמונות שנוספו מהסריקה האחרונה"""

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
    new_images = []

    try:
        logger.info(f"🔍 סורק תיקייה: {folder_path}")

        for root, dirs, files in os.walk(folder_path):
            # דילוג על תיקיות מערכת
            dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('$')]

            for file in files:
                try:
                    file_path = Path(root) / file

                    # בדיקת הרחבה
                    if file_path.suffix.lower() not in image_extensions:
                        continue

                    # בדיקת תאריך שינוי
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if file_modified > last_scan_time:
                        # בדיקת גודל קובץ (לא ריק)
                        if file_path.stat().st_size > 0:
                            new_images.append(str(file_path))

                except Exception as e:
                    logger.warning(f"⚠️ שגיאה בבדיקת קובץ {file}: {e}")
                    continue

        logger.info(f"📸 נמצאו {len(new_images)} תמונות חדשות")
        return new_images

    except Exception as e:
        logger.error(f"❌ שגיאה בסריקת תיקייה: {e}")
        return []


def process_images_with_smart_strategy(image_paths):
    """עיבוד תמונות עם אסטרטגיה חכמה - ללא הגבלות!"""
    strategy = SmartProcessingStrategy()
    total_images = len(image_paths)

    logger.info(f"🧠 מתחיל עיבוד חכם של {total_images} תמונות")

    # חישוב אסטרטגיה ראשונית
    batch_size = strategy.calculate_optimal_batch_size(total_images)
    logger.info(f"📊 גודל batch מומלץ: {batch_size} תמונות")

    processed_count = 0
    start_time = time.time()
    avg_time_per_image = None

    try:
        # ייבוא הכלים
        from services.blip_captioner import Blip2Captioner
        from services.text_encoder import encode_text
        from db.setup import get_db
        from db.user_image_access import add_user_image, image_exists

        captioner = Blip2Captioner.get_instance()
        db = next(get_db())

        try:
            while processed_count < total_images:
                # בדיקה האם להמשיך
                if not strategy.should_continue_processing(start_time, processed_count, total_images):
                    logger.info(f"⏸️ עצירה זמנית. עובדו {processed_count}/{total_images} תמונות")
                    break

                # חישוב batch נוכחי
                remaining_images = total_images - processed_count
                current_batch_size = min(batch_size, remaining_images)

                current_batch = image_paths[processed_count:processed_count + current_batch_size]

                logger.info(f"🔄 מעבד batch {processed_count + 1}-{processed_count + current_batch_size}")

                batch_start_time = time.time()
                batch_processed = 0

                # עיבוד הbatch הנוכחי
                for image_path in current_batch:
                    try:
                        # בדיקה שהתמונה לא קיימת כבר
                        normalized_path = image_path.replace("\\", "/")
                        if image_exists(db, normalized_path):
                            continue

                        # עיבוד התמונה
                        image_start_time = time.time()

                        caption = captioner.generate_caption(image_path)
                        embedding = encode_text(caption)
                        add_user_image(db, caption, embedding.tolist(), normalized_path)

                        # עדכון זמן ממוצע
                        image_time = time.time() - image_start_time
                        if avg_time_per_image is None:
                            avg_time_per_image = image_time
                        else:
                            avg_time_per_image = (avg_time_per_image * 0.9) + (image_time * 0.1)

                        batch_processed += 1
                        processed_count += 1

                        # שמירה תקופתית
                        if batch_processed % 10 == 0:
                            db.commit()
                            logger.info(f"💾 נשמרו {processed_count} תמונות (זמן ממוצע: {avg_time_per_image:.1f}s)")

                    except Exception as e:
                        logger.error(f"❌ שגיאה בעיבוד {image_path}: {e}")
                        continue

                # סיום batch
                db.commit()
                batch_time = time.time() - batch_start_time

                logger.info(f"✅ batch הושלם: {batch_processed} תמונות ב-{batch_time / 60:.1f} דקות")

                # עדכון אסטרטגיה לbatch הבא
                if avg_time_per_image:
                    remaining = total_images - processed_count
                    if remaining > 0:
                        new_batch_size = strategy.calculate_optimal_batch_size(remaining, avg_time_per_image)
                        if new_batch_size != batch_size:
                            batch_size = new_batch_size
                            logger.info(f"🔧 עדכון גודל batch ל-{batch_size}")

            # סיכום
            total_time = time.time() - start_time
            remaining_images = total_images - processed_count

            result = {
                'processed': processed_count,
                'total': total_images,
                'remaining': remaining_images,
                'time_taken': total_time,
                'avg_time_per_image': avg_time_per_image,
                'completed': remaining_images == 0
            }

            if remaining_images > 0:
                estimated_sessions = (remaining_images / batch_size) + 1
                logger.info(f"📈 נותרו {remaining_images} תמונות, הערכה: {estimated_sessions:.0f} סשנים נוספים")

            return result

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ שגיאה כללית בעיבוד חכם: {e}")
        return {
            'error': str(e),
            'processed': processed_count,
            'total': total_images
        }


def should_scan():
    """בדיקה האם צריך לבצע סריקה"""
    last_scan = get_last_scan_time()
    now = datetime.now()
    hours_passed = (now - last_scan).total_seconds() / 3600

    should = hours_passed >= 20

    logger.info(f"⏰ עברו {hours_passed:.1f} שעות מהסריקה האחרונה")
    logger.info(f"🎯 צריך סריקה: {should}")

    return should


def main():
    """פונקציה ראשית"""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("🌙 מתחיל סריקה יומית אוטומטית (אסטרטגיה חכמה)")
    logger.info(f"🕐 זמן התחלה: {start_time}")

    try:
        if not should_scan():
            logger.info("ℹ️ סריקה לא נדרשת עדיין")
            return

        folder_path = get_user_folder_path()

        if not folder_path or not Path(folder_path).exists():
            logger.warning(f"❌ לא נמצאה תיקיית המשתמש: {folder_path}")
            logger.info("➡️ הסריקה הופסקה – אך האפליקציה תמשיך לפעול עם הנתונים הקיימים.")
            return

        if not folder_path:
            logger.warning("⚠️ לא נמצאה תיקיית משתמש - מסיים")
            return

        last_scan = get_last_scan_time()
        new_images = find_new_images(folder_path, last_scan)

        if not new_images:
            logger.info("✅ אין תמונות חדשות לעיבוד")
            save_last_scan_time()
            return
        logger.info(f"📸 נמצאו {len(new_images)} תמונות חדשות")

        # עיבוד חכם - ללא הגבלות מלאכותיות!
        result = process_images_with_smart_strategy(new_images)

        if 'error' in result:
            logger.error(f"❌ שגיאה בעיבוד: {result['error']}")
        else:
            logger.info(f"🎉 עיבוד הושלם:")
            logger.info(f"   📸 עובדו: {result['processed']}/{result['total']} תמונות")
            logger.info(f"   ⏱️ זמן כולל: {result['time_taken'] / 60:.1f} דקות")
            logger.info(f"   ⚡ זמן ממוצע לתמונה: {result.get('avg_time_per_image', 0):.1f} שניות")

            if result['remaining'] > 0:
                logger.info(f"   📋 נותרו: {result['remaining']} תמונות לסשן הבא")
            else:
                logger.info("   🎊 כל התמונות עובדו בהצלחה!")

        save_last_scan_time()
    except Exception as e:
        logger.error(f"❌ שגיאה כללית: {e}")
        logger.error(f"📋 מידע נוסף: {traceback.format_exc()}")
    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"⏱️ זמן ביצוע כולל: {duration}")
        logger.info("🏁 סריקה יומית הושלמה")
        logger.info("=" * 60)
if __name__ == "__main__":
    main()