import urllib.request
import json
import threading
import time

class WeatherService:
    def __init__(self):
        self._weather_data = None
        self._last_update = 0
        self._update_interval = 1800  # Update every 30 minutes
        self._lock = threading.Lock()
        
    def get_weather(self):
        current_time = time.time()
        
        with self._lock:
            if self._weather_data and (current_time - self._last_update) < self._update_interval:
                return self._weather_data
                
        # Run update in a separate thread to avoid blocking
        threading.Thread(target=self._update_weather, daemon=True).start()
        
        return self._weather_data
        
    def _update_weather(self):
        try:
            req = urllib.request.Request('http://ip-api.com/json/', headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                location_data = json.loads(response.read().decode('utf-8'))
                lat = location_data['lat']
                lon = location_data['lon']
                
            req2 = urllib.request.Request(f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code', headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req2, timeout=5) as response2:
                weather_data = json.loads(response2.read().decode('utf-8'))
                temp = weather_data['current']['temperature_2m']
                code = weather_data['current']['weather_code']
                
                weather_desc = {
                    0: ('☀️', '晴'),
                    1: ('🌤️', '晴间多云'), 2: ('⛅', '多云'), 3: ('☁️', '阴'),
                    45: ('🌫️', '雾'), 48: ('🌫️', '雾凇'),
                    51: ('🌧️', '毛毛雨'), 53: ('🌧️', '毛毛雨'), 55: ('🌧️', '毛毛雨'),
                    61: ('🌧️', '小雨'), 63: ('🌧️', '中雨'), 65: ('🌧️', '大雨'),
                    71: ('🌨️', '小雪'), 73: ('🌨️', '中雪'), 75: ('🌨️', '大雪'),
                    95: ('⛈️', '雷阵雨'), 96: ('⛈️', '雷阵雨'), 99: ('⛈️', '雷阵雨伴有冰雹')
                }
                icon, text = weather_desc.get(code, ('❓', '未知'))
                
                with self._lock:
                    self._weather_data = {
                        "temp": f"{temp}°C",
                        "icon": icon,
                        "desc": text,
                        "full": f"{temp}°C {icon} {text}"
                    }
                    self._last_update = time.time()
                    
        except Exception as e:
            print(f"Weather update error: {e}")
