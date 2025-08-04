const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage } = require("electron");
const path = require("path");

let mainWindow;
let tray;

function createWindow() {
    if (mainWindow) return;

    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        icon: path.join(__dirname, "icon.png"),
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
    });

    // טוען את index.html מתוך תיקיית pages
    mainWindow.loadFile(path.join(__dirname, "pages", "index.html"));

    mainWindow.on("closed", function () {
        mainWindow = null;
    });
}

app.whenReady().then(() => {
    createWindow();

    const iconPath = path.join(__dirname, "icon.png");
    const trayIcon = nativeImage.createFromPath(iconPath);
    tray = new Tray(trayIcon);

    const contextMenu = Menu.buildFromTemplate([
        {
            label: "Open App",
            click: () => {
                if (!mainWindow) {
                    createWindow();
                } else {
                    if (mainWindow.isMinimized()) mainWindow.restore();
                    mainWindow.show();
                }
            },
        },
        {
            label: "Exit",
            click: () => {
                app.quit();
            },
        },
    ]);

    tray.setToolTip("ImaginFind");
    tray.setContextMenu(contextMenu);
});

app.on("window-all-closed", function () {
    if (process.platform !== "darwin") {
        app.quit();
    }
});

app.on("activate", function () {
    if (mainWindow === null) {
        createWindow();
    }
});
