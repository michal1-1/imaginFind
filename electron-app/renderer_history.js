document.addEventListener("DOMContentLoaded", async () => {
  const list = document.getElementById("history-list");

  console.log("📅 Loading beautiful search history...");

  try {
    const res = await fetch("http://localhost:8001/history");

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const rawHistory = await res.json();
    console.log("📊 Raw history data received:", rawHistory.length, "entries");

    // סינון חיפושים - רק חיפושים עם תוצאות!
    const filteredHistory = rawHistory.filter(entry => {
      return entry.results &&
             Array.isArray(entry.results) &&
             entry.results.length > 0 &&
             entry.results.some(result => result.path);
    });

    console.log("✅ Filtered history:", filteredHistory.length, "entries with results");

    if (!filteredHistory || filteredHistory.length === 0) {
      list.innerHTML = `
        <div class="no-history">
          No successful searches found yet.<br>
          <small style="font-size: 16px; margin-top: 16px; display: block; opacity: 0.8;">
            Perform searches that return results to see them here!
          </small>
        </div>
      `;
      return;
    }

    // ההיסטוריה כבר ממוינת מהשרת (החדש ביותר ראשון)
    filteredHistory.forEach((entry, index) => {
      console.log(`🖼️ Entry ${index}:`, {
        query: entry.query,
        resultsCount: entry.results?.length || 0,
        firstResult: entry.results?.[0]
      });

      const item = document.createElement("div");
      item.className = "history-item";

      // אנימציה מתקדמת לכל פריט
      item.style.animationDelay = `${index * 0.1}s`;

      // יצירת תמונה נציגית על בסיס התוצאות
      const previewImage = createEnhancedPreviewImage(entry.query, entry.results);

      item.innerHTML = `
        <div class="history-preview">
          ${previewImage}
        </div>
        <div class="history-info">
          <div class="history-query">🔍 ${escapeHtml(entry.query)}</div>
          <div class="history-timestamp">${formatEnhancedTimestamp(entry.timestamp)}</div>
          <div class="history-stats">${getEnhancedResultsStats(entry.results)}</div>
        </div>
        <button class="search-again-btn" onclick="searchAgain('${escapeHtml(entry.query).replace(/'/g, "\\'")}')">
          🔄 Search Again
        </button>
      `;

      list.appendChild(item);
    });

  } catch (error) {
    console.error("❌ Error loading history:", error);
    list.innerHTML = `
      <div class="no-history">
        Failed to load search history.<br>
        <small style="font-size: 16px; margin-top: 16px; display: block; opacity: 0.8;">
          Error: ${error.message}<br>
          Please check if the server is running on http://localhost:8001
        </small>
      </div>
    `;
  }
});

// 🖼️ יצירת תמונה נציגית משופרת עם דיבוג מלא
function createEnhancedPreviewImage(query, results) {
  console.log("🎨 Creating enhanced preview for:", query, "with results:", results);

  // וידוא שיש תוצאות עם תמונות
  if (results && results.length > 0 && results[0]) {
    const firstResult = results[0];
    console.log("📸 First result:", firstResult);

    let imageSrc;

    if (firstResult.path && firstResult.path.startsWith("http")) {
      // COCO images - נתיב מלא
      imageSrc = firstResult.path;
      console.log("🌐 COCO image URL:", imageSrc);
    } else if (firstResult.filename && firstResult.path) {
      // Personal images - צריך לבנות נתיב
      imageSrc = `http://localhost:8001/image/?filename=${encodeURIComponent(firstResult.filename)}&folder_path=${encodeURIComponent(firstResult.path)}`;
      console.log("💻 Personal image URL:", imageSrc);
    } else {
      console.log("❌ No valid path found in result:", firstResult);
      return createEnhancedPlaceholder(query);
    }

    return `
      <img src="${imageSrc}" alt="${escapeHtml(query)}" class="history-thumbnail" 
           onload="console.log('✅ Enhanced image loaded:', this.src)"
           onerror="console.log('❌ Enhanced image failed to load:', this.src); this.style.display='none'; this.nextElementSibling.style.display='flex';">
      <div class="history-placeholder" style="display: none;">
        <span class="history-icon">🖼️</span>
        <span class="history-query-short">${truncateText(query, 15)}</span>
      </div>
    `;
  } else {
    console.log("⚠️ No results or empty results for:", query);
    return createEnhancedPlaceholder(query);
  }
}

// יצירת placeholder משופר
function createEnhancedPlaceholder(query) {
  // בחירת אייקון מתאים לפי תוכן החיפוש
  let icon = '🔍';
  const lowerQuery = query.toLowerCase();

  if (lowerQuery.includes('sunset') || lowerQuery.includes('sunrise')) icon = '🌅';
  else if (lowerQuery.includes('flower') || lowerQuery.includes('garden')) icon = '🌸';
  else if (lowerQuery.includes('mountain') || lowerQuery.includes('landscape')) icon = '🏔️';
  else if (lowerQuery.includes('beach') || lowerQuery.includes('ocean')) icon = '🏖️';
  else if (lowerQuery.includes('food') || lowerQuery.includes('meal')) icon = '🍽️';
  else if (lowerQuery.includes('cat') || lowerQuery.includes('dog')) icon = '🐾';
  else if (lowerQuery.includes('car') || lowerQuery.includes('vehicle')) icon = '🚗';
  else if (lowerQuery.includes('house') || lowerQuery.includes('building')) icon = '🏠';
  else if (lowerQuery.includes('person') || lowerQuery.includes('people')) icon = '👥';

  return `
    <div class="history-placeholder">
      <span class="history-icon">${icon}</span>
      <span class="history-query-short">${truncateText(query, 15)}</span>
    </div>
  `;
}

// פורמט זמן משופר
function formatEnhancedTimestamp(timestamp) {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return 'Today, ' + date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } else if (diffDays === 1) {
      return 'Yesterday, ' + date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      });
    }
  } catch (error) {
    console.error("❌ Error formatting enhanced timestamp:", error);
    return new Date(timestamp).toLocaleDateString();
  }
}

// סטטיסטיקות תוצאות משופרות
function getEnhancedResultsStats(results) {
  if (!results || results.length === 0) {
    return '<span class="no-results">❌ No results</span>';
  }

  const count = results.length;
  let emoji, className;

  if (count >= 20) {
    emoji = '🎉';
    className = 'results-count';
  } else if (count >= 10) {
    emoji = '✨';
    className = 'results-count';
  } else if (count >= 5) {
    emoji = '📸';
    className = 'results-count';
  } else {
    emoji = '🔍';
    className = 'results-count';
  }

  return `<span class="${className}">${emoji} ${count} result${count !== 1 ? 's' : ''} found</span>`;
}

// קיצור טקסט
function truncateText(text, maxLength) {
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

// פונקציה לחיפוש מחדש
function searchAgain(query) {
  try {
    localStorage.setItem("searchQuery", query);
    console.log(`🔄 Searching again for: "${query}"`);

    // אפקט ויזואלי לפני המעבר
    document.body.style.opacity = '0.8';
    document.body.style.transform = 'scale(0.98)';

    setTimeout(() => {
      window.location.href = "index.html";
    }, 300);

  } catch (error) {
    console.error("❌ Error in searchAgain:", error);
  }
}

// פונקציה לחזרה לעמוד הראשי
function goBack() {
  try {
    console.log("🔙 Going back to main page");

    // אפקט ויזואלי לפני המעבר
    document.body.style.opacity = '0.8';
    document.body.style.transform = 'scale(0.98)';

    setTimeout(() => {
      window.location.href = "index.html";
    }, 300);

  } catch (error) {
    console.error("❌ Error in goBack:", error);
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}