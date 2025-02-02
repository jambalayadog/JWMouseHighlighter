from PyQt5.QtCore import QTimer, QPoint, Qt, pyqtSlot, QMetaObject, Q_ARG, QObject, pyqtSignal, QEvent, QThread, QSettings
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSystemTrayIcon, QMenu, QAction, QLabel, QVBoxLayout, QSlider, QColorDialog,
    QFormLayout, QDialog, QPushButton, QDoubleSpinBox, QSpinBox, QGroupBox, QGridLayout, QCheckBox
)
from PyQt5.QtGui import QPainter, QColor, QIcon
import pyautogui
import sys
import os
import winreg
import time
from pynput import mouse  # Import pynput for global mouse click detection

def add_to_startup():
    """Add the application to Windows startup."""
    # Path to the executable
    exe_path = os.path.abspath(sys.argv[0])  # Gets the path of the current executable

    # Registry key for current user startup programs
    key = winreg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        # Open the registry key
        registry_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE)
        # Set the value for the startup entry
        winreg.SetValueEx(registry_key, "JW Mouse Highlighter", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(registry_key)
        print("Added to startup.")
    except Exception as e:
        print(f"Failed to add to startup: {e}")

def remove_from_startup():
    """Remove the application from Windows startup."""
    # Registry key for current user startup programs
    key = winreg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        # Open the registry key
        registry_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE)
        # Delete the value for the startup entry
        winreg.DeleteValue(registry_key, "JW Mouse Highlighter")
        winreg.CloseKey(registry_key)
        print("Removed from startup.")
    except Exception as e:
        print(f"Failed to remove from startup: {e}")


def is_in_startup():
    """Check if the application is in Windows startup."""
    # Path to the executable
    exe_path = os.path.abspath(sys.argv[0])

    # Registry key for current user startup programs
    key = winreg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        # Open the registry key
        registry_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_READ)
        # Get the value for the startup entry
        value, _ = winreg.QueryValueEx(registry_key, "JW Mouse Highlighter")
        winreg.CloseKey(registry_key)
        return value == exe_path
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error checking startup status: {e}")
        return False

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ClickCircle(QMainWindow):
    def __init__(self, radius=5, color=QColor(170, 255, 255, 175)):
        super().__init__()
        self.radius = radius
        self.color = color

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput |
            Qt.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Allow clicks to pass through
        self.hide()

    def show_circle(self, x, y):
        self.move(x - self.radius, y - self.radius)
        self.resize(self.radius * 2, self.radius * 2)
        self.show()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.radius * 2, self.radius * 2)

class MouseHighlighter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.radius = 75
        self.color = QColor(255, 255, 0, 50)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput |
            Qt.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.resize(self.radius * 2, self.radius * 2)

    def update_position(self, x, y):
        self.move(x - self.radius, y - self.radius)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.radius * 2, self.radius * 2)

class MouseTracker(QThread):
    position_update = pyqtSignal(int, int)

    def run(self):
        while True:
            x, y = pyautogui.position()
            self.position_update.emit(x, y)
            time.sleep(0.01)  # Update every 10ms

class PynputListener(QThread):
    click_detected = pyqtSignal(int, int)  # Signal to emit click coordinates

    def run(self):
        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                self.click_detected.emit(x, y)

        # Start the pynput listener
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

class ClickManager(QObject):
    def __init__(self, max_circles=2, click_duration=0.8):
        super().__init__()
        self.click_circles = []
        self.max_circles = max_circles
        self.click_duration = click_duration
        self.click_radius = 5
        self.click_color = QColor(170, 255, 255, 175)

    def add_click(self, x, y):
        if len(self.click_circles) >= self.max_circles:
            oldest_circle = self.click_circles.pop(0)
            oldest_circle.hide()
            oldest_circle.deleteLater()

        circle = ClickCircle(radius=self.click_radius, color=self.click_color)
        circle.show_circle(x, y)
        self.click_circles.append(circle)

        # Use QTimer to remove the circle after the specified duration
        QTimer.singleShot(int(self.click_duration * 1000), lambda: self.remove_circle(circle))

    def remove_circle(self, circle):
        if circle in self.click_circles:
            circle.hide()
            self.click_circles.remove(circle)
            circle.deleteLater()


class SettingsPanel(QDialog):
    def __init__(self, highlighter, click_manager):
        super().__init__()
        self.highlighter = highlighter
        self.click_manager = click_manager

        self.setWindowTitle("JW Mouse Highlighter")
        self.setGeometry(100, 100, 400, 300)

        # Prevent the dialog from closing the app
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        layout = QVBoxLayout()

        # Add a checkbox for startup behavior
        self.startup_checkbox = QCheckBox("Start with Windows")
        self.startup_checkbox.stateChanged.connect(self.toggle_startup)
        layout.addWidget(self.startup_checkbox)

        # Check if the app is in startup and set the checkbox state
        self.startup_checkbox.setChecked(is_in_startup())

        # Highlighter settings group
        highlighter_group = QGroupBox("Highlighter")
        highlighter_layout = QGridLayout()

        # Highlighter Radius
        self.highlighter_radius_label = QLabel(str(self.highlighter.radius))
        self.highlighter_radius_slider = QSlider(Qt.Horizontal)
        self.highlighter_radius_slider.setRange(1, 200)
        self.highlighter_radius_slider.setValue(self.highlighter.radius)
        self.highlighter_radius_slider.valueChanged.connect(self.update_highlighter_radius)
        highlighter_layout.addWidget(QLabel("Radius"), 0, 0)
        highlighter_layout.addWidget(self.highlighter_radius_label, 0, 1)
        highlighter_layout.addWidget(self.highlighter_radius_slider, 0, 2)

        # Highlighter Transparency
        self.highlighter_transparency_label = QLabel(str(self.highlighter.color.alpha()))
        self.highlighter_transparency_slider = QSlider(Qt.Horizontal)
        self.highlighter_transparency_slider.setRange(0, 255)
        self.highlighter_transparency_slider.setValue(self.highlighter.color.alpha())
        self.highlighter_transparency_slider.valueChanged.connect(self.update_highlighter_transparency)
        highlighter_layout.addWidget(QLabel("Transparency"), 1, 0)
        highlighter_layout.addWidget(self.highlighter_transparency_label, 1, 1)
        highlighter_layout.addWidget(self.highlighter_transparency_slider, 1, 2)

        # Highlighter Color
        self.highlighter_color_preview = QLabel()
        self.highlighter_color_preview.setFixedSize(20, 20)
        self.highlighter_color_preview.setStyleSheet(f"background-color: {self.highlighter.color.name()};")
        self.highlighter_color_button = QPushButton("Choose Color")
        self.highlighter_color_button.clicked.connect(self.choose_highlighter_color)
        highlighter_layout.addWidget(QLabel("Color"), 2, 0)
        highlighter_layout.addWidget(self.highlighter_color_preview, 2, 1)
        highlighter_layout.addWidget(self.highlighter_color_button, 2, 2)

        highlighter_group.setLayout(highlighter_layout)
        layout.addWidget(highlighter_group)

        # Click settings group
        click_group = QGroupBox("Clicks")
        click_layout = QGridLayout()

        # Click Circle Radius
        self.click_radius_label = QLabel(str(self.click_manager.click_radius))
        self.click_radius_slider = QSlider(Qt.Horizontal)
        self.click_radius_slider.setRange(1, 200)
        self.click_radius_slider.setValue(self.click_manager.click_radius)
        self.click_radius_slider.valueChanged.connect(self.update_click_radius)
        click_layout.addWidget(QLabel("Circle Radius"), 0, 0)
        click_layout.addWidget(self.click_radius_label, 0, 1)
        click_layout.addWidget(self.click_radius_slider, 0, 2)

        # Click Circle Transparency
        self.click_transparency_label = QLabel(str(self.click_manager.click_color.alpha()))
        self.click_transparency_slider = QSlider(Qt.Horizontal)
        self.click_transparency_slider.setRange(0, 255)
        self.click_transparency_slider.setValue(self.click_manager.click_color.alpha())
        self.click_transparency_slider.valueChanged.connect(self.update_click_transparency)
        click_layout.addWidget(QLabel("Circle Transparency"), 1, 0)
        click_layout.addWidget(self.click_transparency_label, 1, 1)
        click_layout.addWidget(self.click_transparency_slider, 1, 2)

        # Click Circle Color
        self.click_color_preview = QLabel()
        self.click_color_preview.setFixedSize(20, 20)
        self.click_color_preview.setStyleSheet(f"background-color: {self.click_manager.click_color.name()};")
        self.click_color_button = QPushButton("Choose Circle Color")
        self.click_color_button.clicked.connect(self.choose_click_color)
        click_layout.addWidget(QLabel("Circle Color"), 2, 0)
        click_layout.addWidget(self.click_color_preview, 2, 1)
        click_layout.addWidget(self.click_color_button, 2, 2)

        # Click Duration
        self.click_duration_spinbox = QDoubleSpinBox()
        self.click_duration_spinbox.setRange(0.1, 10.0)
        self.click_duration_spinbox.setValue(self.click_manager.click_duration)
        self.click_duration_spinbox.setSingleStep(0.1)
        self.click_duration_spinbox.valueChanged.connect(self.update_click_duration)
        click_layout.addWidget(QLabel("Click Duration (seconds)"), 3, 0)
        click_layout.addWidget(self.click_duration_spinbox, 3, 1, 1, 2)

        # Max Click Circles
        self.max_circles_spinbox = QSpinBox()
        self.max_circles_spinbox.setRange(1, 10)
        self.max_circles_spinbox.setValue(self.click_manager.max_circles)
        self.max_circles_spinbox.valueChanged.connect(self.update_max_circles)
        click_layout.addWidget(QLabel("Max Clicks To Track"), 4, 0)
        click_layout.addWidget(self.max_circles_spinbox, 4, 1, 1, 2)

        click_group.setLayout(click_layout)
        layout.addWidget(click_group)

       

        self.setLayout(layout)


    def toggle_startup(self, state):
        if state == Qt.Checked:
            add_to_startup()
        else:
            remove_from_startup()

    def update_highlighter_radius(self, value):
        self.highlighter.radius = value
        self.highlighter.resize(value * 2, value * 2)
        self.highlighter_radius_label.setText(str(value))

    def update_highlighter_transparency(self, value):
        color = self.highlighter.color
        color.setAlpha(value)
        self.highlighter.color = color
        self.highlighter.update()
        self.highlighter_transparency_label.setText(str(value))

    def choose_highlighter_color(self):
        color = QColorDialog.getColor(self.highlighter.color, self, "Choose Highlighter Color")
        if color.isValid():
            color.setAlpha(self.highlighter.color.alpha())  # Preserve transparency
            self.highlighter.color = color
            self.highlighter.update()
            self.highlighter_color_preview.setStyleSheet(f"background-color: {color.name()};")

    def update_click_radius(self, value):
        self.click_manager.click_radius = value
        self.click_radius_label.setText(str(value))

    def update_click_transparency(self, value):
        self.click_manager.click_color.setAlpha(value)
        self.click_transparency_label.setText(str(value))

    def choose_click_color(self):
        color = QColorDialog.getColor(self.click_manager.click_color, self, "Choose Click Circle Color")
        if color.isValid():
            color.setAlpha(self.click_manager.click_color.alpha())  # Preserve transparency
            self.click_manager.click_color = color
            self.click_color_preview.setStyleSheet(f"background-color: {color.name()};")

    def update_click_duration(self, value):
        self.click_manager.click_duration = value

    def update_max_circles(self, value):
        self.click_manager.max_circles = value

    def closeEvent(self, event):
        # Hide the dialog instead of closing it
        self.hide()
        event.ignore()

    def showEvent(self, event):
        """Update UI elements when the settings panel is shown."""
        super().showEvent(event)
        
        # Update highlighter settings
        self.highlighter_radius_slider.setValue(self.highlighter.radius)
        self.highlighter_radius_label.setText(str(self.highlighter.radius))
        self.highlighter_transparency_slider.setValue(self.highlighter.color.alpha())
        self.highlighter_transparency_label.setText(str(self.highlighter.color.alpha()))
        self.highlighter_color_preview.setStyleSheet(f"background-color: {self.highlighter.color.name()};")

        # Update click circle settings
        self.click_radius_slider.setValue(self.click_manager.click_radius)
        self.click_radius_label.setText(str(self.click_manager.click_radius))
        self.click_transparency_slider.setValue(self.click_manager.click_color.alpha())
        self.click_transparency_label.setText(str(self.click_manager.click_color.alpha()))
        self.click_duration_spinbox.setValue(self.click_manager.click_duration)
        self.max_circles_spinbox.setValue(self.click_manager.max_circles)
        self.click_color_preview.setStyleSheet(f"background-color: {self.click_manager.click_color.name()};")

class SystemTrayApp:
    def __init__(self, app):
        self.app = app
        self.highlighter = MouseHighlighter()
        self.click_manager = ClickManager()
        self.settings_panel = SettingsPanel(self.highlighter, self.click_manager)

        # Load saved settings
        self.load_settings()

        # System tray setup
        self.tray_icon = QSystemTrayIcon(QIcon(resource_path("icon.png")), parent=app)
        self.tray_menu = QMenu()

        toggle_action = QAction("Toggle Highlight", self.tray_menu)
        toggle_action.triggered.connect(self.toggle_highlight)
        self.tray_menu.addAction(toggle_action)

        settings_action = QAction("Settings", self.tray_menu)
        settings_action.triggered.connect(self.show_settings)
        self.tray_menu.addAction(settings_action)

        exit_action = QAction("Exit", self.tray_menu)
        exit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.setToolTip("Mouse Highlighter")
        self.tray_icon.show()

        # Start mouse tracking thread
        self.mouse_tracker = MouseTracker()
        self.mouse_tracker.position_update.connect(self.highlighter.update_position)
        self.mouse_tracker.start()

        # Start pynput listener thread
        self.pynput_listener = PynputListener()
        self.pynput_listener.click_detected.connect(self.click_manager.add_click)
        self.pynput_listener.start()

        self.toggle_highlight()  # Enable the highlight when the program begins
        #Update the highlight immediately because when re-opening the program, the highlight circle sometimes draws partially cut-off
        self.settings_panel.update_highlighter_radius(self.highlighter.radius) 

    def load_settings(self):
        """Load saved settings from QSettings."""
        settings = QSettings("JW Mouse Highlighter", "Settings")

        # Highlighter settings
        self.highlighter.radius = settings.value("highlighter/radius", 100, int)
        self.highlighter.color = QColor(settings.value("highlighter/color", QColor(255, 255, 0, 50).name(), str))
        self.highlighter.color.setAlpha(settings.value("highlighter/transparency", 75, int))

        # Click circle settings
        self.click_manager.click_radius = settings.value("click/radius", 5, int)
        self.click_manager.click_color = QColor(settings.value("click/color", QColor(170, 255, 255, 175).name(), str))
        self.click_manager.click_color.setAlpha(settings.value("click/transparency", 175, int))
        self.click_manager.click_duration = settings.value("click/duration", 0.8, float)
        self.click_manager.max_circles = settings.value("click/max_circles", 2, int)

    def save_settings(self):
        """Save current settings to QSettings."""
        settings = QSettings("JW Mouse Highlighter", "Settings")

        # Highlighter settings
        settings.setValue("highlighter/radius", self.highlighter.radius)
        settings.setValue("highlighter/color", self.highlighter.color.name())
        settings.setValue("highlighter/transparency", self.highlighter.color.alpha())

        # Click circle settings
        settings.setValue("click/radius", self.click_manager.click_radius)
        settings.setValue("click/color", self.click_manager.click_color.name())
        settings.setValue("click/transparency", self.click_manager.click_color.alpha())
        settings.setValue("click/duration", self.click_manager.click_duration)
        settings.setValue("click/max_circles", self.click_manager.max_circles)

    def toggle_highlight(self):
        if self.highlighter.isVisible():
            self.highlighter.hide()
        else:
            self.highlighter.show()

    def show_settings(self):
        #self.settings_panel = SettingsPanel(self.highlighter, self.click_manager)
        self.settings_panel.show()

    def quit_app(self):
        # Save settings before quitting
        self.save_settings()

        self.mouse_tracker.quit()
        self.pynput_listener.quit()  # Stop the pynput listener thread
        self.app.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tray_app = SystemTrayApp(app)
    sys.exit(app.exec_())