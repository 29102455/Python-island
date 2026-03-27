import asyncio
import urllib.request
import urllib.parse
import json
import win32gui
from typing import Optional, Dict, Any, Callable
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager, GlobalSystemMediaTransportControlsSessionPlaybackStatus

class MediaService:
    def __init__(self):
        self._manager = None
        self._loop = asyncio.new_event_loop()
        self._last_title = None
        self._last_artist = None
        self._lyrics = ""
        self._is_fallback_mode = False
        
    def _run_async(self, coro):
        asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(coro)

    async def _init_manager(self):
        if not self._manager:
            self._manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        return self._manager

    def _get_netease_fallback_info(self) -> Optional[Dict[str, Any]]:
        """当系统SMTC检测不到时，尝试通过窗口标题读取网易云音乐的状态"""
        try:
            windows = []
            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    class_name = win32gui.GetClassName(hwnd)
                    if class_name == 'OrpheusBrowserHost':
                        title = win32gui.GetWindowText(hwnd)
                        windows.append(title)
                        
            win32gui.EnumWindows(callback, None)
            
            if windows and windows[0]:
                title_str = windows[0]
                if ' - ' in title_str:
                    # 格式通常是 "歌曲名 - 歌手"
                    parts = title_str.split(' - ', 1)
                    title = parts[0].strip()
                    artist = parts[1].strip()
                    
                    return {
                        'title': title,
                        'artist': artist,
                        # 无法通过标题判断是否正在播放，假设在播放
                        'is_playing': True, 
                        'is_fallback': True
                    }
        except Exception as e:
            print(f"Fallback detection error: {e}")
            
        return None

    def fetch_lyrics(self, title: str, artist: str) -> str:
        try:
            # 当从标题解析出数据时，格式可能不太规范（比如包含一些额外标记），尝试用通用搜索
            query = title
            if artist and not self._is_fallback_mode:
                # 只有非 fallback 模式才强制带上 artist，因为 fallback 解析出的 artist 可能是错的
                url = f'https://lrclib.net/api/search?track_name={urllib.parse.quote(title)}&artist_name={urllib.parse.quote(artist)}'
            else:
                # Fallback 模式下，直接把解析出来的整个内容作为搜索关键词
                search_query = f"{title} {artist}" if artist else title
                url = f'https://lrclib.net/api/search?q={urllib.parse.quote(search_query)}'
                
            req = urllib.request.Request(url, headers={'User-Agent': 'Python-island'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data and len(data) > 0:
                    lyrics = data[0].get('plainLyrics') or data[0].get('syncedLyrics') or "未找到歌词"
                    # 返回第一行非空歌词
                    for line in lyrics.split('\n'):
                        if line.startswith('['):
                            parts = line.split(']', 1)
                            if len(parts) > 1:
                                line = parts[1]
                        line = line.strip()
                        if line:
                            return line
                    return "未找到歌词"
                else:
                    # 如果 fallback 的全名搜索失败，尝试只搜歌曲名
                    if self._is_fallback_mode and artist:
                        url2 = f'https://lrclib.net/api/search?q={urllib.parse.quote(title)}'
                        req2 = urllib.request.Request(url2, headers={'User-Agent': 'Python-island'})
                        with urllib.request.urlopen(req2, timeout=5) as response2:
                            data2 = json.loads(response2.read().decode('utf-8'))
                            if data2 and len(data2) > 0:
                                lyrics = data2[0].get('plainLyrics') or data2[0].get('syncedLyrics') or "未找到歌词"
                                for line in lyrics.split('\n'):
                                    if line.startswith('['):
                                        parts = line.split(']', 1)
                                        if len(parts) > 1:
                                            line = parts[1]
                                    line = line.strip()
                                    if line:
                                        return line
                                return "未找到歌词"
                    return "未找到歌词"
        except Exception as e:
            print(f'Error fetching lyrics: {e}')
            return "获取歌词失败"

    def get_media_info(self) -> Optional[Dict[str, Any]]:
        return self._run_async(self._get_media_info_async())
        
    async def _get_media_info_async(self) -> Optional[Dict[str, Any]]:
        manager = await self._init_manager()
        session = manager.get_current_session()
        
        info_dict = None
        
        if session:
            try:
                info = await session.try_get_media_properties_async()
                playback_info = session.get_playback_info()
                is_playing = playback_info.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
                
                info_dict = {
                    'title': info.title,
                    'artist': info.artist,
                    'is_playing': is_playing,
                    'is_fallback': False
                }
            except Exception as e:
                print(f"Error getting SMTC media info: {e}")
                
        # 如果 SMTC 没有获取到，尝试 fallback 方法（比如读取网易云窗口标题）
        if not info_dict or not info_dict.get('title'):
            info_dict = self._get_netease_fallback_info()
            self._is_fallback_mode = True
        else:
            self._is_fallback_mode = False
            
        if not info_dict:
            return None
            
        # Fetch lyrics if track changed
        title = info_dict.get('title')
        artist = info_dict.get('artist')
        
        if title and (title != self._last_title or artist != self._last_artist):
            self._last_title = title
            self._last_artist = artist
            self._lyrics = "正在搜索歌词..."
            import threading
            def update_lyrics():
                self._lyrics = self.fetch_lyrics(title, artist)
            threading.Thread(target=update_lyrics, daemon=True).start()
        
        info_dict['lyrics'] = self._lyrics
        return info_dict
            
    def play_pause(self):
        self._run_async(self._play_pause_async())
        
    async def _play_pause_async(self):
        manager = await self._init_manager()
        session = manager.get_current_session()
        if session:
            playback_info = session.get_playback_info()
            if playback_info.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                await session.try_pause_async()
            else:
                await session.try_play_async()
        else:
            # Fallback 模拟媒体按键控制
            import win32api
            import win32con
            # VK_MEDIA_PLAY_PAUSE
            win32api.keybd_event(0xB3, win32api.MapVirtualKey(0xB3, 0), 0, 0)
            win32api.keybd_event(0xB3, win32api.MapVirtualKey(0xB3, 0), win32con.KEYEVENTF_KEYUP, 0)
                
    def next_track(self):
        self._run_async(self._next_track_async())
        
    async def _next_track_async(self):
        manager = await self._init_manager()
        session = manager.get_current_session()
        if session:
            await session.try_skip_next_async()
        else:
            # Fallback 模拟媒体按键控制
            import win32api
            import win32con
            # VK_MEDIA_NEXT_TRACK
            win32api.keybd_event(0xB0, win32api.MapVirtualKey(0xB0, 0), 0, 0)
            win32api.keybd_event(0xB0, win32api.MapVirtualKey(0xB0, 0), win32con.KEYEVENTF_KEYUP, 0)
            
    def prev_track(self):
        self._run_async(self._prev_track_async())
        
    async def _prev_track_async(self):
        manager = await self._init_manager()
        session = manager.get_current_session()
        if session:
            await session.try_skip_previous_async()
        else:
            # Fallback 模拟媒体按键控制
            import win32api
            import win32con
            # VK_MEDIA_PREV_TRACK
            win32api.keybd_event(0xB1, win32api.MapVirtualKey(0xB1, 0), 0, 0)
            win32api.keybd_event(0xB1, win32api.MapVirtualKey(0xB1, 0), win32con.KEYEVENTF_KEYUP, 0)
