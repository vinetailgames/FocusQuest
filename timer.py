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
        self.just_finished = False   # used by main to detect finish
        self.just_finished_study = False

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
        self.just_finished = False
        self.just_finished_study = False

    def start(self):
        if self.remaining <= 0:
            self.remaining = self.break_seconds if self.is_break else self.study_seconds
        self.running = True
        self.paused = False
        self.just_finished = False
        self.just_finished_study = False
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
        """Stop without playing alarm."""
        self.running = False
        self.paused = False
        self.is_break = False
        self.remaining = self.study_seconds
        self.just_finished = False
        self.just_finished_study = False
        self._fade_rain(False)

    def update(self, dt):
        self.just_finished = False
        self.just_finished_study = False

        if self.running and not self.paused and self.remaining > 0:
            self.remaining -= dt / 1000.0

            if self.remaining <= 0:
                finished_study = not self.is_break
                self.remaining = 0
                self.running = False
                self.just_finished = True
                self.just_finished_study = finished_study
                self._fade_rain(False)
                self._play_alarm()

                if finished_study:
                    self.is_break = True
                    self.remaining = self.break_seconds
                    self.running = True
                else:
                    self.is_break = False
                    self.remaining = self.study_seconds

    def get_time_str(self):
        total = max(0, int(self.remaining))
        minutes = total // 60
        seconds = total % 60
        session = "Break" if self.is_break else "Focus"
        return f"{session}: {minutes:02d}:{seconds:02d}"

    def _fade_rain(self, fade_in):
        if not self.rain_sound:
            return
        if fade_in:
            self.rain_sound.play(-1)
            for v in range(0, 6):
                self.rain_sound.set_volume(v / 10.0)
                pygame.time.delay(25)
        else:
            for v in range(5, -1, -1):
                self.rain_sound.set_volume(v / 10.0)
                pygame.time.delay(25)
            self.rain_sound.stop()

    def _play_alarm(self):
        if self.alarm_sound:
            self.alarm_sound.play()
