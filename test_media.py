import asyncio
import time
from app.services.media import MediaService
import traceback

def main():
    ms = MediaService()
    for _ in range(5):
        try:
            info = ms.get_media_info()
            if info:
                print(f"Title: {info.get('title')}, Position: {info.get('position')}, Playing: {info.get('is_playing')}")
            else:
                print('No media info')
        except Exception as e:
            print('Error:')
            traceback.print_exc()
        time.sleep(1)

main()
