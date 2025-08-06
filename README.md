# imaginFind – AI-Powered Personal & COCO Image Search 🔍

**imaginFind** is an AI-based image search application that allows users to search both their **personal image gallery** and the **COCO dataset** using natural language queries. The system works offline, with automatic caption generation, semantic similarity search, search history, and optional image clustering.

---

## 🚀 Features

- 🖼️ **Search in Personal Images** – Upload and search your own gallery  
- 🧠 **COCO Dataset Search** – Find images from the popular COCO dataset  
- 📝 **Offline Captioning** – Uses BLIP2 to generate image captions locally  
- 🔍 **Semantic Search** – Uses Word2Vec for text-to-image similarity  
- 🗂️ **Image Clustering** – Group images by topics  
- 🕓 **Search History** – Save and re-run previous searches  
- 📐 **Angle Similarity Visualization** – See how close images are to the query  
- 💬 **Offline Chatbot** – Ask questions about the system


---

## 🧠 AI Modules Used

| Module                | Purpose                                                     |
|-----------------------|-------------------------------------------------------------|
| **BLIP2**             | Generates captions for images to create semantic embeddings |
| **MiniLM**   | Measures similarity between cluster names   |
| **Word2Vec**          | Embeds user text queries for semantic similarity            |
| **Logistic Regression** | Custom-trained classifier to predict image categories prior to clustering |
| **KMeans**            | Clusters images within predicted categories                  |
| **PGVector**          | Stores image embeddings for efficient similarity search      |

---

## 🛠️ Tech Stack

| Area     | Technology Used                        |
|----------|----------------------------------------|
| Backend  | Python (FastAPI), SQLite               |
| AI       | Transformers, scikit-learn, Faiss      |
| Frontend | HTML, CSS, JavaScript (Electron-ready) |
| Tools    | Pillow, Uvicorn, Pydantic      |

---

## 📁 Project Structure
```
imaginFind/
├── server/
│   ├── main.py — Main backend FastAPI application
│   ├── routes/ — API route handlers
│   ├── services/ — Business logic and AI integration
│   └── db/ — Database models and migration scripts
├── models/
│   ├── blip2/ — BLIP2 captioning model files
│   ├── classifier/ — Trained Logistic Regression model and related files
│   └── word2vec/ — Word2Vec embeddings and utilities
├── client/
│   ├── index.html — Main frontend page
│   ├── renderer.js — Frontend JavaScript logic
│   ├── style1.css — Stylesheet for frontend
│   ├── history.html — Page to display search history
│   └── chat.html — Chatbot interface
├── screenshots/ — Folder containing application screenshots
│   ├── home.png
│   ├── search.png
│   ├── clusters.png
│   └── history.png
└── README.md — This documentation file
```
