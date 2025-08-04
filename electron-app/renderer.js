const fs = require("fs");
const path = require("path");
const { ipcRenderer } = require("electron");
const configPath = path.join(__dirname, "config.json");
let folderPath = "";

if (fs.existsSync(configPath)) {
    const data = fs.readFileSync(configPath, "utf8");
    const config = JSON.parse(data);
    folderPath = config.folderPath;
}
window.addEventListener("DOMContentLoaded", () => {
    // Add beautiful button styles
    const buttonStyles = document.createElement('style');
    buttonStyles.id = 'beautiful-button-styles';
    buttonStyles.textContent = `
        .btn-container {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            margin: 24px 0;
            padding: 20px;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 20px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
        }

        .btn-beautiful {
            position: relative;
            padding: 14px 28px;
            border: none;
            border-radius: 16px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            min-width: 160px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .btn-beautiful::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
            transition: left 0.5s;
        }

        .btn-beautiful:hover::before {
            left: 100%;
        }

        .btn-beautiful:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }

        .btn-beautiful:active {
            transform: translateY(-1px) scale(1.02);
        }

        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #2563eb, #1e40af);
        }

        .btn-secondary {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }

        .btn-secondary:hover {
            background: linear-gradient(135deg, #0d9488, #047857);
        }

        .btn-accent {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
        }

        .btn-accent:hover {
            background: linear-gradient(135deg, #e5a313, #c2710c);
        }

        .btn-special {
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            color: white;
        }

        .btn-special:hover {
            background: linear-gradient(135deg, #7c3aed, #6d28d9);
        }

        .btn-icon {
            font-size: 1.2rem;
            margin-right: 4px;
        }

        @media (max-width: 768px) {
            .btn-container {
                flex-direction: column;
                gap: 12px;
            }
            
            .btn-beautiful {
                width: 100%;
                max-width: 280px;
            }
        }
    `;
    document.head.appendChild(buttonStyles);

    const queryInput = document.getElementById("search-input");
    const savedQuery = localStorage.getItem("searchQuery");
    if (savedQuery) {
        queryInput.value = savedQuery;
        localStorage.removeItem("searchQuery");
    }
    const resultsContainer = document.getElementById("results");
    const suggestionsBox = document.createElement("div");
    suggestionsBox.classList.add("suggestions-box");
    suggestionsBox.style.cssText = `
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        width: 100%;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        z-index: 1000;
        max-height: 280px;
        overflow-y: auto;
        margin-top: 4px;
    `;

    // הוספת הstyles לparent
    queryInput.parentNode.style.position = "relative";
    queryInput.parentNode.appendChild(suggestionsBox);

    let typingTimer;
    let currentRequest = null; // למניעת בקשות מקבילות

    // מאזין לכתיבה בשדה החיפוש
    queryInput.addEventListener("input", () => {
        clearTimeout(typingTimer);
        // ביטול בקשה קודמת אם קיימת
        if (currentRequest) {
            currentRequest.abort();
        }
        typingTimer = setTimeout(fetchSuggestions, 300);
    });
document.getElementById("history-button").addEventListener("click", async () => {
    const resultsContainer = document.getElementById("results");
    if (!resultsContainer) return;

    resultsContainer.innerHTML = "";
    if (loadingDiv) loadingDiv.style.display = "block";

    try {
        const res = await fetch("http://localhost:8001/history");
        const data = await res.json();

        const filtered = data.filter(entry =>
            Array.isArray(entry.results) && entry.results.length > 0
        );

        if (filtered.length === 0) {
            showStyledAlert("No history found", "info");
            return;
        }

        displayHistoryEntries(filtered);
        showStyledAlert(`Loaded ${filtered.length} history entries`, "info");

    } catch (error) {
        console.error("❌ Error fetching history:", error);
        showStyledAlert("Failed to load history", "error");
    } finally {
        if (loadingDiv) loadingDiv.style.display = "none";
        resultsContainer.style.opacity = "1";
    }
});


    document.addEventListener("click", (e) => {
        if (!suggestionsBox.contains(e.target) && e.target !== queryInput) {
            suggestionsBox.style.display = "none";
        }
    });
    queryInput.addEventListener("keydown", (e) => {
        const suggestions = suggestionsBox.querySelectorAll(".suggestion-item");
        const activeSuggestion = suggestionsBox.querySelector(".suggestion-active");

        if (e.key === "ArrowDown") {
            e.preventDefault();
            if (activeSuggestion) {
                activeSuggestion.classList.remove("suggestion-active");
                const next = activeSuggestion.nextElementSibling;
                if (next) {
                    next.classList.add("suggestion-active");
                } else {
                    suggestions[0]?.classList.add("suggestion-active");
                }
            } else {
                suggestions[0]?.classList.add("suggestion-active");
            }
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            if (activeSuggestion) {
                activeSuggestion.classList.remove("suggestion-active");
                const prev = activeSuggestion.previousElementSibling;
                if (prev) {
                    prev.classList.add("suggestion-active");
                } else {
                    suggestions[suggestions.length - 1]?.classList.add("suggestion-active");
                }
            }
        } else if (e.key === "Enter") {
            if (activeSuggestion) {
                e.preventDefault();
                queryInput.value = activeSuggestion.textContent;
                suggestionsBox.style.display = "none";
            }
        } else if (e.key === "Escape") {
            suggestionsBox.style.display = "none";
        }
    });

    function fetchSuggestions() {
        const query = queryInput.value.trim();
        if (!query || query.length < 2) {
            suggestionsBox.style.display = "none";
            return;
        }

        // יצירת AbortController לביטול בקשות
        const controller = new AbortController();
        currentRequest = controller;

        console.log("🔍 מחפש הצעות עבור:", query);

        fetch(`http://localhost:8001/suggest_captions?prefix=${encodeURIComponent(query)}`, {
            signal: controller.signal
        })
        .then((res) => {
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then((suggestions) => {
            console.log("📝 התקבלו הצעות:", suggestions);

            suggestionsBox.innerHTML = "";
            if (!suggestions || suggestions.length === 0) {
                suggestionsBox.style.display = "none";
                return;
            }

            suggestions.forEach((suggestion, index) => {
                const div = document.createElement("div");
                div.textContent = suggestion;
                div.className = "suggestion-item";
                div.style.cssText = `
                    padding: 12px 20px;
                    cursor: pointer;
                    font-size: 0.95rem;
                    font-family: Georgia, serif;
                    color: #2c1810;
                    border-bottom: 1px solid #f1f5f9;
                    transition: all 0.2s ease;
                `;

                // hover effects
                div.addEventListener("mouseenter", () => {
                    // הסרת active מכל ההצעות
                    suggestionsBox.querySelectorAll(".suggestion-item").forEach(item => {
                        item.classList.remove("suggestion-active");
                        item.style.background = "";
                    });
                    div.classList.add("suggestion-active");
                    div.style.background = "#f8fafc";
                });

                div.addEventListener("mouseleave", () => {
                    div.style.background = "";
                });

                div.addEventListener("click", () => {
                    queryInput.value = suggestion;
                    suggestionsBox.style.display = "none";
                    queryInput.focus();
                });

                suggestionsBox.appendChild(div);
            });

            // הוספת CSS לactive suggestion
            const style = document.createElement('style');
            if (!document.getElementById('suggestions-style')) {
                style.id = 'suggestions-style';
                style.textContent = `
                    .suggestion-active {
                        background: #f8fafc !important;
                        color: #1e40af !important;
                    }
                `;
                document.head.appendChild(style);
            }

            suggestionsBox.style.display = "block";
        })
        .catch((err) => {
            if (err.name !== 'AbortError') {
                console.error("❌ שגיאה בהצעות:", err);
                suggestionsBox.style.display = "none";
            }
        })
        .finally(() => {
            currentRequest = null;
        });
    }
    // פתיחת clusters.html בדפדפן של האפליקציה
document.getElementById("view-clusters-button").addEventListener("click", () => {
    window.location.href = "clusters.html";
});



    // יצירת loading div
    let loadingDiv = document.getElementById("loading");
    if (!loadingDiv && resultsContainer && resultsContainer.parentNode) {
        loadingDiv = document.createElement("div");
        loadingDiv.id = "loading";
        loadingDiv.style.cssText = `
            display: none;
            text-align: center;
            padding: 2rem;
            margin: 1rem;
            background: linear-gradient(135deg, #99f6e4, #5eead4);
            border-radius: 20px;
            box-shadow: 0 16px 32px rgba(0, 0, 0, 0.08);
            color: #0f172a;
            font-weight: 600;
            font-size: 1.1rem;
            animation: pulse 2s infinite;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(0, 0, 0, 0.05);
        `;

        loadingDiv.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
                <div style="
                    width: 24px;
                    height: 24px;
                    border: 3px solid rgba(0,0,0,0.1);
                    border-top: 3px solid #0f172a;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <span>Loading amazing results...</span>
            </div>
        `;

        if (!document.getElementById('loading-animations')) {
            const style = document.createElement('style');
            style.id = 'loading-animations';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                @keyframes pulse {
                    0%, 100% { transform: scale(1); opacity: 0.9; }
                    50% { transform: scale(1.02); opacity: 1; }
                }
                @keyframes slideUp {
                    from { opacity: 0; transform: translateY(30px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        resultsContainer.parentNode.insertBefore(loadingDiv, resultsContainer);
    }

    // 🔥 כפתור חיפוש אישי - עם שמירת תוצאות!
    document.getElementById("search-personal-button").addEventListener("click", async () => {
        const query = queryInput.value.trim();
        if (!query) {
            showStyledAlert("נא להזין שאילתת חיפוש", "warning");
            return;
        }

        let folder = "";
        try {
            const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
            folder = config.user_images_path;
        } catch (err) {
            console.error("⚠️ שגיאה בקריאת config.json:", err);
        }

        if (!folder) {
            showStyledAlert("No folder selected. Please select a folder in settings.", "error");
            return;
        }

        try {
            if (loadingDiv) loadingDiv.style.display = "block";
            resultsContainer.innerHTML = "";
            resultsContainer.style.opacity = "0.5";

            console.log("🔍 Searching for:", query);
            const url = `http://localhost:8001/custom/search_folder?query=${encodeURIComponent(query)}&folder_path=${encodeURIComponent(folder)}`;
            const response = await fetch(url);
            const data = await response.json();

            console.log("📊 Search results:", data.results?.length || 0, "results");

            // 🔥 שמירה רק אם יש תוצאות!
            if (data.results && data.results.length > 0) {
                console.log("💾 Saving search with", data.results.length, "results");
                await saveSearchToHistory(query, data.results);
            } else {
                console.log("⏭️ No results - not saving to history");
                showStyledAlert("No results found - search not saved to history", "info");
            }

            displaySearchResults(data.results);
        } catch (error) {
            console.error("❌ שגיאה בבקשת חיפוש:", error);
            showStyledAlert("אירעה שגיאה בחיפוש", "error");
        } finally {
            if (loadingDiv) loadingDiv.style.display = "none";
            resultsContainer.style.opacity = "1";
        }
    });

 // הוסף את זה בתחילת הfetch של חיפוש COCO בrenderer.js:

// מצא את הקטע הזה:
document.getElementById("search-coco-button").addEventListener("click", async () => {
    const query = queryInput.value.trim();
    if (!query) {
        showStyledAlert("נא להזין שאילתת חיפוש", "warning");
        return;
    }

    try {
        if (loadingDiv) loadingDiv.style.display = "block";
        resultsContainer.innerHTML = "";
        resultsContainer.style.opacity = "0.5";

        console.log("🔍 Searching COCO for:", query);

        // 🔥 זה הURL שצריך לבדוק!
        const url = `http://localhost:8001/search_coco?query=${encodeURIComponent(query)}`;
        console.log("🔗 COCO Search URL:", url); // 👈 הוסף את זה!

        const response = await fetch(url);
        console.log("📡 COCO Response status:", response.status); // 👈 וגם את זה!

        const data = await response.json();
        console.log("📊 COCO Search results:", data); // 👈 וגם את זה!
        console.log("📊 COCO Results count:", data.results?.length || 0);

        // בדיקה של התוצאה הראשונה
        if (data.results && data.results.length > 0) {
            console.log("🔍 First COCO result:", data.results[0]);
            console.log("🔍 First COCO result path:", data.results[0].path);
            console.log("🔍 Is COCO URL?", data.results[0].path?.startsWith("http"));
        }

        // שמירה רק אם יש תוצאות
        if (data.results && data.results.length > 0) {
            console.log("💾 Saving COCO search with", data.results.length, "results");
            await saveSearchToHistory(query, data.results);
        } else {
            console.log("⏭️ No COCO results - not saving to history");
            showStyledAlert("No results found - search not saved to history", "info");
        }

        displaySearchResults(data.results);
    } catch (error) {
        console.error("❌ שגיאה בבקשת חיפוש COCO:", error);
        showStyledAlert("אירעה שגיאה בחיפוש COCO", "error");
    } finally {
        if (loadingDiv) loadingDiv.style.display = "none";
        resultsContainer.style.opacity = "1";
    }
});
    // 🔥 הפונקציה החשובה - שמירת חיפוש עם תוצאות
    async function saveSearchToHistory(query, results = []) {
        try {
            // וידוא שיש תוצאות לפני השמירה
            if (!results || results.length === 0) {
                console.log("⏭️ No results to save");
                return;
            }

            console.log("📤 Sending search to history:", query, "with", results.length, "results");

            const response = await fetch('http://localhost:8001/save_search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    results: results,
                    timestamp: new Date().toISOString()
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                console.log("✅ Search saved to history successfully!");
                showStyledAlert("Search saved to history! 📅", "info");
            } else {
                console.warn("⚠️ Failed to save search:", result.error || "Unknown error");
            }
        } catch (error) {
            console.error("❌ Error saving search to history:", error);
        }
    }

function displaySearchResults(results) {
    resultsContainer.innerHTML = "";

    if (!results || results.length === 0) {
        resultsContainer.innerHTML = `
            <div style="
                text-align: center;
                padding: 3rem;
                background: linear-gradient(135deg, #fef9c3, #fde68a);
                border-radius: 20px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.08);
                color: #78350f;
                font-weight: 600;
                font-size: 1.1rem;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                No matching results found.
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">Try different keywords</div>
            </div>
        `;
        return;
    }

    results.forEach((result, index) => {
        const card = document.createElement("div");
        card.style.cssText = `
            background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
            border-radius: 16px;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.05);
            padding: 1.5rem;
            transition: all 0.3s ease-in-out;
            border: 1px solid #e2e8f0;
            animation: slideUp 0.6s ease-out ${index * 0.1}s both;
            position: relative;
            overflow: hidden;
            margin-bottom: 2rem;
        `;

        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-6px) scale(1.015)';
            card.style.boxShadow = '0 16px 32px rgba(0, 0, 0, 0.08)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0) scale(1)';
            card.style.boxShadow = '0 10px 24px rgba(0, 0, 0, 0.05)';
        });

        const img = document.createElement("img");
        img.src = result.path;
        img.alt = result.caption || "Image";
        img.style.cssText = `
            width: 100%;
            height: 12rem;
            object-fit: cover;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        `;

        img.onerror = () => {
            console.error(`❌ Failed to load image: ${img.src}`);
            img.src = createSafePlaceholder("Image Load Failed", result.path || "No path");
        };

        img.onload = () => {
            console.log(`✅ Image loaded: ${img.src}`);
        };

        const caption = document.createElement("p");
        caption.textContent = result.caption || "No caption";
        caption.style.cssText = `
            font-size: 0.95rem;
            color: #334155;
            line-height: 1.6;
            margin-bottom: 0.75rem;
            font-weight: 500;
        `;

        const score = document.createElement("div");
        score.style.cssText = `
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: #2dd4bf;
            color: white;
            padding: 0.4rem 1rem;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(45, 212, 191, 0.3);
        `;
        score.innerHTML = `<span>⭐</span> ${result.score}`;

const infoIcon = document.createElement("div");
infoIcon.textContent = "🧠";
infoIcon.style.cssText = `
    position: absolute;
    top: 1rem;
    right: 1rem;
    font-size: 1.3rem;
    cursor: pointer;
    opacity: 0.6;
    transition: all 0.3s ease;
    padding: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`;

// יצירת פופאפ מעוצב
const wordsPopup = document.createElement("div");
const matchedWords = result.matched_words || [];
wordsPopup.innerHTML = `
    <div style="
        position: absolute;
        top: 100%;
        right: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        min-width: 200px;
        transform: translateY(8px) scale(0.8);
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        z-index: 1000;
        pointer-events: none;
    ">
        <div style="
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 6px;
        ">
            <span>🎯</span> Matched Words
        </div>
        ${matchedWords.length > 0 ? 
            `<div style="
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            ">
                ${matchedWords.map(word => `
                    <span style="
                        background: rgba(255, 255, 255, 0.2);
                        padding: 4px 8px;
                        border-radius: 8px;
                        font-size: 0.8rem;
                        font-weight: 500;
                        border: 1px solid rgba(255, 255, 255, 0.3);
                    ">${word}</span>
                `).join('')}
            </div>` 
            : '<div style="opacity: 0.8; font-style: italic;">No specific words matched</div>'
        }
        <div style="
            position: absolute;
            top: -6px;
            right: 12px;
            width: 12px;
            height: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transform: rotate(45deg);
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            border-left: 1px solid rgba(255, 255, 255, 0.2);
        "></div>
    </div>
`;

infoIcon.appendChild(wordsPopup);

// אפקטי ריחוף מתקדמים
let hoverTimeout;

infoIcon.addEventListener("mouseenter", () => {
    clearTimeout(hoverTimeout);
    infoIcon.style.opacity = "1";
    infoIcon.style.transform = "scale(1.1)";

    const popup = wordsPopup.firstElementChild;
    popup.style.transform = "translateY(8px) scale(1)";
    popup.style.opacity = "1";
    popup.style.pointerEvents = "auto";
});

infoIcon.addEventListener("mouseleave", () => {
    hoverTimeout = setTimeout(() => {
        infoIcon.style.opacity = "0.6";
        infoIcon.style.transform = "scale(1)";

        const popup = wordsPopup.firstElementChild;
        popup.style.transform = "translateY(8px) scale(0.8)";
        popup.style.opacity = "0";
        popup.style.pointerEvents = "none";
    }, 150);
});

wordsPopup.addEventListener("mouseenter", () => {
    clearTimeout(hoverTimeout);
});

wordsPopup.addEventListener("mouseleave", () => {
    infoIcon.style.opacity = "0.6";
    infoIcon.style.transform = "scale(1)";

    const popup = wordsPopup.firstElementChild;
    popup.style.transform = "translateY(8px) scale(0.8)";
    popup.style.opacity = "0";
    popup.style.pointerEvents = "none";
});
        card.appendChild(img);
        card.appendChild(caption);
        card.appendChild(score);
        card.appendChild(infoIcon);
        resultsContainer.appendChild(card);
    });
}

// וודא שיש לך גם את הפונקציה הזו:
function createSafePlaceholder(text, details = "") {
  try {
    const cleanText = String(text || "Error").replace(/[^\x00-\x7F]/g, "?");
    const cleanDetails = String(details || "").replace(/[^\x00-\x7F]/g, "?").substring(0, 30);

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="192">
      <rect width="100%" height="100%" fill="#f3f4f6"/>
      <text x="50%" y="45%" font-family="Arial" font-size="16" fill="#6b7280" text-anchor="middle">
        ${cleanText}
      </text>
      <text x="50%" y="65%" font-family="Arial" font-size="12" fill="#9ca3af" text-anchor="middle">
        ${cleanDetails}
      </text>
      <circle cx="150" cy="96" r="25" fill="#e5e7eb"/>
      <text x="150" y="105" font-family="Arial" font-size="20" fill="#9ca3af" text-anchor="middle">📷</text>
    </svg>`;

    return `data:image/svg+xml,${encodeURIComponent(svg)}`;
  } catch (error) {
    console.error("Placeholder error:", error);
    return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='192'%3E%3Crect width='100%25' height='100%25' fill='%23f3f4f6'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle'%3EError%3C/text%3E%3C/svg%3E";
  }
}
    function showStyledAlert(message, type = "info") {
        const colors = {
            warning: { bg: "linear-gradient(135deg, #fde68a, #facc15)", icon: "⚠️" },
            error: { bg: "linear-gradient(135deg, #fca5a5, #ef4444)", icon: "❌" },
            info: { bg: "linear-gradient(135deg, #93c5fd, #3b82f6)", icon: "ℹ️" }
        };
        const alertDiv = document.createElement("div");
        alertDiv.style.cssText = `
            position: fixed;
            top: 2rem;
            right: 2rem;
            z-index: 1000;
            background: ${colors[type].bg};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 15px;
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
            font-weight: 600;
            animation: slideInRight 0.5s ease-out;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            max-width: 300px;
        `;

        alertDiv.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.2rem;">${colors[type].icon}</span>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(alertDiv);
        setTimeout(() => {
            alertDiv.style.animation = "slideInRight 0.5s ease-out reverse";
            setTimeout(() => alertDiv.remove(), 500);
        }, 4000);
    }
});
function displayClusters(clustersData) {
    console.log("🎨 מציג clusters:", clustersData);

    const resultsContainer = document.getElementById("results");
    if (!resultsContainer) {
        console.error("❌ לא נמצא results container");
        return;
    }

    resultsContainer.innerHTML = "";

    if (!clustersData || clustersData.length === 0) {
        resultsContainer.innerHTML = `
            <div style="
                text-align: center;
                padding: 3rem;
                background: linear-gradient(135deg, #fef9c3, #fde68a);
                border-radius: 20px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.08);
                color: #78350f;
                font-weight: 600;
                font-size: 1.1rem;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🧠</div>
                No clusters found.
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">Try running clustering again</div>
            </div>
        `;
        return;
    }

    // יצירת כותרת סיכום
    const summaryDiv = document.createElement("div");
    summaryDiv.style.cssText = `
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 24px rgba(59, 130, 246, 0.3);
    `;
    summaryDiv.innerHTML = `
        <h2 style="font-size: 2rem; margin-bottom: 1rem;">🧠 Smart Clustering Results</h2>
        <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 12px;">
                <div style="font-size: 1.5rem; font-weight: bold;">${clustersData.length}</div>
                <div style="font-size: 0.9rem;">Clusters</div>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 12px;">
                <div style="font-size: 1.5rem; font-weight: bold;">${clustersData.reduce((sum, c) => sum + c.image_count, 0)}</div>
                <div style="font-size: 0.9rem;">Total Images</div>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 12px;">
                <div style="font-size: 1.5rem; font-weight: bold;">${Math.round(clustersData.reduce((sum, c) => sum + c.confidence, 0) / clustersData.length)}%</div>
                <div style="font-size: 0.9rem">Avg Confidence</div>
            </div>
        </div>
    `;
    resultsContainer.appendChild(summaryDiv);

    // הצגת כל cluster
    clustersData.forEach((cluster, index) => {
        const clusterCard = document.createElement("div");
        clusterCard.style.cssText = `
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 20px;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.06);
            padding: 2rem;
            margin-bottom: 2rem;
            transition: all 0.3s ease;
            border: 1px solid #e2e8f0;
            animation: slideUp 0.6s ease-out ${index * 0.1}s both;
        `;

        // כותרת הcluster
        const header = document.createElement("div");
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #e2e8f0;
        `;

        const confidenceColor = cluster.confidence > 80 ? '#10b981' :
                               cluster.confidence > 50 ? '#f59e0b' : '#ef4444';

        header.innerHTML = `
            <div>
                <h3 style="font-size: 1.5rem; font-weight: bold; color: #1e293b; margin-bottom: 0.5rem;">
                    🏷️ ${cluster.name}
                </h3>
                <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
                    <span style="background: #3b82f6; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                        📊 ${cluster.image_count} images
                    </span>
                    <span style="background: ${confidenceColor}; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                        🎯 ${cluster.confidence}% confidence
                    </span>
                </div>
            </div>
        `;

        // מילות מפתח
        if (cluster.keywords && cluster.keywords.length > 0) {
            const keywordsDiv = document.createElement("div");
            keywordsDiv.style.cssText = `
                margin-bottom: 1rem;
            `;
            keywordsDiv.innerHTML = `
                <div style="font-weight: 600; color: #64748b; margin-bottom: 0.5rem;">🔤 Keywords:</div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    ${cluster.keywords.map(keyword => 
                        `<span style="background: #e0e7ff; color: #3730a3; padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.8rem;">${keyword}</span>`
                    ).join('')}
                </div>
            `;
            clusterCard.appendChild(header);
            clusterCard.appendChild(keywordsDiv);
        } else {
            clusterCard.appendChild(header);
        }

        // גלריה של תמונות (הצג עד 12 תמונות)
        if (cluster.images && cluster.images.length > 0) {
            const gallery = document.createElement("div");
            gallery.style.cssText = `
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 1rem;
                margin-top: 1rem;
            `;

            const imagesToShow = cluster.images.slice(0, 12); // הצג רק 12 תמונות ראשונות

            imagesToShow.forEach((image, imgIndex) => {
                const imgWrapper = document.createElement("div");
                imgWrapper.style.cssText = `
                    position: relative;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    transition: transform 0.3s ease;
                    background: #f1f5f9;
                `;

                imgWrapper.addEventListener('mouseenter', () => {
                    imgWrapper.style.transform = 'scale(1.05)';
                });

                imgWrapper.addEventListener('mouseleave', () => {
                    imgWrapper.style.transform = 'scale(1)';
                });

                const img = document.createElement("img");
                img.style.cssText = `
                    width: 100%;
                    height: 140px;
                    object-fit: cover;
                `;

                // טיפול בנתיבי תמונות
                if (image.path) {
                    if (image.path.startsWith("http")) {
                        img.src = image.path; // תמונות COCO
                    } else {
                        // תמונות מקומיות
                        const normalizedPath = image.path.replace(/\\/g, '/');
                        img.src = `file:///${normalizedPath}`;
                    }
                } else {
                    img.src = createSafePlaceholder("No Path");
                }

                img.onerror = () => {
                    img.src = createSafePlaceholder("Load Error", image.path);
                };

                // כותרת תמונה
                const caption = document.createElement("div");
                caption.style.cssText = `
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(transparent, rgba(0,0,0,0.8));
                    color: white;
                    padding: 1rem 0.5rem 0.5rem;
                    font-size: 0.75rem;
                    line-height: 1.2;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                `;
                caption.textContent = image.caption || 'No caption';

                imgWrapper.addEventListener('mouseenter', () => {
                    caption.style.opacity = '1';
                });

                imgWrapper.addEventListener('mouseleave', () => {
                    caption.style.opacity = '0';
                });

                imgWrapper.appendChild(img);
                imgWrapper.appendChild(caption);
                gallery.appendChild(imgWrapper);
            });

            // הצגת מספר תמונות נוספות אם יש
            if (cluster.images.length > 12) {
                const moreDiv = document.createElement("div");
                moreDiv.style.cssText = `
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #f1f5f9;
                    border: 2px dashed #94a3b8;
                    border-radius: 12px;
                    height: 140px;
                    color: #64748b;
                    font-weight: 600;
                    font-size: 0.9rem;
                `;
                moreDiv.innerHTML = `+${cluster.images.length - 12} more images`;
                gallery.appendChild(moreDiv);
            }

            clusterCard.appendChild(gallery);
        }

        resultsContainer.appendChild(clusterCard);
    });

    // הוספת אנימציה אם לא קיימת
    if (!document.getElementById('cluster-animations')) {
        const style = document.createElement('style');
        style.id = 'cluster-animations';
        style.textContent = `
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
        `;
        document.head.appendChild(style);
    }
}
document.getElementById("history-button").addEventListener("click", () => {
    window.location.href = "history.html";
});