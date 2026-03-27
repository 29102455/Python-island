"""UI构建器模块

负责灵动岛UI组件的构建和初始化。
"""

from typing import Tuple, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel,
    QStackedWidget, QVBoxLayout, QWidget, QSlider
)

from app.core.config import (
    COLLAPSED_WIDTH,
    COLLAPSED_HEIGHT,
    CONTROLS_HEIGHT,
    EXPANDED_WIDTH,
    TIME_LABEL_HEIGHT,
)
from app.core.icons import IslandIcon
from app.ui.controls import ControlRowFactory
from app.ui.status_bar import StatusBar
from app.ui.url_dialog import UrlDialog

from PySide6.QtGui import QFont  # 如果已导入则无需重复



class IslandUIBuilder:
    """灵动岛UI构建器

    负责创建和配置所有UI组件。

    Attributes:
        container: 主容器
        time_label: 时间标签
        date_label: 日期标签
        controls: 控制面板堆栈
        status_bar: 状态栏
        bright_slider: 亮度滑块
        bright_val: 亮度值标签
    """

    def __init__(self, parent: QWidget):
        self._parent = parent
        self._icon_cache: Dict[IslandIcon, Any] = {}

    def build(self) -> Tuple[QFrame, QLabel, QLabel, QStackedWidget, StatusBar, QSlider, QLabel, QSlider, QLabel, Dict[str, Any]]:
        self._icon_cache = ControlRowFactory.preload_icons(list(IslandIcon))

        container = self._create_container()
        time_label, date_label, weather_label_small = self._create_time_labels()
        controls, status_bar, bright_slider, bright_val, volume_slider, volume_val = self._create_controls()

        # 使用水平布局将时间和天气放在一起
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)
        top_layout.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(time_label)
        top_layout.addWidget(weather_label_small)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.addWidget(top_container)
        layout.addWidget(controls)

        # 保存媒体控件的引用以便后续更新
        return container, time_label, date_label, controls, status_bar, bright_slider, bright_val, volume_slider, volume_val, {
            'title': self.song_title_label,
            'artist': self.song_artist_label,
            'lyrics': self.lyrics_label,
            'prev': self.btn_prev,
            'play': self.btn_play,
            'next': self.btn_next,
            'weather_small': weather_label_small
        }

    def _create_container(self) -> QFrame:
        container = QFrame(self._parent)
        container.setObjectName("IslandContainer")
        container.setFixedSize(COLLAPSED_WIDTH, COLLAPSED_HEIGHT)
        container.setMouseTracking(True)
        return container

    def _create_time_labels(self) -> Tuple[QLabel, QLabel]:
        time_label = QLabel("")
        time_label.setObjectName("TimeLabel")
        time_label.setAlignment(Qt.AlignCenter)
        time_label.setFixedHeight(TIME_LABEL_HEIGHT)
        
        weather_label_small = QLabel("")
        weather_label_small.setObjectName("WeatherLabelSmall")
        weather_label_small.setAlignment(Qt.AlignCenter)
        weather_label_small.setFixedHeight(TIME_LABEL_HEIGHT)
        weather_label_small.setStyleSheet("color: white;")
        font_weather_small = QFont()
        font_weather_small.setBold(True)
        font_weather_small.setPointSize(12)
        weather_label_small.setFont(font_weather_small)

        date_label = QLabel("")
        date_label.setObjectName("DateLabel")
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setFixedHeight(TIME_LABEL_HEIGHT)
        date_label.hide()
        date_label.setParent(self._parent)

        return time_label, date_label, weather_label_small

    def _create_controls(self) -> Tuple[QStackedWidget, StatusBar, QSlider, QLabel, QSlider, QLabel]:
        controls = QStackedWidget()
        controls.hide()
        controls.setFixedHeight(CONTROLS_HEIGHT)

        ctrl_page, status_bar, bright_slider, bright_val, volume_slider, volume_val = self._create_ctrl_page()
        url_single_page, url_multi_page = self._create_url_pages()
        empty_page = self._create_empty_page()

        controls.addWidget(ctrl_page)
        controls.addWidget(url_single_page)
        controls.addWidget(url_multi_page)
        controls.addWidget(empty_page)

        return controls, status_bar, bright_slider, bright_val, volume_slider, volume_val

    def _create_ctrl_page(self) -> Tuple[QWidget, StatusBar, QSlider, QLabel, QSlider, QLabel]:
        ctrl_page = QWidget()
        ctrl_layout = QVBoxLayout(ctrl_page)
        #减少顶部边距
        ctrl_layout.setContentsMargins(5, 10, 5, 10)
        ctrl_layout.setSpacing(10)

        bright_row, bright_slider, bright_val = \
            ControlRowFactory.create(self._icon_cache, IslandIcon.LIGHT, "亮度")
            
        volume_row, volume_slider, volume_val = \
            ControlRowFactory.create(self._icon_cache, IslandIcon.VOLUME, "音量")

        status_bar = StatusBar(self._icon_cache, self._parent)

        ctrl_layout.addLayout(bright_row)
        ctrl_layout.addLayout(volume_row)
        ctrl_layout.addWidget(status_bar)

        return ctrl_page, status_bar, bright_slider, bright_val, volume_slider, volume_val

    def _create_url_pages(self) -> Tuple[UrlDialog, UrlDialog]:
        url_single_page = UrlDialog()
        url_multi_page = UrlDialog()
        return url_single_page, url_multi_page

    def _create_empty_page(self) -> QWidget:
        """创建媒体控制页面（用于右键展开）"""
        media_page = QWidget()
        media_layout = QVBoxLayout(media_page)
        # 恢复使用原生的 margin 和 spacing 来管理布局，避免弹簧导致的挤压重叠
        # 调整上边距，将歌曲名称及后续控件整体上移
        media_layout.setContentsMargins(15, 10, 15, 10)
        # 将整体间距缩小为0，通过控件自身的margin/padding来控制，使得歌词和下方控制按钮更近
        media_layout.setSpacing(0) 
        
        # --- 标题区域 ---
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 歌曲信息标签
        self.song_title_label = QLabel("暂无播放")
        self.song_title_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.song_title_label.setFont(font)
        self.song_title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        # 允许标题在过长时自动换行，避免被截断
        self.song_title_label.setWordWrap(True)
        
        self.song_artist_label = QLabel("")
        self.song_artist_label.hide() # 隐藏歌手信息
        
        title_layout.addWidget(self.song_title_label)
        
        # 将 title_container 设为固定高度，只留给歌名足够的空间
        title_container.setFixedHeight(50) # 增加高度以容纳顶部边距
        # 增加标题容器的下边距，拉开与下方歌词区域的距离，并增加上边距将文字往下推
        title_container.setContentsMargins(0, 15, 0, 5)
        media_layout.addWidget(title_container)
        
        # --- 歌词区域 ---
        from PySide6.QtWidgets import QScrollArea
        
        self.lyrics_label = QLabel("歌词显示区域")
        self.lyrics_label.setAlignment(Qt.AlignCenter)
        font_lyrics = QFont()
        font_lyrics.setPointSize(11)
        self.lyrics_label.setFont(font_lyrics)
        self.lyrics_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.75); 
                background-color: transparent;
                padding: 4px;
            }
        """)
        self.lyrics_label.setWordWrap(False) # 取消自动换行，保持单行
        
        scroll = QScrollArea()
        scroll.setWidget(self.lyrics_label)
        scroll.setWidgetResizable(True)
        # 隐藏滚动条
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: transparent; 
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        # 精确调整高度以完美容纳单行歌词
        scroll.setFixedHeight(30)
        media_layout.addWidget(scroll)
        
        # --- 媒体控制按钮区域 ---
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.setContentsMargins(0, 5, 0, 0) # 减小按钮上方的边距
        btn_layout.setSpacing(40)
        
        from PySide6.QtWidgets import QPushButton
        
        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶️")
        self.btn_next = QPushButton("⏭")
        
        for btn in [self.btn_prev, self.btn_play, self.btn_next]:
            btn.setFixedSize(32, 32)
            # 添加手型光标效果
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    font-size: 18px;
                    border: none;
                }
                QPushButton:hover {
                    color: rgba(255, 255, 255, 0.7);
                }
                QPushButton:pressed {
                    color: rgba(255, 255, 255, 0.5);
                }
            """)
            btn_layout.addWidget(btn)
            
        media_layout.addLayout(btn_layout)
        
        # 底部留白，利用 Stretch 将所有内容向上推
        media_layout.addStretch()
        
        return media_page

    @staticmethod
    def calculate_label_width(label: QLabel, text: str, object_name: str = None) -> int:
        temp_label = QLabel(text)
        if object_name:
            temp_label.setObjectName(object_name)
            temp_label.setStyleSheet(label.styleSheet())
            temp_label.setFont(label.font())
        temp_label.adjustSize()
        return temp_label.width()

    @staticmethod
    def position_label_center(label: QLabel, text: str, container_width: int, object_name: str = None, container_height: int = None):
        width = IslandUIBuilder.calculate_label_width(label, text, object_name)
        x = (container_width - width) // 2
        
        # 垂直居中
        y = 0
        if container_height:
            label_height = label.height()
            y = (container_height - label_height) // 2
        
        label.setFixedWidth(width)
        label.move(x, y)

    def get_icon_cache(self) -> Dict[IslandIcon, Any]:
        return self._icon_cache

    def setup_ui(self, main_window):
        """设置主界面UI"""
        main_window.setAttribute(Qt.WA_TranslucentBackground)
        
        # 主布局
        main_layout = QVBoxLayout(main_window)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 背景容器（用于绘制圆角和背景色）
        self.bg_widget = QWidget()
        self.bg_widget.setStyleSheet("""
            QWidget {
                background-color: #000000;
                border-radius: 20px;
            }
        """)
        
        bg_layout = QVBoxLayout(self.bg_widget)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部布局（始终显示的内容，包含时间和天气）
        self.top_widget = QWidget()
        top_layout = QHBoxLayout(self.top_widget)
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(10)
        
        # 时间标签
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: white;")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.time_label.setFont(font)
        
        # 天气标签（折叠时显示：图标+温度）
        self.weather_label_small = QLabel()
        self.weather_label_small.setAlignment(Qt.AlignCenter)
        self.weather_label_small.setStyleSheet("color: white;")
        font_weather_small = QFont()
        font_weather_small.setBold(True)
        font_weather_small.setPointSize(12)
        self.weather_label_small.setFont(font_weather_small)
        
        # 使用水平布局将时间居中偏左一点，天气紧随其后
        time_weather_container = QWidget()
        time_weather_layout = QHBoxLayout(time_weather_container)
        time_weather_layout.setContentsMargins(0, 0, 0, 0)
        time_weather_layout.setSpacing(8)
        time_weather_layout.addStretch()
        time_weather_layout.addWidget(self.time_label)
        time_weather_layout.addWidget(self.weather_label_small)
        time_weather_layout.addStretch()
        
        top_layout.addWidget(time_weather_container)
        
        # 展开的内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 堆叠布局管理不同的展开页面
        self.stacked_widget = QStackedWidget()
        
        # 添加各个页面
        self.page_time_weather = self._create_time_weather_page()
        self.page_media = self._create_empty_page() # 借用原有的 media 页面，稍后重命名
        
        self.stacked_widget.addWidget(self.page_time_weather)
        self.stacked_widget.addWidget(self.page_media)
        
        self.content_layout.addWidget(self.stacked_widget)
        self.content_widget.hide()  # 默认隐藏
        
        bg_layout.addWidget(self.top_widget)
        bg_layout.addWidget(self.content_widget)
        
        main_layout.addWidget(self.bg_widget)
        
        return {
            'bg_widget': self.bg_widget,
            'top_widget': self.top_widget,
            'time_label': self.time_label,
            'weather_label_small': self.weather_label_small,
            'content_widget': self.content_widget,
            'stacked_widget': self.stacked_widget
        }