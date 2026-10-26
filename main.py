# main.py
import pygame
import sys
import os
from constants import *
from ui import Button, InputBox
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
    normal_font = pygame.font.SysFont(None, 26)

    # Main buttons
    music_button = Button(20, SCREEN_HEIGHT - 60, 160, 40, "Music")
    quest_button = Button(SCREEN_WIDTH - 220, 20, 200, 40, "No Quest")

    # States
    show_music_list = False
    show_quest_window = False
    music_buttons = []

    # Quest creation state
    creating_quest = False
    selected_type = "main"       # main / side / task_list
    selected_subtype = 1         # 1 = pomodoros, 2 = minutes
    name_input = InputBox(0, 0, 400, 40)

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
            text = q.name if len(q.name) <= 20 else q.name[:18] + "..."
            quest_button.set_text(text)
        else:
            quest_button.set_text("No Quest Available")

    update_quest_button()

    # Buttons inside quest window
    add_button = Button(0, 0, 140, 40, "+ Add Quest")
    type_main_btn = Button(0, 0, 120, 36, "Main")
    type_side_btn = Button(0, 0, 120, 36, "Side")
    type_task_btn = Button(0, 0, 140, 36, "Task List")
    sub_pomodoro_btn = Button(0, 0, 140, 36, "Pomodoros")
    sub_minutes_btn = Button(0, 0, 140, 36, "Minutes")
    confirm_btn = Button(0, 0, 120, 40, "Confirm")
    cancel_btn = Button(0, 0, 120, 40, "Cancel")

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Main buttons
            if music_button.is_clicked(event):
                show_music_list = not show_music_list
                show_quest_window = False
                creating_quest = False

            if quest_button.is_clicked(event):
                show_quest_window = not show_quest_window
                show_music_list = False
                creating_quest = False

            # Music list
            if show_music_list:
                for i, btn in enumerate(music_buttons):
                    if btn.is_clicked(event):
                        music_player.play(i)

            # Quest window interactions
            if show_quest_window:
                if not creating_quest:
                    if add_button.is_clicked(event):
                        creating_quest = True
                        name_input.text = ""
                        name_input.txt_surface = name_input.font.render("", True, WHITE)
                else:
                    # Type selection
                    if type_main_btn.is_clicked(event):
                        selected_type = "main"
                    if type_side_btn.is_clicked(event):
                        selected_type = "side"
                    if type_task_btn.is_clicked(event):
                        selected_type = "task_list"

                    # Subtype
                    if sub_pomodoro_btn.is_clicked(event):
                        selected_subtype = 1
                    if sub_minutes_btn.is_clicked(event):
                        selected_subtype = 2

                    # Input
                    result = name_input.handle_event(event)
                    if result == "enter" or confirm_btn.is_clicked(event):
                        if name_input.text.strip():
                            quest_manager.add_quest(
                                name_input.text.strip(),
                                selected_type,
                                selected_subtype
                            )
                            update_quest_button()
                            creating_quest = False
                    if cancel_btn.is_clicked(event):
                        creating_quest = False

        # Update
        music_button.update(mouse_pos)
        quest_button.update(mouse_pos)
        if show_music_list:
            for btn in music_buttons:
                btn.update(mouse_pos)

        if show_quest_window:
            add_button.update(mouse_pos)
            if creating_quest:
                type_main_btn.update(mouse_pos)
                type_side_btn.update(mouse_pos)
                type_task_btn.update(mouse_pos)
                sub_pomodoro_btn.update(mouse_pos)
                sub_minutes_btn.update(mouse_pos)
                confirm_btn.update(mouse_pos)
                cancel_btn.update(mouse_pos)

        # Draw
        screen.blit(background, (0, 0))

        # Coins
        coin_text = coin_font.render(f"Coins: {coin_amount}", True, GOLD)
        coin_rect = coin_text.get_rect(topleft=(20, 20))
        pygame.draw.rect(screen, (0, 0, 0, 180), coin_rect.inflate(20, 10), border_radius=6)
        screen.blit(coin_text, coin_rect)

        quest_button.draw(screen)
        music_button.draw(screen)

        if show_music_list:
            for btn in music_buttons:
                btn.draw(screen)

        # ===== QUEST WINDOW =====
        if show_quest_window:
            window = pygame.Rect(SCREEN_WIDTH//2 - 280, 80, 560, 520)
            pygame.draw.rect(screen, (25, 25, 35), window, border_radius=14)
            pygame.draw.rect(screen, LIGHT_GRAY, window, 2, border_radius=14)

            title = normal_font.render("Quest Manager", True, WHITE)
            screen.blit(title, (window.x + 20, window.y + 15))

            if not creating_quest:
                # List existing quests
                y = window.y + 60
                for q in quest_manager.quests:
                    status = "✓" if q.completed else "○"
                    color = GREEN if q.completed else WHITE
                    text = f"{status} [{q.quest_type}] {q.name}"
                    label = normal_font.render(text[:50], True, color)
                    screen.blit(label, (window.x + 25, y))
                    y += 32

                add_button.rect.topleft = (window.x + 20, window.bottom - 60)
                add_button.draw(screen)
            else:
                # Creation form
                label = normal_font.render("Quest Name:", True, WHITE)
                screen.blit(label, (window.x + 30, window.y + 70))

                name_input.rect.topleft = (window.x + 30, window.y + 100)
                name_input.draw(screen)

                # Type
                label = normal_font.render("Type:", True, WHITE)
                screen.blit(label, (window.x + 30, window.y + 160))

                type_main_btn.rect.topleft = (window.x + 30, window.y + 190)
                type_side_btn.rect.topleft = (window.x + 160, window.y + 190)
                type_task_btn.rect.topleft = (window.x + 290, window.y + 190)

                type_main_btn.bg_color = GOLD if selected_type == "main" else DARK_GRAY
                type_side_btn.bg_color = GOLD if selected_type == "side" else DARK_GRAY
                type_task_btn.bg_color = GOLD if selected_type == "task_list" else DARK_GRAY

                type_main_btn.draw(screen)
                type_side_btn.draw(screen)
                type_task_btn.draw(screen)

                # Subtype
                label = normal_font.render("Goal:", True, WHITE)
                screen.blit(label, (window.x + 30, window.y + 250))

                sub_pomodoro_btn.rect.topleft = (window.x + 30, window.y + 280)
                sub_minutes_btn.rect.topleft = (window.x + 180, window.y + 280)

                sub_pomodoro_btn.bg_color = GOLD if selected_subtype == 1 else DARK_GRAY
                sub_minutes_btn.bg_color = GOLD if selected_subtype == 2 else DARK_GRAY

                sub_pomodoro_btn.draw(screen)
                sub_minutes_btn.draw(screen)

                # Confirm / Cancel
                confirm_btn.rect.topleft = (window.x + 30, window.bottom - 60)
                cancel_btn.rect.topleft = (window.x + 170, window.bottom - 60)
                confirm_btn.draw(screen)
                cancel_btn.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    music_player.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()