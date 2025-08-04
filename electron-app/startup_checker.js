const fs = require('fs');
const path = require('path');

class StartupChecker {
    constructor() {
        this.configPath = path.join(__dirname, 'pages', 'config.json');
        this.logPath = path.join(__dirname, 'daily_scan.log');
        this.schedulerConfigPath = path.join(__dirname, 'scheduler_config.json');
    }

    /**
     * בדיקה מהירה אם יש תמונות חדשות
     */
    async checkForNewImages() {
        try {
            console.log("🔍 בודק תמונות חדשות בהפעלה...");

            const response = await fetch('http://127.0.0.1:8001/daily_check', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                console.log("⚠️ שרת לא זמין - דולג על בדיקה");
                return null;
            }

            const result = await response.json();
            console.log("📊 תוצאת בדיקה:", result);

            return result;

        } catch (error) {
            console.log("⚠️ לא ניתן לבדוק תמונות חדשות:", error.message);
            return null;
        }
    }

    /**
     * קריאת לוג הסריקה האחרונה
     */
    getLastScanLog() {
        try {
            if (!fs.existsSync(this.logPath)) {
                return "לא בוצעה סריקה עדיין";
            }

            const logContent = fs.readFileSync(this.logPath, 'utf8');
            const lines = logContent.trim().split('\n');

            // חיפוש השורה האחרונה עם תוצאות
            for (let i = lines.length - 1; i >= 0; i--) {
                const line = lines[i];
                if (line.includes('עובדו:') || line.includes('אין תמונות חדשות') ||
                    line.includes('הושלם') || line.includes('תמונות')) {
                    // ניקוי הלוג מתאריכים ומידע מיותר
                    const cleanLog = line.replace(/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3}\s+-\s+INFO\s+-\s+/, '');
                    return cleanLog;
                }
            }

            return "לא נמצאו תוצאות בלוג";

        } catch (error) {
            console.error("שגיאה בקריאת לוג:", error);
            return "שגיאה בקריאת לוג הסריקה";
        }
    }

    /**
     * בדיקת סטטוס הגדרת הסריקה האוטומטית
     */
    checkAutoScanStatus() {
        try {
            const config = this.getConfig();
            const schedulerExists = fs.existsSync(this.schedulerConfigPath);

            let schedulerInfo = null;
            if (schedulerExists) {
                try {
                    schedulerInfo = JSON.parse(fs.readFileSync(this.schedulerConfigPath, 'utf8'));
                } catch (e) {
                    console.warn("שגיאה בקריאת scheduler config:", e);
                }
            }

            return {
                enabled: config.auto_scan_enabled || schedulerExists,
                skipped: config.auto_scan_skipped || false,
                setupDate: config.auto_scan_setup_date || (schedulerInfo && schedulerInfo.created) || null,
                skipDate: config.auto_scan_skip_date || null,
                taskName: schedulerInfo && schedulerInfo.taskName || null
            };

        } catch (error) {
            console.error("שגיאה בבדיקת סטטוס אוטומטי:", error);
            return { enabled: false, skipped: false };
        }
    }

    /**
     * קריאת קובץ התצורה
     */
    getConfig() {
        try {
            if (fs.existsSync(this.configPath)) {
                const configData = fs.readFileSync(this.configPath, 'utf8');
                return JSON.parse(configData);
            }
        } catch (error) {
            console.error("שגיאה בקריאת config:", error);
        }
        return {};
    }

    /**
     * הצגת הודעת סטטוס בהפעלה
     */
    showStartupStatus(mainWindow) {
        try {
            const lastScanLog = this.getLastScanLog();
            const autoScanStatus = this.checkAutoScanStatus();

            let statusMessage = "";
            let autoScanEnabled = autoScanStatus.enabled;

            if (autoScanStatus.enabled) {
                statusMessage = `✅ סריקה אוטומטית פעילה (כל יום ב-02:00)\n📋 סריקה אחרונה: ${lastScanLog}`;
            } else if (autoScanStatus.skipped) {
                statusMessage = "ℹ️ סריקה אוטומטית לא הוגדרה\n💡 ניתן להגדיר בהגדרות";
            } else {
                statusMessage = "🔧 ניתן להגדיר סריקה אוטומטית בהגדרות\n💡 יעזור לשמור על חיפושים מהירים";
            }

            // שליחת הודעה לממשק
            mainWindow.webContents.send('startup-status', {
                message: statusMessage,
                autoScanEnabled: autoScanEnabled,
                lastScanLog: lastScanLog,
                taskName: autoScanStatus.taskName
            });

            console.log("📊 סטטוס הפעלה נשלח:", { autoScanEnabled, lastScanLog });

        } catch (error) {
            console.error("שגיאה בהצגת סטטוס הפעלה:", error);
        }
    }

    /**
     * בדיקה והפעלה של סריקה ידנית אם נדרש
     */
    async checkAndRunManualScan(mainWindow) {
        try {
            const autoScanStatus = this.checkAutoScanStatus();

            // אם אין סריקה אוטומטית, בדוק אם צריך סריקה ידנית
            if (!autoScanStatus.enabled) {
                const newImagesCheck = await this.checkForNewImages();

                if (newImagesCheck && newImagesCheck.has_new_images) {
                    console.log(`📸 נמצאו ${newImagesCheck.new_images_count} תמונות חדשות`);

                    // המתנה קצרה לפני שליחת הודעה (כדי שהממשק יטען)
                    setTimeout(() => {
                        mainWindow.webContents.send('new-images-found', {
                            count: newImagesCheck.new_images_count,
                            message: `נמצאו ${newImagesCheck.new_images_count} תמונות חדשות. האם לעבד עכשיו?`
                        });
                    }, 2000);
                } else {
                    console.log("📊 אין תמונות חדשות או שרת לא זמין");
                }
            } else {
                console.log("🤖 סריקה אוטומטית פעילה - לא נדרשת בדיקה ידנית");
            }

        } catch (error) {
            console.error("שגיאה בבדיקת סריקה ידנית:", error);
        }
    }

    /**
     * בדיקת תקינות הגדרות
     */
    validateSettings() {
        try {
            const config = this.getConfig();
            const issues = [];

            // בדיקת תיקיית משתמש
            if (!config.user_images_path) {
                issues.push("לא הוגדרה תיקיית תמונות");
            } else if (!fs.existsSync(config.user_images_path)) {
                issues.push("תיקיית התמונות לא קיימת יותר");
            }

            // בדיקת הגדרות סריקה
            const autoScanStatus = this.checkAutoScanStatus();
            if (autoScanStatus.enabled && autoScanStatus.taskName) {
                // ניתן להוסיף בדיקה של Task Scheduler כאן
            }

            return {
                valid: issues.length === 0,
                issues: issues
            };

        } catch (error) {
            console.error("שגיאה בבדיקת תקינות:", error);
            return {
                valid: false,
                issues: ["שגיאה בבדיקת הגדרות"]
            };
        }
    }

    /**
     * בדיקה מלאה בהפעלת האפליקציה
     */
    async performStartupCheck(mainWindow) {
        console.log("🚀 מבצע בדיקות הפעלה...");

        // המתנה קצרה לטעינת האפליקציה
        setTimeout(async () => {
            try {
                // בדיקת תקינות הגדרות
                const validation = this.validateSettings();
                if (!validation.valid) {
                    console.warn("⚠️ בעיות בהגדרות:", validation.issues);

                    mainWindow.webContents.send('settings-issues', {
                        issues: validation.issues
                    });
                }

                // הצגת סטטוס
                this.showStartupStatus(mainWindow);

                // בדיקת תמונות חדשות (רק אם אין סריקה אוטומטית)
                await this.checkAndRunManualScan(mainWindow);

                console.log("✅ בדיקות הפעלה הושלמו");

            } catch (error) {
                console.error("❌ שגיאה בבדיקות הפעלה:", error);
            }
        }, 3000); // 3 שניות המתנה
    }

    /**
     * בדיקת סטטוס Server Python
     */
    async checkServerStatus() {
        try {
            const response = await fetch('http://127.0.0.1:8001/health', {
                method: 'GET',
                timeout: 3000
            });

            return response.ok;

        } catch (error) {
            return false;
        }
    }
}

module.exports = { StartupChecker };