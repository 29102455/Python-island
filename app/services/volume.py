import ctypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class VolumeService:
    @staticmethod
    def get_volume() -> int:
        try:
            devices = AudioUtilities.GetSpeakers()
            if not devices:
                return 50
            volume = devices.EndpointVolume
            current_volume = volume.GetMasterVolumeLevelScalar()
            return round(current_volume * 100)
        except Exception as e:
            print(f"Error getting volume: {e}")
            return 50

    @staticmethod
    def set_volume(level: int):
        try:
            level = max(0, min(100, level))
            devices = AudioUtilities.GetSpeakers()
            if not devices:
                return
            volume = devices.EndpointVolume
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        except Exception as e:
            print(f"Error setting volume: {e}")
