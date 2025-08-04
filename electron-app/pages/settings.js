const { ipcRenderer } = require("electron");
const fs = require("fs");
const path = require("path");

console.log("🚀 Settings System Loading...");

window.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOM טעון, מתחיל אתחול הגדרות");

    const folderInput = document.getElementById("folder-path");
    const statusDiv = document.getElementById("status");
    const selectButton = document.getElementById("select-folder");

    if (!folderInput || !statusDiv || !selectButton) {
        console.error("❌ לא נמצאו אלמנטים נדרשים ב-DOM!");
        return;
    }

    const configPath = path.join(__dirname, "config.json");
    console.log("📍 נתיב קובץ הגדרות:", configPath);

    function updateStatus(message, type = "info") {
        statusDiv.textContent = message;

        const colors = {
            success: "#22c55e",
            error: "#ef4444",
            warning: "#f59e0b",
            info: "#3b82f6",
            loading: "#8b5cf6"
        };

        statusDiv.style.color = colors[type] || colors.info;
        console.log(`📢 ${type.toUpperCase()}: ${message}`);
    }

    function loadExistingSettings() {
        try {
            if (fs.existsSync(configPath)) {
                const configData = fs.readFileSync(configPath, "utf8");
                const config = JSON.parse(configData);

                console.log("📂 הגדרות נטענו:", config);

                if (config.user_images_path && config.user_images_path.trim() !== "") {
                    folderInput.value = config.user_images_path;

                    if (fs.existsSync(config.user_images_path)) {
                        updateStatus("✅ תיקייה נטענה מההגדרות", "success");

                        // בדיקה אם כבר הוגדרה סריקה אוטומטית
                        if (config.auto_scan_enabled) {
                            showAutoScanStatus(true);
                        } else if (!config.auto_scan_skipped) {
                            // אם לא הוגדרה ולא נדחתה, הצג אפשרות
                            setTimeout(() => {
                                showAutoScanOption();
                            }, 2000);
                        }
                    } else {
                        updateStatus("⚠️ תיקייה שמורה לא קיימת יותר", "warning");
                    }
                } else {
                    updateStatus("📝 לא הוגדרה תיקייה עדיין", "info");
                }
            } else {
                console.log("📝 אין קובץ הגדרות קיים");
                updateStatus("📝 לא הוגדרה תיקייה עדיין", "info");
            }
        } catch (error) {
            console.error("❌ שגיאה בטעינת הגדרות:", error);
            updateStatus("❌ שגיאה בטעינת הגדרות", "error");
        }
    }

    function saveSettings(folderPath) {
        try {
            const existingConfig = getLocalConfig() || {};

            const config = {
                ...existingConfig,
                user_images_path: folderPath,
                coco_mode: "remote",
                coco_local_path: "D:/coco/val2017",
                last_updated: new Date().toISOString()
            };

            fs.writeFileSync(configPath, JSON.stringify(config, null, 2), "utf8");
            console.log("💾 הגדרות נשמרו באלקטרון");
            return true;
        } catch (error) {
            console.error("❌ שגיאה בשמירת הגדרות באלקטרון:", error);
            updateStatus("❌ שגיאה בשמירת הגדרות", "error");
            return false;
        }
    }

    async function syncWithServer(folderPath) {
        try {
            console.log("📡 שולח לשרת Python...");
            updateStatus("📡 מסנכרן עם השרת...", "loading");

            const response = await fetch("http://127.0.0.1:8001/set_user_folder", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({ path: folderPath })
            });

            console.log("📡 תגובה מהשרת:", response.status, response.statusText);

            if (response.ok) {
                const result = await response.json();
                console.log("📡 תוכן התגובה:", result);

                if (result.success === true) {
                    console.log("✅ שרת אישר שמירה בהצלחה");

                    let message = "✅ נשמר בהצלחה באפליקציה ובשרת!";
                    if (result.image_count >= 0) {
                        message += ` (נמצאו ${result.image_count} תמונות)`;
                    }

                    return {
                        success: true,
                        message: message,
                        imageCount: result.image_count
                    };
                } else {
                    console.log("❌ שרת החזיר success: false:", result.error || result.message);
                    return {
                        success: false,
                        message: `שגיאה בשרת: ${result.error || result.message || 'לא ידוע'}`
                    };
                }
            } else {
                console.log("❌ שרת החזיר קוד שגיאה:", response.status);
                const errorText = await response.text().catch(() => "לא ניתן לקרוא שגיאה");
                return {
                    success: false,
                    message: `שרת החזיר שגיאה ${response.status}: ${errorText}`
                };
            }
        } catch (error) {
            console.log("❌ אין חיבור לשרת:", error.message);
            return {
                success: false,
                message: "אין חיבור לשרת Python"
            };
        }
    }

    selectButton.addEventListener("click", async () => {
        try {
            console.log("🎯 לחיצה על בחירת תיקייה");
            updateStatus("🔍 פותח חלון בחירת תיקייה...", "loading");

            selectButton.disabled = true;
            selectButton.textContent = "בוחר...";

            const selectedFolder = await ipcRenderer.invoke("select-folder");

            if (selectedFolder) {
                console.log("📁 תיקייה נבחרה:", selectedFolder);
                folderInput.value = selectedFolder;

                // שמירה מקומית
                const saveSuccess = saveSettings(selectedFolder);

                if (saveSuccess) {
                    updateStatus("📁 נשמר באלקטרון, מסנכרן עם השרת...", "loading");

                    // ניסיון סנכרון עם השרת
                    const serverResult = await syncWithServer(selectedFolder);

                    if (serverResult.success) {
                        updateStatus(serverResult.message, "success");

                        // בדיקה אם כבר הוגדרה סריקה אוטומטית
                        const config = getLocalConfig();
                        if (!config.auto_scan_enabled && !config.auto_scan_skipped) {
                            // הצגת אפשרות להגדרת סריקה אוטומטית
                            setTimeout(() => {
                                showAutoScanOption();
                            }, 2000);
                        }
                    } else {
                        updateStatus(`⚠️ נשמר באלקטרון, ${serverResult.message}`, "warning");
                    }
                } else {
                    updateStatus("❌ שגיאה בשמירה באלקטרון", "error");
                }

            } else {
                console.log("🚫 בחירת תיקייה בוטלה");
                updateStatus("🚫 בחירת תיקייה בוטלה", "info");
            }

        } catch (error) {
            console.error("❌ שגיאה בתהליך בחירת תיקייה:", error);
            updateStatus(`❌ שגיאה: ${error.message}`, "error");
        } finally {
            selectButton.disabled = false;
            selectButton.textContent = "Select Folder";
        }
    });

    // פונקציה להצגת אפשרות סריקה אוטומטית
    function showAutoScanOption() {
        // בדיקה אם כבר יש קונטיינר
        if (document.getElementById('auto-scan-container')) {
            return;
        }

        const autoScanContainer = document.createElement('div');
        autoScanContainer.id = 'auto-scan-container';
        autoScanContainer.style.cssText = `
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            border: 2px solid #2196F3;
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
            text-align: center;
            animation: slideDown 0.5s ease-out;
        `;

        autoScanContainer.innerHTML = `
            <h3 style="color: #1565c0; margin-bottom: 10px;">🕐 סריקה אוטומטית</h3>
            <p style="color: #1976d2; margin-bottom: 15px; line-height: 1.6;">
                האם תרצה שהמערכת תסרוק תמונות חדשות אוטומטית כל לילה ב-02:00?<br>
                <small>(מומלץ - כך החיפושים יהיו מהירים תמיד)</small>
            </p>
            <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                <button id="enable-auto-scan" class="auto-scan-btn" style="
                    background: linear-gradient(135deg, #4caf50, #45a049);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: transform 0.2s;
                    min-width: 150px;
                ">
                    ✅ כן, הפעל סריקה אוטומטית
                </button>
                <button id="skip-auto-scan" class="auto-scan-btn" style="
                    background: linear-gradient(135deg, #9e9e9e, #757575);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: transform 0.2s;
                    min-width: 120px;
                ">
                    ⏭️ לא עכשיו
                </button>
            </div>
        `;

        // הוספת אנימציה
        if (!document.getElementById('settings-animations')) {
            const style = document.createElement('style');
            style.id = 'settings-animations';
            style.textContent = `
                @keyframes slideDown {
                    from { opacity: 0; transform: translateY(-20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .auto-scan-btn:hover {
                    transform: translateY(-2px) scale(1.05);
                }
                .auto-scan-btn:active {
                    transform: translateY(0) scale(0.98);
                }
            `;
            document.head.appendChild(style);
        }

        document.querySelector('.settings-container').appendChild(autoScanContainer);

        // מאזינים לכפתורים
        document.getElementById('enable-auto-scan').addEventListener('click', setupAutoScan);
        document.getElementById('skip-auto-scan').addEventListener('click', skipAutoScan);
    }

    // הגדרת סריקה אוטומטית
    async function setupAutoScan() {
        try {
            updateStatus("🔧 מגדיר סריקה אוטומטית...", "loading");

            const result = await ipcRenderer.invoke('setup-auto-scan');

            if (result.success) {
                updateStatus("✅ סריקה אוטומטית הוגדרה לשעה 02:00!", "success");

                // שמירה בהגדרות
                const config = getLocalConfig() || {};
                config.auto_scan_enabled = true;
                config.auto_scan_setup_date = new Date().toISOString();
                config.auto_scan_task_name = result.taskName;
                saveLocalConfig(config);

                // הצגת סטטוס מתמשך
                showAutoScanStatus(true);

            } else {
                updateStatus(`⚠️ ${result.message}`, "warning");
                console.error("שגיאה בהגדרת סריקה:", result.error);
            }

        } catch (error) {
            console.error("❌ שגיאה בהגדרת סריקה אוטומטית:", error);
            updateStatus("❌ שגיאה בהגדרת סריקה אוטומטית", "error");
        } finally {
            // הסרת הקונטיינר
            const container = document.getElementById('auto-scan-container');
            if (container) {
                container.remove();
            }
        }
    }

    // דילוג על סריקה אוטומטית
    function skipAutoScan() {
        updateStatus("ℹ️ ניתן להגדיר סריקה אוטומטית מאוחר יותר", "info");

        // שמירה שהמשתמש בחר לדלג
        const config = getLocalConfig() || {};
        config.auto_scan_skipped = true;
        config.auto_scan_skip_date = new Date().toISOString();
        saveLocalConfig(config);

        // הסרת הקונטיינר
        const container = document.getElementById('auto-scan-container');
        if (container) {
            container.remove();
        }
    }

    // הצגת סטטוס סריקה אוטומטית
    function showAutoScanStatus(enabled) {
        // הסרת קונטיינר אפשרות אם קיים
        const optionContainer = document.getElementById('auto-scan-container');
        if (optionContainer) {
            optionContainer.remove();
        }

        // בדיקה אם כבר יש סטטוס
        if (document.getElementById('auto-scan-status')) {
            return;
        }

        const statusContainer = document.createElement('div');
        statusContainer.id = 'auto-scan-status';
        statusContainer.style.cssText = `
            background: ${enabled ? 
                'linear-gradient(135deg, #d4edda, #c3e6cb)' : 
                'linear-gradient(135deg, #f8d7da, #f5c6cb)'};
            border: 2px solid ${enabled ? '#c3e6cb' : '#f5c6cb'};
            border-radius: 15px;
            padding: 15px;
            margin-top: 20px;
            text-align: center;
        `;

        const config = getLocalConfig() || {};
        const setupDate = config.auto_scan_setup_date ?
            new Date(config.auto_scan_setup_date).toLocaleDateString('he-IL') : 'לא ידוע';

        statusContainer.innerHTML = `
            <h4 style="color: ${enabled ? '#155724' : '#721c24'}; margin-bottom: 10px;">
                ${enabled ? '✅ סריקה אוטומטית פעילה' : '❌ סריקה אוטומטית לא פעילה'}
            </h4>
            <p style="color: ${enabled ? '#155724' : '#721c24'}; margin-bottom: 15px; font-size: 14px;">
                ${enabled ? 
                    `המערכת תסרוק תמונות חדשות כל יום ב-02:00<br>הוגדרה ב: ${setupDate}` :
                    'לא הוגדרה סריקה אוטומטית'
                }
            </p>
            <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                ${enabled ? `
                    <button id="disable-auto-scan" style="
                        background: linear-gradient(135deg, #dc3545, #c82333);
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 20px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: transform 0.2s;
                    ">
                        🔴 השבת סריקה אוטומטית
                    </button>
                ` : `
                    <button id="enable-auto-scan-later" style="
                        background: linear-gradient(135deg, #28a745, #20c997);
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 20px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: transform 0.2s;
                    ">
                        🟢 הפעל סריקה אוטומטית
                    </button>
                `}
            </div>
        `;

        document.querySelector('.settings-container').appendChild(statusContainer);

        // מאזינים לכפתורים
        if (enabled) {
            document.getElementById('disable-auto-scan')?.addEventListener('click', disableAutoScan);
        } else {
            document.getElementById('enable-auto-scan-later')?.addEventListener('click', () => {
                statusContainer.remove();
                showAutoScanOption();
            });
        }
    }

    // השבתת סריקה אוטומטית
    async function disableAutoScan() {
        try {
            updateStatus("🔧 משבית סריקה אוטומטית...", "loading");

            const result = await ipcRenderer.invoke('remove-auto-scan');

            if (result.success) {
                updateStatus("✅ סריקה אוטומטית הושבתה", "success");

                // עדכון הגדרות
                const config = getLocalConfig() || {};
                config.auto_scan_enabled = false;
                config.auto_scan_disabled_date = new Date().toISOString();
                delete config.auto_scan_task_name;
                saveLocalConfig(config);

                // עדכון תצוגה
                const statusContainer = document.getElementById('auto-scan-status');
                if (statusContainer) {
                    statusContainer.remove();
                }
                showAutoScanStatus(false);

            } else {
                updateStatus(`⚠️ ${result.message}`, "warning");
            }

        } catch (error) {
            console.error("❌ שגיאה בהשבתת סריקה:", error);
            updateStatus("❌ שגיאה בהשבתת סריקה אוטומטית", "error");
        }
    }

    // פונקציות עזר לניהול קובץ config
    function getLocalConfig() {
        try {
            if (fs.existsSync(configPath)) {
                const configData = fs.readFileSync(configPath, "utf8");
                return JSON.parse(configData);
            }
        } catch (error) {
            console.error("שגיאה בקריאת config:", error);
        }
        return {};
    }

    function saveLocalConfig(config) {
        try {
            fs.writeFileSync(configPath, JSON.stringify(config, null, 2), "utf8");
            console.log("💾 config נשמר:", config);
        } catch (error) {
            console.error("שגיאה בשמירת config:", error);
        }
    }

    // טעינת הגדרות קיימות
    loadExistingSettings();

    console.log("🎉 מערכת ההגדרות מוכנה לשימוש!");
});