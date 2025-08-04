let allClustersData = [];
let currentCategory = null;

document.addEventListener("DOMContentLoaded", () => {
  fetchClusters();
});

async function fetchClusters() {
  try {
    console.log("🔄 Fetching clusters...");
    
    // Show loading state
    showState('loadingState');

    const response = await fetch("http://localhost:8001/coco/clustering");

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`❌ API Error ${response.status}: ${text}`);
    }

    const data = await response.json();
    console.log("📊 Clusters data received:", data);

    if (!data || data.length === 0) {
      showState('emptyState');
      return;
    }

    // Store data and create navigation
    allClustersData = data;
    createNavigation(data);
    updateGlobalStats(data);
    
    // Show first category by default
    if (data.length > 0) {
      showCategory(0);
    }

    // Show navigation and stats
    document.getElementById('navigationContainer').classList.remove('hidden');
    document.getElementById('statsSection').classList.remove('hidden');
    showState('categoryContent');

  } catch (error) {
    console.error("🚨 Failed to fetch clusters:", error);
    document.getElementById('errorMessage').textContent = error.message;
    showState('errorState');
  }
}

function showState(activeState) {
  const states = ['loadingState', 'categoryContent', 'errorState', 'emptyState'];
  states.forEach(state => {
    const element = document.getElementById(state);
    if (element) {
      if (state === activeState) {
        element.classList.remove('hidden');
      } else {
        element.classList.add('hidden');
      }
    }
  });
}

function createNavigation(data) {
  const tabsContainer = document.getElementById('categoryTabs');
  if (!tabsContainer) return;

  tabsContainer.innerHTML = '';

  data.forEach((categoryData, index) => {
    const categoryName = categoryData.category || `Category ${index + 1}`;
    const clusters = categoryData.clusters || [];
    const clusterCount = clusters.length;
    const imageCount = clusters.reduce((sum, cluster) => sum + (cluster.images ? cluster.images.length : 0), 0);

    const tab = document.createElement('div');
    tab.className = 'nav-tab';
    tab.setAttribute('data-category-index', index);
    tab.innerHTML = `
      <span class="text-lg">📂</span>
      <div class="flex flex-col items-center">
        <span class="font-medium">${categoryName}</span>
        <span class="count">${clusterCount} clusters</span>
      </div>
    `;

    tab.addEventListener('click', () => showCategory(index));
    tabsContainer.appendChild(tab);
  });
}

function showCategory(categoryIndex) {
  if (!allClustersData || !allClustersData[categoryIndex]) return;

  currentCategory = categoryIndex;
  const categoryData = allClustersData[categoryIndex];
  
  // Update active tab
  document.querySelectorAll('.nav-tab').forEach((tab, index) => {
    if (index === categoryIndex) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  // Update category stats
  updateCategoryStats(categoryData);
  
  // Display category content
  displayCategory(categoryData, categoryIndex);
}

function updateGlobalStats(data) {
  const totalCategories = data.length;
  animateNumber('totalCategories', totalCategories);
}

function updateCategoryStats(categoryData) {
  const clusters = categoryData.clusters || [];
  const clusterCount = clusters.length;
  const imageCount = clusters.reduce((sum, cluster) => sum + (cluster.images ? cluster.images.length : 0), 0);
  const avgPerCluster = clusterCount > 0 ? Math.round(imageCount / clusterCount) : 0;

  animateNumber('currentCategoryClusters', clusterCount);
  animateNumber('currentCategoryImages', imageCount);
  animateNumber('avgPerCluster', avgPerCluster);
}

function animateNumber(elementId, targetValue) {
  const element = document.getElementById(elementId);
  if (!element) return;

  let currentValue = 0;
  const increment = Math.ceil(targetValue / 20);
  const timer = setInterval(() => {
    currentValue += increment;
    if (currentValue >= targetValue) {
      element.textContent = targetValue;
      clearInterval(timer);
    } else {
      element.textContent = currentValue;
    }
  }, 50);
}

function displayCategory(categoryData, categoryIndex) {
  const container = document.getElementById("categoryContent");
  if (!container) return;

  const categoryName = categoryData.category || `Category ${categoryIndex + 1}`;
  const clusters = categoryData.clusters || [];

  console.log(`Displaying category: ${categoryName} with ${clusters.length} clusters`);

  // Create category container with animation
  container.innerHTML = '';
  const categoryDiv = document.createElement("div");
  categoryDiv.className = "category-content";

  if (clusters.length === 0) {
    categoryDiv.innerHTML = `
      <div class="empty-category">
        <div class="text-6xl mb-4">📦</div>
        <h3 class="text-2xl font-bold text-gray-700 mb-2">No Clusters in ${categoryName}</h3>
        <p class="text-gray-500">This category doesn't contain any clusters yet.</p>
      </div>
    `;
    container.appendChild(categoryDiv);
    return;
  }

  // Category header
  const headerDiv = document.createElement("div");
  headerDiv.className = "bg-white rounded-2xl p-8 shadow-lg border border-gray-200 mb-8";
  headerDiv.innerHTML = `
    <div class="flex items-center justify-between">
      <div class="flex items-center">
        <span class="text-5xl mr-4">📂</span>
        <div>
          <h2 class="text-3xl font-bold text-gray-800">${categoryName}</h2>
          <p class="text-gray-600 text-lg">${clusters.length} clusters ready to explore</p>
        </div>
      </div>
      <div class="text-right">
        <div class="bg-blue-100 text-blue-800 px-4 py-2 rounded-full font-semibold">
          ${clusters.reduce((sum, cluster) => sum + (cluster.images ? cluster.images.length : 0), 0)} images total
        </div>
      </div>
    </div>
  `;
  categoryDiv.appendChild(headerDiv);

  // Clusters grid
  const clustersGrid = document.createElement("div");
  clustersGrid.className = "space-y-8";

  clusters.forEach((cluster, clusterIndex) => {
    console.log(`Processing cluster ${clusterIndex}:`, cluster);

    const clusterDiv = document.createElement("div");
    clusterDiv.className = "cluster-card bg-white rounded-xl shadow-lg p-6 border border-gray-200";

    // Cluster name and info
    let clusterName = "Unknown Cluster";
    let clusterScore = "";

    if (cluster.name) {
      if (typeof cluster.name === 'string') {
        clusterName = cluster.name;
      } else if (cluster.name.name) {
        clusterName = cluster.name.name;
        if (cluster.name.score) {
          clusterScore = ` <span class="text-sm text-green-600 bg-green-100 px-2 py-1 rounded-full">${cluster.name.score}% match</span>`;
        }
      }
    } else if (cluster.title) {
      clusterName = cluster.title;
    } else {
      clusterName = `Cluster ${clusterIndex + 1}`;
    }

    // Cluster header
    const clusterHeader = document.createElement("div");
    clusterHeader.className = "flex items-center justify-between mb-6 pb-4 border-b border-gray-200";
    clusterHeader.innerHTML = `
      <div class="flex items-center">
        <span class="text-3xl mr-4">🧠</span>
        <div>
          <h3 class="text-xl font-bold text-gray-800">${clusterName}${clusterScore}</h3>
          <p class="text-gray-600" id="image-count-${clusterIndex}">${cluster.images ? cluster.images.length : 0} images in this cluster</p>
        </div>
      </div>
      <div class="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-full font-semibold text-sm" id="image-badge-${clusterIndex}">
        ${cluster.images ? cluster.images.length : 0} items
      </div>
    `;
    clusterDiv.appendChild(clusterHeader);

    // Check if images exist
    if (!cluster.images || cluster.images.length === 0) {
      const noImages = document.createElement("div");
      noImages.className = "text-center py-12";
      noImages.innerHTML = `
        <div class="text-4xl mb-2">📷</div>
        <p class="text-gray-500">No images in this cluster</p>
      `;
      clusterDiv.appendChild(noImages);
      clustersGrid.appendChild(clusterDiv);
      return;
    }

    // Image gallery
    const gallery = document.createElement("div");
    gallery.className = "image-grid";

    let validImageCount = 0; // ספירת תמונות תקינות
    let processedImages = 0; // ספירת תמונות שעובדו
    const totalImages = cluster.images ? cluster.images.length : 0;

    // פונקציה לעדכון המונים
    function updateCounters() {
      const imageCountElement = document.getElementById(`image-count-${clusterIndex}`);
      const imageBadgeElement = document.getElementById(`image-badge-${clusterIndex}`);

      if (imageCountElement) {
        imageCountElement.textContent = `${validImageCount} valid images in this cluster`;
      }
      if (imageBadgeElement) {
        imageBadgeElement.textContent = `${validImageCount} items`;
      }
    }

    cluster.images.forEach((image, imageIndex) => {
      console.log(`Processing image ${imageIndex}:`, image);

      // בדיקה ראשונית - אם אין path, דלג על התמונה
      if (!image.path) {
        console.log(`⏭️ Skipping image without path`);
        return;
      }

      const imgWrapper = document.createElement("div");
      imgWrapper.className = "image-item";

      const img = document.createElement("img");
      img.alt = image.caption || `Cluster image ${imageIndex + 1}`;

      // Image loading logic
      if (image.path.startsWith("http")) {
        img.src = image.path;
        console.log(`🌐 Loading COCO image: ${image.path}`);
      } else {
        const normalizedPath = image.path.replace(/\\/g, '/');
        img.src = `file:///${normalizedPath}`;
        console.log(`💻 Loading local image: file:///${normalizedPath}`);
      }

      // Success handler - ספירה וטעינה מוצלחת
      img.onload = () => {
        console.log(`✅ Successfully loaded: ${image.path}`);
        validImageCount++;
        processedImages++;
        updateCounters();
      };

      // Error handler - הסתרה במקרה של כשלון
      img.onerror = () => {
        console.log(`❌ Failed to load image: ${img.src} - hiding element`);
        imgWrapper.style.display = "none";
        processedImages++;

        // אם כל התמונות עובדו, עדכן את המונים
        if (processedImages === totalImages) {
          updateCounters();
        }
      };

      // Image caption
      const caption = document.createElement("div");
      caption.className = "image-caption";
      caption.innerHTML = `
        <p class="font-medium">${image.caption || 'No caption available'}</p>
        <p class="text-gray-300 text-xs mt-1">Path: ${image.path || 'Unknown'}</p>
      `;

      imgWrapper.appendChild(img);
      imgWrapper.appendChild(caption);
      gallery.appendChild(imgWrapper);
    });

    clusterDiv.appendChild(gallery);
    clustersGrid.appendChild(clusterDiv);
  });

  categoryDiv.appendChild(clustersGrid);
  container.appendChild(categoryDiv);
}

// יצירת placeholder image
function createPlaceholderImage(text = "No Image", details = "") {
  try {
    const cleanText = String(text || "Error").replace(/[^\x00-\x7F]/g, "?");
    const cleanDetails = String(details || "").replace(/[^\x00-\x7F]/g, "?").substring(0, 30);

    const svg = `<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="#f3f4f6"/>
      <text x="50%" y="40%" font-family="Inter, Arial, sans-serif" font-size="14" fill="#6b7280" text-anchor="middle">
        ${cleanText}
      </text>
      <text x="50%" y="60%" font-family="Inter, Arial, sans-serif" font-size="10" fill="#9ca3af" text-anchor="middle">
        ${cleanDetails}
      </text>
      <circle cx="100" cy="75" r="20" fill="#e5e7eb"/>
      <text x="100" y="80" font-family="Arial" font-size="16" fill="#9ca3af" text-anchor="middle">📷</text>
    </svg>`;

    return `data:image/svg+xml;base64,${btoa(svg)}`;
  } catch (error) {
    console.error("Placeholder error:", error);
    return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='150'%3E%3Crect width='100%25' height='100%25' fill='%23f3f4f6'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle'%3EError%3C/text%3E%3C/svg%3E";
  }
}

// Keyboard navigation
document.addEventListener('keydown', (e) => {
  if (!allClustersData || allClustersData.length === 0) return;

  // Arrow keys for navigation
  if (e.key === 'ArrowLeft' && currentCategory > 0) {
    showCategory(currentCategory - 1);
  } else if (e.key === 'ArrowRight' && currentCategory < allClustersData.length - 1) {
    showCategory(currentCategory + 1);
  }
  
  // Number keys for direct navigation
  const numKey = parseInt(e.key);
  if (numKey >= 1 && numKey <= allClustersData.length) {
    showCategory(numKey - 1);
  }
});