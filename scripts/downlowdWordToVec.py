import gensim.downloader as api
import time

print("📦 מתחיל להוריד את המודל word2vec-google-news-300...")
print("📏 size: ~1.6GB")
print("⏳ זמן משוער: 5-20 דקות")

start_time = time.time()
model = api.load("word2vec-google-news-300")
end_time = time.time()

print(f"✅ המודל נטען בהצלחה!")
print(f"⏱️ זמן הורדה: {(end_time - start_time)/60:.1f} דקות")
print(f"📊 גודל אוצר המילים: {len(model.key_to_index):,} מילים")

print("\n🔍 בדיקת מילה 'computer':")
if 'computer' in model:
    print(f"📏 גודל וקטור: {len(model['computer'])} מימדים")
    print("🔢 ערכים ראשונים:", model['computer'][:5])
else:
    print("❌ המילה לא נמצאת")