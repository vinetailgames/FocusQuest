# main.py
import pygame
import sys
import os
from constants import *
from ui import Button
from music_player import MusicPlayer

def load_background():
    try:
        if os.path.exists(BACKGROUND_PATH):
            img = pygame.image.load(BACKGROUND_PATH).convert()
            return pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            print(f"Background not found at {BACKGROUND_PATH}. Using fallback.")
    except Exception as e:
        print(f"Error loading background: {e}")

    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surface.fill(DARK_GRAY)
    return surface

def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    background = load_background()
    music_player = MusicPlayer()

    coin_amount = 0
    coin_font = pygame.font.SysFont(None, FONT_LARGE)

    # Music button (bottom left)
    music_button = Button(20, SCREEN_HEIGHT - 60, 160, 40, "Music")

    # Music list state
    show_music_list = False
    music_buttons = []

    def rebuild_music_list():
        nonlocal music_buttons
        music_buttons.clear()
        names = music_player.get_song_names()
        print(f"Found songs: {names}")  # debug

        for i, name in enumerate(names):
            # Place list ABOVE the Music button
            y = SCREEN_HEIGHT - 110 - (i * 48)
            btn = Button(20, y, 300, 42, name, font_size=24)
            music_buttons.append(btn)

    rebuild_music_list()

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Toggle music list
            if music_button.is_clicked(event):
                show_music_list = not show_music_list
                print(f"Music list visible: {show_music_list}")

            # Click on a song
            if show_music_list:
                for i, btn in enumerate(music_buttons):
                    if btn.is_clicked(event):
                        music_player.play(i)

        # Update
        music_button.update(mouse_pos)
        if show_music_list:
            for btn in music_buttons:
                btn.update(mouse_pos)

        # Draw
        screen.blit(background, (0, 0))

        # Coin counter (top left)
        coin_text = coin_font.render(f"Coins: {coin_amount}", True, GOLD)
        coin_rect = coin_text.get_rect(topleft=(20, 20))
        bg_rect = coin_rect.inflate(20, 10)
        pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect, border_radius=6)
        screen.blit(coin_text, coin_rect)

        # Music button
        music_button.draw(screen)

        # Music list (drawn on top)
        if show_music_list:
            for btn in music_buttons:
                btn.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    music_player.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()