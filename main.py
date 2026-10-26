# main.py
import pygame
import sys
import os
from constants import *
from ui import Button
from music_player import MusicPlayer
from quest import QuestManager

def load_background():
    try:
        if os.path.exists(BACKGROUND_PATH):
            img = pygame.image.load(BACKGROUND_PATH).convert()
            return pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
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
    quest_manager = QuestManager()

    coin_amount = 0
    coin_font = pygame.font.SysFont(None, FONT_LARGE)
    normal_font = pygame.font.SysFont(None, 28)

    # Buttons
    music_button = Button(20, SCREEN_HEIGHT - 60, 160, 40, "Music")
    quest_button = Button(SCREEN_WIDTH - 220, 20, 200, 40, "No Quest")

    # States
    show_music_list = False
    show_quest_window = False
    music_buttons = []

    def rebuild_music_list():
        nonlocal music_buttons
        music_buttons.clear()
        for i, name in enumerate(music_player.get_song_names()):
            y = SCREEN_HEIGHT - 110 - (i * 48)
            music_buttons.append(Button(20, y, 300, 42, name, font_size=24))

    rebuild_music_list()

    def update_quest_button():
        q = quest_manager.get_current_quest()
        if q:
            quest_button.set_text(q.name[:22] + "..." if len(q.name) > 22 else q.name)
        else:
            quest_button.set_text("No Quest Available")

    update_quest_button()

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if music_button.is_clicked(event):
                show_music_list = not show_music_list
                show_quest_window = False

            if quest_button.is_clicked(event):
                show_quest_window = not show_quest_window
                show_music_list = False

            if show_music_list:
                for i, btn in enumerate(music_buttons):
                    if btn.is_clicked(event):
                        music_player.play(i)

        # Update
        music_button.update(mouse_pos)
        quest_button.update(mouse_pos)
        if show_music_list:
            for btn in music_buttons:
                btn.update(mouse_pos)

        # Draw
        screen.blit(background, (0, 0))

        # Coins (top left)
        coin_text = coin_font.render(f"Coins: {coin_amount}", True, GOLD)
        coin_rect = coin_text.get_rect(topleft=(20, 20))
        pygame.draw.rect(screen, (0, 0, 0, 180), coin_rect.inflate(20, 10), border_radius=6)
        screen.blit(coin_text, coin_rect)

        # Quest button (top right)
        quest_button.draw(screen)

        # Music button
        music_button.draw(screen)

        if show_music_list:
            for btn in music_buttons:
                btn.draw(screen)

        # Simple Quest Window (placeholder for now)
        if show_quest_window:
            window_rect = pygame.Rect(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 180, 500, 360)
            pygame.draw.rect(screen, (30, 30, 40), window_rect, border_radius=12)
            pygame.draw.rect(screen, LIGHT_GRAY, window_rect, 2, border_radius=12)

            title = normal_font.render("Quest Manager (coming in next step)", True, WHITE)
            screen.blit(title, (window_rect.x + 20, window_rect.y + 20))

            close_text = normal_font.render("Click Quest button again to close", True, LIGHT_GRAY)
            screen.blit(close_text, (window_rect.x + 20, window_rect.y + 60))

        pygame.display.flip()
        clock.tick(FPS)

    music_player.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()