import os
import pygame
import logging
from gtts import gTTS

# ------------------- PHÁT ÂM THANH -------------------------
def TTS(text):
    """
    Phát âm thanh text bằng gTTS
    """
    try:
        # Tạo thư mục __cache__ nếu chưa tồn tại
        cache_dir = "__cache__"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        pygame.mixer.init()
        tts = gTTS(text=text, lang='vi')
        tts.save(f"{cache_dir}/thongbao.mp3")
        pygame.mixer.music.load(f"{cache_dir}/thongbao.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        os.remove(f"{cache_dir}/thongbao.mp3")
    except Exception as e:
        logging.error(f"Lỗi phát âm thanh: {e}")
        print(f"Lỗi phát âm thanh: {e}")
