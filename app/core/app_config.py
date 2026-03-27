import os
from qfluentwidgets import QConfig, ColorConfigItem, qconfig
from PySide6.QtGui import QColor

class AppConfig(QConfig):
    """应用配置"""
    islandThemeColor = ColorConfigItem("Island", "ThemeColor", QColor(0, 0, 0))

cfg = AppConfig()
config_path = os.path.join(os.path.expanduser('~'), '.pyisland', 'config.json')
qconfig.load(config_path, cfg)
