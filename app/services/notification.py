import asyncio
import threading
from typing import Callable, Dict, Any

try:
    from winrt.windows.ui.notifications.management import UserNotificationListener
    from winrt.windows.ui.notifications import NotificationKinds
    WINRT_AVAILABLE = True
except ImportError:
    WINRT_AVAILABLE = False


class NotificationService:
    """Windows系统通知接管服务（使用轮询方式，兼容非打包应用）"""
    
    def __init__(self):
        self._listener = None
        self._callback = None
        self._loop = None
        self._thread = None
        self._running = False
        self._known_notifications = set()
        self._poll_interval = 1.0 # 1秒轮询一次

    def start_listening(self, callback: Callable[[Dict[str, Any]], None]):
        if not WINRT_AVAILABLE:
            print("WinRT not available. Notification listener cannot start.")
            return

        self._callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop_listening(self):
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._poll_notifications())

    async def _poll_notifications(self):
        try:
            self._listener = UserNotificationListener.current
            access_status = await self._listener.request_access_async()
            
            if access_status == 1: # ALLOWED
                # 初始化已有的通知，避免启动时重复弹窗
                try:
                    current_notifications = await self._listener.get_notifications_async(NotificationKinds.TOAST)
                    for n in current_notifications:
                        self._known_notifications.add(n.id)
                except Exception as e:
                    print(f"Error getting initial notifications: {e}")

                print("Successfully started polling Windows notifications.")
                
                # 开始轮询
                while self._running:
                    try:
                        notifications = await self._listener.get_notifications_async(NotificationKinds.TOAST)
                        current_ids = set()
                        
                        for n in notifications:
                            current_ids.add(n.id)
                            if n.id not in self._known_notifications:
                                self._known_notifications.add(n.id)
                                self._process_new_notification(n)
                                
                        # 清理已经消失的通知记录
                        self._known_notifications.intersection_update(current_ids)
                        
                    except Exception as e:
                        print(f"Error polling notifications: {e}")
                    
                    await asyncio.sleep(self._poll_interval)
            else:
                print(f"Notification access denied. Status: {access_status}")
        except Exception as e:
            print(f"Error setting up notification listener: {e}")

    def _process_new_notification(self, n):
        try:
            app_name = n.app_info.display_info.display_name if n.app_info else "System"
            title = ""
            content = ""
            
            try:
                text_elements = n.notification.visual.bindings[0].get_text_elements()
                texts = [t.text for t in text_elements if t.text]
                if len(texts) > 0:
                    title = texts[0]
                if len(texts) > 1:
                    content = "\n".join(texts[1:])
            except Exception as e:
                print(f"Error parsing notification text: {e}")
                
            if title or content:
                notification_data = {
                    "app": app_name,
                    "title": title,
                    "content": content
                }
                if self._callback:
                    self._callback(notification_data)
        except Exception as e:
            print(f"Error processing notification: {e}")
