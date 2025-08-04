from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.image_routes import router as image_router
from routes.custom_search_routes import router as custom_search_router
from routes.coco_image_routes import router as coco_image_router
from routes.search_routes import router as search_router
from routes.clustering_routes import router as clustering_router
from routes import daily_routes
from routes import caption_suggestions
from routes.history_routes import router as history_router
from routes.chatbot_routes import router as chatbot_router
from routes import user_folder_routes
from dotenv import load_dotenv
load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(image_router)
app.include_router(custom_search_router, prefix="/custom", tags=["Custom Search"])
app.include_router(coco_image_router)
app.include_router(search_router)
app.include_router(clustering_router)
app.include_router(caption_suggestions.router)
app.include_router(user_folder_routes.router)
app.include_router(daily_routes.router)
app.include_router(history_router)
app.include_router(chatbot_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)