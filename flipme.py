"""
flipme.py - Main entry point for FlipMe App
Floating 3D Realistic Alive Alien Blob application for flipping display horizontally & vertically.
Left Click on Blob: Flips display horizontally.
Right Click on Blob: Flips display vertically.
Double Click / Tray Menu / Hotkey: Resets display to normal (0 deg).
"""

import sys
import os
import io
import time
import traceback
import winsound

# Logging utility to capture any frozen EXE errors
LOG_FILE = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "flipme_debug.log")

def log_msg(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

log_msg("=== Starting FlipMe ===")

from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox, QShortcut
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QRadialGradient, QKeySequence, QSurfaceFormat

# Ensure Native Desktop OpenGL is bound for PyInstaller frozen executables
try:
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)
    log_msg("Desktop OpenGL & SurfaceFormat set")
except Exception as err:
    log_msg(f"OpenGL Setup Warning: {err}")

try:
    from display_manager import DisplayManager, DMDO_DEFAULT, DMDO_90, DMDO_180, DMDO_270
    from blob_widget import AlienBlobWidget
    log_msg("Imports completed successfully")
except Exception as e:
    log_msg(f"Import error: {e}\n{traceback.format_exc()}")

# Force stdout/stderr to UTF-8 or dummy writer
class DummyWriter:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass

if sys.stdout is None:
    sys.stdout = DummyWriter()
if sys.stderr is None:
    sys.stderr = DummyWriter()


def create_alien_icon():
    """Generates a procedural glowing 3D alien icon for the system tray."""
    try:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Glowing outer bioluminescence
        radial = QRadialGradient(32, 32, 28)
        radial.setColorAt(0.0, QColor(0, 255, 200, 255))
        radial.setColorAt(0.5, QColor(140, 0, 255, 220))
        radial.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(radial)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)

        # Alien Eye
        painter.setBrush(QColor(10, 10, 20))
        painter.drawEllipse(22, 20, 20, 20)
        painter.setBrush(QColor(0, 255, 230))
        painter.drawEllipse(27, 25, 10, 10)

        painter.end()
        return QIcon(pixmap)
    except Exception as e:
        log_msg(f"Icon error: {e}")
        return QIcon()


class FlipMeApp:
    def __init__(self):
        log_msg("Initializing QApplication...")
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)

        self.app.setApplicationName("FlipMe")
        self.app.setQuitOnLastWindowClosed(False)

        log_msg("Initializing DisplayManager...")
        self.display_mgr = DisplayManager()

        log_msg("Initializing AlienBlobWidget...")
        self.blob_widget = AlienBlobWidget(display_manager=self.display_mgr)

        # Connect signals
        self.blob_widget.left_clicked.connect(self.on_left_click)
        self.blob_widget.right_clicked.connect(self.on_right_click)
        self.blob_widget.double_clicked.connect(self.on_double_click)

        # Safety auto-revert timer (10 seconds)
        self.auto_revert_enabled = False
        self.auto_revert_timer = QTimer()
        self.auto_revert_timer.setSingleShot(True)
        self.auto_revert_timer.timeout.connect(self.reset_display)

        # Sound effect toggle
        self.sound_enabled = True

        # System Tray setup
        log_msg("Setting up System Tray Icon...")
        self.tray_icon = QSystemTrayIcon(create_alien_icon(), self.app)
        self.tray_icon.setToolTip("FlipMe - 3D Alien Blob Display Flipper\nLeft Click Blob: Horizontal Flip\nRight Click Blob: Vertical Flip")

        self.tray_menu = QMenu()
        self.setup_tray_menu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Global Application-scoped Keyboard Shortcut: Ctrl+Shift+R to Reset Display
        self.reset_shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self.blob_widget, context=Qt.ApplicationShortcut)
        self.reset_shortcut.activated.connect(self.reset_display)

        # Position widget near top-right of screen initially
        log_msg("Positioning widget on screen...")
        self.clamp_widget_to_screen()
        self.blob_widget.show()
        log_msg("FlipMeApp initialization complete.")

    def clamp_widget_to_screen(self):
        try:
            screen = QApplication.primaryScreen()
            if screen:
                screen_geo = screen.availableGeometry()
                x = max(screen_geo.left() + 20, min(self.blob_widget.x(), screen_geo.right() - self.blob_widget.width() - 20))
                y = max(screen_geo.top() + 20, min(self.blob_widget.y(), screen_geo.bottom() - self.blob_widget.height() - 20))
                if self.blob_widget.x() == 0 and self.blob_widget.y() == 0:
                    x = screen_geo.right() - 360
                    y = screen_geo.top() + 80
                self.blob_widget.move(x, y)
        except Exception as e:
            log_msg(f"Clamp error: {e}")

    def setup_tray_menu(self):
        title_action = QAction("👽 FlipMe 3D Alien Blob", self.tray_menu)
        title_action.setEnabled(False)
        self.tray_menu.addAction(title_action)
        self.tray_menu.addSeparator()

        flip_h_action = QAction("↔ Flip Horizontally (Left Click)", self.tray_menu)
        flip_h_action.triggered.connect(self.on_left_click)
        self.tray_menu.addAction(flip_h_action)

        flip_v_action = QAction("↕ Flip Vertically (Right Click)", self.tray_menu)
        flip_v_action.triggered.connect(self.on_right_click)
        self.tray_menu.addAction(flip_v_action)

        reset_action = QAction("🔄 Reset Display (0°) [Ctrl+Shift+R]", self.tray_menu)
        reset_action.triggered.connect(self.reset_display)
        self.tray_menu.addAction(reset_action)

        self.tray_menu.addSeparator()

        self.revert_action = QAction("⏱ Auto-Revert Flips (10s Safety)", self.tray_menu)
        self.revert_action.setCheckable(True)
        self.revert_action.setChecked(self.auto_revert_enabled)
        self.revert_action.triggered.connect(self.toggle_auto_revert)
        self.tray_menu.addAction(self.revert_action)

        self.sound_action = QAction("🔊 Audio Feedback", self.tray_menu)
        self.sound_action.setCheckable(True)
        self.sound_action.setChecked(self.sound_enabled)
        self.sound_action.triggered.connect(self.toggle_sound)
        self.tray_menu.addAction(self.sound_action)

        self.ontop_action = QAction("📌 Always On Top", self.tray_menu)
        self.ontop_action.setCheckable(True)
        self.ontop_action.setChecked(True)
        self.ontop_action.triggered.connect(self.toggle_always_on_top)
        self.tray_menu.addAction(self.ontop_action)

        self.tray_menu.addSeparator()

        exit_action = QAction("❌ Exit FlipMe", self.tray_menu)
        exit_action.triggered.connect(self.exit_app)
        self.tray_menu.addAction(exit_action)

    def play_flip_sound(self, freq=800):
        if self.sound_enabled:
            try:
                winsound.Beep(freq, 80)
            except Exception:
                pass

    def on_left_click(self):
        """Flip Display Horizontally."""
        self.play_flip_sound(750)
        success = self.display_mgr.flip_horizontal()
        self.clamp_widget_to_screen()
        if success and self.auto_revert_enabled:
            self.start_auto_revert_timer()

    def on_right_click(self):
        """Flip Display Vertically."""
        self.play_flip_sound(950)
        success = self.display_mgr.flip_vertical()
        self.clamp_widget_to_screen()
        if success and self.auto_revert_enabled:
            self.start_auto_revert_timer()

    def on_double_click(self):
        """Reset display to normal."""
        self.reset_display()

    def reset_display(self):
        self.auto_revert_timer.stop()
        self.play_flip_sound(1200)
        self.display_mgr.reset_display()
        self.clamp_widget_to_screen()
        self.tray_icon.showMessage("FlipMe", "Display reset to normal orientation (0°).", QSystemTrayIcon.Information, 1500)

    def toggle_auto_revert(self, checked):
        self.auto_revert_enabled = checked

    def toggle_sound(self, checked):
        self.sound_enabled = checked

    def start_auto_revert_timer(self):
        self.auto_revert_timer.start(10000) # 10 seconds
        self.tray_icon.showMessage("FlipMe Safety Timer", "Display will auto-revert to 0° in 10 seconds.", QSystemTrayIcon.Warning, 3000)

    def toggle_always_on_top(self, checked):
        flags = self.blob_widget.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.blob_widget.setWindowFlags(flags)
        self.blob_widget.show()

    def exit_app(self):
        self.display_mgr.reset_display()
        self.app.quit()

    def run(self):
        log_msg("Starting Qt main event loop...")
        res = self.app.exec_()
        log_msg(f"Qt main loop finished with code {res}")
        return res


if __name__ == "__main__":
    try:
        app_instance = FlipMeApp()
        sys.exit(app_instance.run())
    except Exception as exc:
        log_msg(f"CRITICAL MAIN EXCEPTION: {exc}\n{traceback.format_exc()}")
        try:
            QMessageBox.critical(None, "FlipMe Error", f"Fatal Error starting FlipMe:\n{exc}\nCheck flipme_debug.log")
        except Exception:
            pass
