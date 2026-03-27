from PySide6.QtWidgets import QApplication
from qfluentwidgets import ColorSettingCard, ColorDialog, PrimaryPushButton, qconfig, ColorConfigItem, QConfig, FluentIcon
from PySide6.QtGui import QColor
import sys

class AppConfig(QConfig):
    themeColor = ColorConfigItem('Island', 'ThemeColor', QColor('#ff0000'))

cfg = AppConfig()

class IslandColorSettingCard(ColorSettingCard):
    def __init__(self, configItem, icon, title, content=None, parent=None):
        super().__init__(configItem, icon, title, content, parent, enableAlpha=True)
        # Override the clicked connection to our custom dialog
        self.colorPicker.clicked.disconnect()
        self.colorPicker.clicked.connect(self._showCustomColorDialog)
        
    def _showCustomColorDialog(self):
        w = ColorDialog(self.colorPicker.color, self.tr('Choose ') + self.colorPicker.title, self.window(), self.colorPicker.enableAlpha)
        
        # Modify the dialog to add a Reset button
        self.resetBtn = PrimaryPushButton('重置为黑色', w.buttonGroup)
        
        # Adjust button geometry to fit three buttons
        w.yesButton.setFixedWidth(130)
        self.resetBtn.setFixedWidth(130)
        w.cancelButton.setFixedWidth(130)
        
        w.yesButton.move(24, 25)
        self.resetBtn.move(178, 25)
        w.cancelButton.move(332, 25)
        
        def on_reset():
            w.setColor(QColor(0, 0, 0, 255), True)
            
        self.resetBtn.clicked.connect(on_reset)
        
        w.colorChanged.connect(self.colorPicker._ColorPickerButton__onColorChanged)
        w.exec()

app = QApplication(sys.argv)
card = IslandColorSettingCard(cfg.themeColor, FluentIcon.PALETTE, 'Test')
card.show()
from PySide6.QtCore import QTimer
QTimer.singleShot(2000, app.quit)
app.exec()
