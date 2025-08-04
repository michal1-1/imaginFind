import sys
import os
from pathlib import Path
from datetime import datetime
import json
import logging
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sqlalchemy.orm import Session
from db.setup import get_db
from db.user_image_access import add_user_image, image_exists
from services.blip_captioner import Blip2Captioner
from text_encoder import encode_text
from image_utils import is_image_file
from config import COMMIT_INTERVAL
script_dir = Path(__file__).parent.absolute()
log_file = script_dir / "scan_new_images.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
def get_user_folder_path():
    config_paths = [
        script_dir / "user_folder_config.json",
        script_dir.parent / "user_folder_config.json",
        script_dir / "pages" / "config.json"
    ]
    logger.info(f": {script_dir}")
    for config_path in config_paths:
        try:
            logger.info(f" {config_path}")
            if config_path.exists():
                logger.info(f" {config_path}")
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                folder_path = (config.get('folder') or
                               config.get('user_images_path') or
                               config.get('path'))
                if folder_path:
                    folder_path_obj = Path(folder_path)
                    if folder_path_obj.exists():
                        logger.info(f" {folder_path}")
                        return str(folder_path)
                    else:
                        logger.warning(f" {folder_path}")
                else:
                    logger.warning(f" {config}")
        except Exception as e:
            logger.error(f"{config_path}: {e}")
            continue
    return None
def scan_and_update():
    start_time = datetime.now()
    logger.info(f"{start_time}")
    try:
        folder_path = get_user_folder_path()
        if not folder_path:
            return False
        logger.info(f"{folder_path}")
        try:
            db: Session = next(get_db())
        except Exception as e:
            return False
        try:
            captioner = Blip2Captioner()
        except Exception as e:
            db.close()
            return False
        processed_count = 0
        skipped_count = 0
        error_count = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('$')]
                for file in files:
                    file_path = os.path.join(root, file)
                    if not is_image_file(file_path):
                        continue
                    normalized_path = file_path.replace("\\", "/")
                    if image_exists(db, normalized_path):
                        skipped_count += 1
                        continue
                    try:
                        logger.info(f" {Path(file_path).name}")
                        caption = captioner.generate_caption(file_path)
                        embedding = encode_text(caption)
                        add_user_image(db, caption, embedding.tolist(), normalized_path)
                        processed_count += 1
                        logger.info(f" {Path(file_path).name}")
                        if processed_count % COMMIT_INTERVAL == 0:
                            db.commit()
                            logger.info(f"{processed_count} ")
                    except Exception as e:
                        error_count += 1
                        logger.error(f" {file_path}: {e}")
                        continue
            db.commit()
        finally:
            db.close()

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(" Scan Summary:")
        logger.info(f"   New photos added: {processed_count}")
        logger.info(f"   Existing images that were skipped: {skipped_count}")
        logger.info(f"    Errors: {error_count}")
        logger.info(f"  Execution time: {duration}")
        logger.info(" Scan completed")
        return True

    except Exception as e:
        return False
if __name__ == "__main__":
    try:
        success = scan_and_update()
        import gc
        gc.collect()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        sys.exit(1)
