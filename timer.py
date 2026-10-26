# timer.py
import pygame
import os
from constants import ASSETS_DIR

class PomodoroTimer:
    def __init__(self):
        self.study_seconds = 25 * 60
        self.break_seconds = 5 * 60
        self.remaining = self.study_seconds
        self.is_break = False
        self.running = False
        self.paused = False
        self.finished = False

        self.rain_sound = None
        self.alarm_sound = None
        self.load_sounds()

    def load_sounds(self):
        rain_path = os.path.join(ASSETS_DIR, "sounds", "rain.wav")
        alarm_path = os.path.join(ASSETS_DIR, "sounds", "alarm.mp3")

        try:
            if os.path.exists(rain_path):
                self.rain_sound = pygame.mixer.Sound(rain_path)
                self.rain_sound.set_volume(0.0)
        except Exception as e:
            print(f"Could not load rain: {e}")

        try:
            if os.path.exists(alarm_path):
                self.alarm_sound = pygame.mixer.Sound(alarm_path)
        except Exception as e:
            print(f"Could not load alarm: {e}")

    def set_times(self, study_min, break_min):
        self.study_seconds = max(1, study_min) * 60
        self.break_seconds = max(1, break_min) * 60
        self.remaining = self.study_seconds
        self.is_break = False
        self.finished = False

    def start(self):
        if self.remaining <= 0:
            self.remaining = self.break_seconds if self.is_break else self.study_seconds
        self.running = True
        self.paused = False
        self.finished = False
        if not self.is_break:
            self._fade_rain(True)

    def pause(self):
        self.paused = True
        self._fade_rain(False)

    def resume(self):
        self.paused = False
        if not self.is_break:
            self._fade_rain(True)

    def stop(self):
        self.running = False
        self.paused = False
        self.is_break = False
        self.remaining = self.study_seconds
        self._fade_rain(False)
        self._play_alarm()

    def update(self, dt):
        if self.running and not self.paused and self.remaining > 0:
            self.remaining -= dt / 1000
            if self.remaining <= 0:
                self.remaining = 0
                self.running = False
                self.finished = True
                self._fade_rain(False)
                self._play_alarm()

                # Auto switch to break after study
                if not self.is_break:
                    self.is_break = True
                    self.remaining = self.break_seconds

    def get_time_str(self):
        total = max(0, int(self.remaining))
        minutes = total // 60
        seconds = total % 60
        prefix = "Break " if self.is_break else ""
        return f"{prefix}{minutes:02d}:{seconds:02d}"

    def _fade_rain(self, fade_in):
        if not self.rain_sound:
            return
        if fade_in:
            self.rain_sound.play(-1)
            for v in range(0, 6):
                self.rain_sound.set_volume(v / 10)
                pygame.time.delay(30)
        else:
            for v in range(5, -1, -1):
                self.rain_sound.set_volume(v / 10)
                pygame.time.delay(30)
            self.rain_sound.stop()

    def _play_alarm(self):
        if self.alarm_sound:
            self.alarm_sound.play()