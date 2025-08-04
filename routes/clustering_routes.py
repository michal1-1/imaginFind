from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.setup import get_db
from services.enhanced_cluster_processing_service import process_enhanced_clusters

router = APIRouter()

@router.get("/coco/clustering")
def get_clusters(db: Session = Depends(get_db)):
    try:
        print("🚀 Starting enhanced cluster processing...")

        # בדיקת מסד נתונים
        try:
            from db.models import ExtraTrainingImage
            images_count = db.query(ExtraTrainingImage).count()
            print(f"📊 Found {images_count} images in the database")

            if images_count == 0:
                print("❌ No images in the database - returning empty result")
                return []
        except Exception as db_error:
            print(f"❌ Database error: {db_error}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")

        # ביצוע קלאסטרינג משופר
        result = process_enhanced_clusters(db)
        print(f"✅ Enhanced clustering completed. Returning {len(result)} categories")

        return result

    except Exception as e:
        print(f"❌ General error during enhanced clustering: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Enhanced clustering error: {str(e)}")


@router.get("/coco/clustering/debug")
def debug_clusters(db: Session = Depends(get_db)):
    debug_info = {
        "database_status": "unknown",
        "images_count": 0,
        "classifier_status": "unknown"
    }

    try:
        from db.models import ExtraTrainingImage
        images_count = db.query(ExtraTrainingImage).count()
        debug_info["database_status"] = "connected"
        debug_info["images_count"] = images_count

        if images_count > 0:
            sample_images = db.query(ExtraTrainingImage).limit(3).all()
            debug_info["sample_images"] = []
            for img in sample_images:
                debug_info["sample_images"].append({
                    "path": getattr(img, 'image_path', 'No path'),
                    "caption": getattr(img, 'blip_caption', '') or getattr(img, 'caption', 'No caption'),
                    "has_embedding": hasattr(img, 'embedding') and img.embedding is not None
                })

    except Exception as e:
        debug_info["database_status"] = f"error: {str(e)}"

    try:
        from services.classifier_predictor import get_classifier_model
        model = get_classifier_model()
        debug_info["classifier_status"] = "loaded" if model is not None else "failed"
    except Exception as e:
        debug_info["classifier_status"] = f"error: {str(e)}"

    return debug_info