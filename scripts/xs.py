from pathlib import Path
from services.blip_captioner import Blip2Captioner
from services.classifier_predictor import get_keyword_category
from tabulate import tabulate

# הנתיב לתיקיית האימון
EXTRA_TRAINING_DIR = Path("extra_training_data")

# טען את מודל BLIP
captioner = Blip2Captioner()

results = []

for category_dir in EXTRA_TRAINING_DIR.iterdir():
    if not category_dir.is_dir():
        continue

    category = category_dir.name
    for image_file in category_dir.glob("*.*"):
        try:
            caption = captioner.generate_caption(str(image_file))
            predicted_category = get_keyword_category(caption)
            match = "✅" if predicted_category == category else "❌"
            results.append({
                "File": image_file.name,
                "Folder": category,
                "Caption": caption,
                "Predicted": predicted_category,
                "Match": match
            })
        except Exception as e:
            results.append({
                "File": image_file.name,
                "Folder": category,
                "Caption": "ERROR",
                "Predicted": "ERROR",
                "Match": "❌"
            })

# הדפסת טבלה
print(tabulate(results, headers="keys", tablefmt="fancy_grid", maxcolwidths=[None, None, 50, None, None]))
