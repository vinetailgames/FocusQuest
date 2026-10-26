# music_player.py
import pygame
import os
from constants import MUSIC_DIR

class MusicPlayer:
    def __init__(self):
        self.songs = []          # list of (display_name, full_path)
        self.current_song = None
        self.is_playing = False
        self.load_songs()

    def load_songs(self):
        """Scan music folder and load available tracks."""
        self.songs.clear()
        if not os.path.exists(MUSIC_DIR):
            os.makedirs(MUSIC_DIR, exist_ok=True)
            print(f"Created music folder: {MUSIC_DIR}")
            return

        supported = (".mp3", ".ogg", ".wav")
        for filename in sorted(os.listdir(MUSIC_DIR)):
            if filename.lower().endswith(supported):
                name = os.path.splitext(filename)[0]  # remove extension
                path = os.path.join(MUSIC_DIR, filename)
                self.songs.append((name, path))

        print(f"Loaded {len(self.songs)} songs.")

    def play(self, index):
        """Play song by index. If same song is already playing → stop."""
        if index < 0 or index >= len(self.songs):
            return

        name, path = self.songs[index]

        # Clicking the same song again → stop
        if self.current_song == path and self.is_playing:
            self.stop()
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)  # loop forever
            self.current_song = path
            self.is_playing = True
            print(f"Now playing: {name}")
        except Exception as e:
            print(f"Could not play {name}: {e}")
            self.is_playing = False
            self.current_song = None

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.current_song = None
        print("Music stopped.")

    def get_song_names(self):
        return [name for name, _ in self.songs]