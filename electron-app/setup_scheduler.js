const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const { app } = require('electron');

class TaskSchedulerSetup {
    constructor() {
        this.taskName = `ImageScan_${app.getName()}_${Date.now()}`;
        this.scriptPath = path.join(__dirname, 'daily_scan.py');
        this.pythonPath = 'python';
    }

    /**
     * מוצא את נתיב Python המתאים
     */
    async findPythonPath() {
        return new Promise((resolve) => {
            // בדיקת python רגיל
            exec('python --version', (error) => {
                if (!error) {
                    resolve('python');
                    return;
                }

                // בדיקת python3
                exec('python3 --version', (error) => {
                    if (!error) {
                        resolve('python3');
                        return;
                    }

                    // בדיקת נתיבים נפוצים
                    const commonPaths = [
                        'C:\\Python39\\python.exe',
                        'C:\\Python38\\python.exe',
                        'C:\\Python37\\python.exe',
                        'C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python39\\python.exe'
                    ];

                    for (const pythonPath of commonPaths) {
                        if (fs.existsSync(pythonPath.replace('%USERNAME%', process.env.USERNAME || ''))) {
                            resolve(pythonPath);
                            return;
                        }
                    }

                    // אם לא נמצא כלום
                    resolve('python');
                });
            });
        });
    }

    /**
     * יצירת קובץ batch להפעלת הסקריפט
     */
    createBatchFile() {
        const batchPath = path.join(__dirname, 'run_daily_scan.bat');
        const batchContent = `@echo off
cd /d "${__dirname}"
"${this.pythonPath}" "${this.scriptPath}" > daily_scan_output.log 2>&1
`;

        try {
            fs.writeFileSync(batchPath, batchContent, 'utf8');
            console.log('✅ קובץ batch נוצר:', batchPath);
            return batchPath;
        } catch (error) {
            console.error('❌ שגיאה ביצירת קובץ batch:', error);
            throw error;
        }
    }

    /**
     * יצירת XML להגדרת המשימה
     */
    createTaskXML(batchPath) {
        const xml = `<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>${new Date().toISOString()}</Date>
    <Author>${process.env.USERNAME || 'ImageScan'}</Author>
    <Description>Daily image scanning for ImageSearch application</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-01T02:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>${process.env.USERNAME || 'SYSTEM'}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <DisallowStartOnRemoteAppSession>false</DisallowStartOnRemoteAppSession>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT4H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"${batchPath}"</Command>
      <WorkingDirectory>"${__dirname}"</WorkingDirectory>
    </Exec>
  </Actions>
</Task>`;

        const xmlPath = path.join(__dirname, 'task_definition.xml');
        try {
            fs.writeFileSync(xmlPath, xml, 'utf16le');
            console.log('✅ קובץ XML נוצר:', xmlPath);
            return xmlPath;
        } catch (error) {
            console.error('❌ שגיאה ביצירת XML:', error);
            throw error;
        }
    }

    /**
     * יצירת המשימה ב-Task Scheduler
     */
    async createTask(xmlPath) {
        return new Promise((resolve, reject) => {
            const command = `schtasks /create /tn "${this.taskName}" /xml "${xmlPath}" /f`;

            console.log('🔧 מגדיר משימה יומית:', command);

            exec(command, (error, stdout, stderr) => {
                if (error) {
                    console.error('❌ שגיאה ביצירת משימה:', error);
                    console.error('stderr:', stderr);
                    reject(error);
                } else {
                    console.log('✅ משימה נוצרה בהצלחה:', stdout);
                    resolve(stdout);
                }
            });
        });
    }

    /**
     * בדיקה אם המשימה קיימת
     */
    async taskExists() {
        return new Promise((resolve) => {
            exec(`schtasks /query /tn "${this.taskName}"`, (error) => {
                resolve(!error);
            });
        });
    }

    /**
     * מחיקת משימה קיימת
     */
    async deleteExistingTask() {
        return new Promise((resolve, reject) => {
            exec(`schtasks /delete /tn "${this.taskName}" /f`, (error, stdout) => {
                if (error) {
                    reject(error);
                } else {
                    console.log('🗑️ משימה קיימת נמחקה:', stdout);
                    resolve();
                }
            });
        });
    }

    /**
     * שמירת מידע על המשימה שנוצרה
     */
    saveTaskInfo() {
        const taskInfo = {
            taskName: this.taskName,
            created: new Date().toISOString(),
            scriptPath: this.scriptPath,
            pythonPath: this.pythonPath,
            status: 'active'
        };

        const configPath = path.join(__dirname, 'scheduler_config.json');

        try {
            fs.writeFileSync(configPath, JSON.stringify(taskInfo, null, 2), 'utf8');
            console.log('💾 מידע משימה נשמר:', configPath);
        } catch (error) {
            console.error('⚠️ לא ניתן לשמור מידע משימה:', error);
        }
    }

    /**
     * הפונקציה הראשית להגדרת המשימה
     */
    async setupDailyTask() {
        try {
            console.log('🚀 מתחיל הגדרת משימה יומית...');

            // מציאת Python
            this.pythonPath = await this.findPythonPath();
            console.log('🐍 נתיב Python:', this.pythonPath);

            // יצירת קובץ batch
            const batchPath = this.createBatchFile();

            // יצירת XML
            const xmlPath = this.createTaskXML(batchPath);

            // בדיקה ומחיקה של משימה קיימת
            if (await this.taskExists()) {
                await this.deleteExistingTask();
            }

            // יצירת המשימה החדשה
            await this.createTask(xmlPath);

            // שמירת מידע
            this.saveTaskInfo();

            // ניקוי קבצים זמניים
            try {
                fs.unlinkSync(xmlPath);
                console.log('🧹 קובץ XML זמני נמחק');
            } catch (error) {
                console.warn('⚠️ לא ניתן למחוק XML זמני:', error.message);
            }

            return {
                success: true,
                taskName: this.taskName,
                message: 'משימה יומית הוגדרה בהצלחה לשעה 02:15'
            };

        } catch (error) {
            console.error('❌ שגיאה בהגדרת משימה יומית:', error);
            return {
                success: false,
                error: error.message,
                message: 'לא ניתן להגדיר משימה יומית. העדכון יתבצע רק בפתיחת האפליקציה.'
            };
        }
    }

    /**
     * הסרת המשימה היומית
     */
    async removeDailyTask() {
        try {
            const configPath = path.join(__dirname, 'scheduler_config.json');

            // קריאת מידע המשימה
            if (fs.existsSync(configPath)) {
                const taskInfo = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                this.taskName = taskInfo.taskName;
            }

            // מחיקת המשימה
            await this.deleteExistingTask();

            // מחיקת קובץ התצורה
            if (fs.existsSync(configPath)) {
                fs.unlinkSync(configPath);
            }

            // מחיקת קובץ batch
            const batchPath = path.join(__dirname, 'run_daily_scan.bat');
            if (fs.existsSync(batchPath)) {
                fs.unlinkSync(batchPath);
            }

            return {
                success: true,
                message: 'משימה יומית הוסרה בהצלחה'
            };

        } catch (error) {
            console.error('❌ שגיאה בהסרת משימה:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// יצוא לשימוש
async function setupAutomaticScan() {
    const scheduler = new TaskSchedulerSetup();
    return await scheduler.setupDailyTask();
}

async function removeAutomaticScan() {
    const scheduler = new TaskSchedulerSetup();
    return await scheduler.removeDailyTask();
}

module.exports = {
    TaskSchedulerSetup,
    setupAutomaticScan,
    removeAutomaticScan
};