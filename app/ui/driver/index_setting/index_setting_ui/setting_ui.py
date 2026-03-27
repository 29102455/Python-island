"""图形设置界面模块"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from qfluentwidgets import (
    ScrollArea, 
    SettingCardGroup, 
    ColorSettingCard, 
    FluentIcon,
    PrimaryPushButton,
    qconfig
)
from qfluentwidgets.components.dialog_box.color_dialog import ColorDialog

from app.core.app_config import cfg
from app.ui.interfaces.index_setting.index_setting_ui.island_index_setting_ui_ui import (
    Ui_island_index_setting_ui_ui,
)


class IslandColorSettingCard(ColorSettingCard):
    """自定义颜色设置卡片，拦截颜色选择器以增加重置按钮"""
    
    def __init__(self, configItem, icon, title, content=None, parent=None):
        super().__init__(configItem, icon, title, content, parent, enableAlpha=True)
        # 取消原来的弹窗连接
        self.colorPicker.clicked.disconnect()
        # 连接到我们自定义的弹窗方法
        self.colorPicker.clicked.connect(self._showCustomColorDialog)
        
    def setValue(self, color: QColor):
        self.colorPicker.setColor(color)

    def _showCustomColorDialog(self):
        w = ColorDialog(self.colorPicker.color, self.tr('Choose ') + self.colorPicker.title, self.window(), self.colorPicker.enableAlpha)
        
        # 在弹窗的 buttonGroup 中添加重置按钮
        self.resetBtn = PrimaryPushButton('重置为黑色', w.buttonGroup)
        
        # 调整三个按钮的位置和宽度以适应 (原始宽度为 486, margin=24, 两个按钮 width=216)
        # 我们把宽度改成 130，间距适中
        w.yesButton.setFixedWidth(130)
        self.resetBtn.setFixedWidth(130)
        w.cancelButton.setFixedWidth(130)
        
        w.yesButton.move(24, 25)
        self.resetBtn.move(178, 25)
        w.cancelButton.move(332, 25)
        
        def on_reset():
            w.setColor(QColor(0, 0, 0, 255), True)
            
        self.resetBtn.clicked.connect(on_reset)
        
        # 保存旧颜色，用于取消时恢复
        old_color = QColor(self.colorPicker.color)

        if old_color.red() == 0 and old_color.green() == 0 and old_color.blue() == 0:
            seed = QColor(old_color)
            seed.setHsv(0, 0, 255, seed.alpha())
            w.setColor(seed, True)

        # 覆写 w.setColor 来拦截所有内部颜色更新并触发实时预览
        original_set_color = w.setColor
        def custom_set_color(color, movePicker=True):
            original_set_color(color, movePicker)
            self.configItem.value = QColor(color)
            
        w.setColor = custom_set_color
        
        # 我们需要自己触发 ColorPickerButton 的更新机制
        # 原本的 _ColorPickerButton__onColorChanged 接收 colorChanged 信号
        w.colorChanged.connect(self.colorPicker._ColorPickerButton__onColorChanged)
        
        # 在用户点击确定时，如果有颜色变化（或重置操作），更新配置文件
        if w.exec():
            # 点击确定，保存到文件
            # 强制设置以保存，即使值相同也要保存
            self.configItem.value = w.color
            cfg.save()
            qconfig.themeColorChanged.emit(w.color)
        else:
            # 点击取消，恢复旧颜色
            self.configItem.value = old_color


class SettingUiDriver(ScrollArea, Ui_island_index_setting_ui_ui):
    """图形设置界面驱动类。"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._init_ui()

    def _init_ui(self):
        self.scg_index_setting_ui_main = SettingCardGroup(
            title="图形",
        )
        self.theme_color_card = IslandColorSettingCard(
            cfg.islandThemeColor,
            FluentIcon.PALETTE,
            title="灵动岛主题色",
            content="设置灵动岛的背景主题颜色"
        )
        self.scg_index_setting_ui_main.addSettingCard(self.theme_color_card)
        self.setWidget(self.scg_index_setting_ui_main)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()


# 兼容旧代码
setting_ui_driver = SettingUiDriver
