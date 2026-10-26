# main.py
import pygame
import sys
import os
from constants import *
from ui import Button, InputBox
from music_player import MusicPlayer
from quest import QuestManager
from timer import PomodoroTimer

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
    timer = PomodoroTimer()

    coin_font = pygame.font.SysFont(None, FONT_LARGE)
    normal_font = pygame.font.SysFont(None, 26)
    small_font = pygame.font.SysFont(None, 22)

    # Main buttons
    music_button = Button(20, SCREEN_HEIGHT - 60, 160, 40, "Music")
    quest_button = Button(SCREEN_WIDTH - 220, 20, 200, 40, "No Quest")
    timer_button = Button(SCREEN_WIDTH // 2 - 90, 20, 180, 50, "25:00")

    # States
    show_music_list = False
    show_quest_window = False
    show_timer_window = False
    music_buttons = []
    creating_quest = False
    editing_index = None
    context_menu = None          # (x, y, index)
    selected_type = "main"
    selected_subtype = 1

    name_input = InputBox(0, 0, 400, 40)
    study_input = InputBox(0, 0, 80, 36, "25")
    break_input = InputBox(0, 0, 80, 36, "5")

    # Quest window buttons
    add_button = Button(0, 0, 140, 40, "+ Add Quest")
    type_main_btn = Button(0, 0, 120, 36, "Main")
    type_side_btn = Button(0, 0, 120, 36, "Side")
    type_task_btn = Button(0, 0, 140, 36, "Task List")
    sub_pomodoro_btn = Button(0, 0, 140, 36, "Pomodoros")
    sub_minutes_btn = Button(0, 0, 140, 36, "Minutes")
    confirm_btn = Button(0, 0, 120, 40, "Confirm")
    cancel_btn = Button(0, 0, 120, 40, "Cancel")

    # Timer window buttons
    start_timer_btn = Button(0, 0, 120, 40, "Start")
    pause_timer_btn = Button(0, 0, 120, 40, "Pause")
    stop_timer_btn = Button(0, 0, 120, 40, "Stop")

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
            text = q.name if len(q.name) <= 18 else q.name[:16] + "..."
            quest_button.set_text(text)
        else:
            quest_button.set_text("No Quest Available")

    update_quest_button()

    running = True
    while running:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Resume music after alarm
            if event.type == pygame.USEREVENT + 1:
                pygame.mixer.music.unpause()
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)

            # Hold Delete to reset everything
            if event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE:
                quest_manager.reset_all()
                update_quest_button()
                print("All data reset!")

            # ===== Main buttons =====
            if music_button.is_clicked(event):
                show_music_list = not show_music_list
                show_quest_window = False
                show_timer_window = False
                creating_quest = False
                context_menu = None

            if quest_button.is_clicked(event):
                show_quest_window = not show_quest_window
                show_music_list = False
                show_timer_window = False
                creating_quest = False
                context_menu = None

            if timer_button.is_clicked(event):
                show_timer_window = not show_timer_window
                show_music_list = False
                show_quest_window = False
                creating_quest = False
                context_menu = None

            # Music list
            if show_music_list:
                for i, btn in enumerate(music_buttons):
                    if btn.is_clicked(event):
                        music_player.play(i)

            # ===== Quest list interactions =====
            if show_quest_window and not creating_quest:
                # Left click → select quest as current
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    y = 140
                    for i, q in enumerate(quest_manager.quests):
                        rect = pygame.Rect(SCREEN_WIDTH // 2 - 255, y, 500, 30)
                        if rect.collidepoint(event.pos):
                            quest_manager.set_current_quest(i)
                            update_quest_button()
                            break
                        y += 32

                # Right click → context menu
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    y = 140
                    for i, q in enumerate(quest_manager.quests):
                        rect = pygame.Rect(SCREEN_WIDTH // 2 - 255, y, 500, 30)
                        if rect.collidepoint(event.pos):
                            context_menu = (event.pos[0], event.pos[1], i)
                            break
                        y += 32

            # Context menu actions
            if context_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my, idx = context_menu
                if pygame.Rect(mx, my, 120, 30).collidepoint(event.pos):
                    # Edit
                    editing_index = idx
                    name_input.text = quest_manager.quests[idx].name
                    name_input.txt_surface = name_input.font.render(name_input.text, True, WHITE)
                    creating_quest = True
                    context_menu = None
                elif pygame.Rect(mx, my + 30, 120, 30).collidepoint(event.pos):
                    # Delete
                    quest_manager.delete_quest(idx)
                    update_quest_button()
                    context_menu = None
                else:
                    context_menu = None

            # ===== Quest creation / editing =====
            if show_quest_window:
                if not creating_quest:
                    if add_button.is_clicked(event):
                        creating_quest = True
                        editing_index = None
                        name_input.text = ""
                        name_input.txt_surface = name_input.font.render("", True, WHITE)
                else:
                    if type_main_btn.is_clicked(event):
                        selected_type = "main"
                    if type_side_btn.is_clicked(event):
                        selected_type = "side"
                    if type_task_btn.is_clicked(event):
                        selected_type = "task_list"
                    if sub_pomodoro_btn.is_clicked(event):
                        selected_subtype = 1
                    if sub_minutes_btn.is_clicked(event):
                        selected_subtype = 2

                    result = name_input.handle_event(event)
                    if result == "enter" or confirm_btn.is_clicked(event):
                        if name_input.text.strip():
                            if editing_index is not None:
                                quest_manager.edit_quest(editing_index, name_input.text.strip())
                            else:
                                quest_manager.add_quest(
                                    name_input.text.strip(),
                                    selected_type,
                                    selected_subtype
                                )
                            update_quest_button()
                            creating_quest = False
                            editing_index = None
                    if cancel_btn.is_clicked(event):
                        creating_quest = False
                        editing_index = None

            # ===== Timer window =====
            if show_timer_window:
                study_input.handle_event(event)
                break_input.handle_event(event)

                if start_timer_btn.is_clicked(event):
                    try:
                        s = int(study_input.text)
                        b = int(break_input.text)
                        timer.set_times(s, b)
                        timer.start()
                        show_timer_window = False
                    except ValueError:
                        pass

                if pause_timer_btn.is_clicked(event):
                    if timer.paused:
                        timer.resume()
                    else:
                        timer.pause()

                if stop_timer_btn.is_clicked(event):
                    timer.stop()   # no alarm

        # ===== Update timer =====
        timer.update(dt)
        timer_button.set_text(timer.get_time_str())

        # Reward when study session finishes
        if timer.just_finished and not timer.is_break:
            q = quest_manager.get_current_quest()
            if q:
                if q.subtype == 1:  # pomodoros
                    earned = quest_manager.add_progress(1)
                else:               # minutes
                    earned = quest_manager.add_progress(timer.study_seconds // 60)
                if earned > 0:
                    print(f"Quest completed! +{earned} coins")
                    update_quest_button()

        # ===== Update UI hover =====
        music_button.update(mouse_pos)
        quest_button.update(mouse_pos)
        timer_button.update(mouse_pos)

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

        if show_timer_window:
            start_timer_btn.update(mouse_pos)
            pause_timer_btn.update(mouse_pos)
            stop_timer_btn.update(mouse_pos)

        # ===== DRAW =====
        screen.blit(background, (0, 0))

        # Coins (top left)
        coin_text = coin_font.render(f"Coins: {quest_manager.coin_amount}", True, GOLD)
        coin_rect = coin_text.get_rect(topleft=(20, 20))
        pygame.draw.rect(screen, (0, 0, 0, 180), coin_rect.inflate(20, 10), border_radius=6)
        screen.blit(coin_text, coin_rect)

        quest_button.draw(screen)
        timer_button.draw(screen)
        music_button.draw(screen)

        if show_music_list:
            for btn in music_buttons:
                btn.draw(screen)

        # Task list panel (right side)
        current = quest_manager.get_current_quest()
        if current and current.quest_type == "task_list":
            panel = pygame.Rect(SCREEN_WIDTH - 280, 80, 260, 400)
            pygame.draw.rect(screen, (20, 20, 30), panel, border_radius=10)
            pygame.draw.rect(screen, LIGHT_GRAY, panel, 2, border_radius=10)
            title = small_font.render("Task List", True, WHITE)
            screen.blit(title, (panel.x + 15, panel.y + 10))
            y = panel.y + 45
            for task in current.tasks:
                label = small_font.render(f"• {task}", True, WHITE)
                screen.blit(label, (panel.x + 15, y))
                y += 28

        # ===== Quest Window =====
        if show_quest_window:
            window = pygame.Rect(SCREEN_WIDTH // 2 - 280, 80, 560, 520)
            pygame.draw.rect(screen, (25, 25, 35), window, border_radius=14)
            pygame.draw.rect(screen, LIGHT_GRAY, window, 2, border_radius=14)

            # Show full current quest info
            current = quest_manager.get_current_quest()
            if current:
                info = f"Current: {current.name}  ({current.progress}/{current.target_value})"
            else:
                info = "No active quest"
            title = normal_font.render(info, True, GOLD)
            screen.blit(title, (window.x + 20, window.y + 12))

            if not creating_quest:
                y = window.y + 55
                for i, q in enumerate(quest_manager.quests):
                    status = "✓" if q.completed else "○"
                    color = GREEN if q.completed else WHITE
                    text = f"{status} [{q.quest_type}] {q.name}"
                    label = normal_font.render(text[:48], True, color)
                    screen.blit(label, (window.x + 25, y))
                    y += 32

                add_button.rect.topleft = (window.x + 20, window.bottom - 60)
                add_button.draw(screen)
            else:
                label = normal_font.render("Quest Name:", True, WHITE)
                screen.blit(label, (window.x + 30, window.y + 70))
                name_input.rect.topleft = (window.x + 30, window.y + 100)
                name_input.draw(screen)

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

                label = normal_font.render("Goal:", True, WHITE)
                screen.blit(label, (window.x + 30, window.y + 250))

                sub_pomodoro_btn.rect.topleft = (window.x + 30, window.y + 280)
                sub_minutes_btn.rect.topleft = (window.x + 180, window.y + 280)

                sub_pomodoro_btn.bg_color = GOLD if selected_subtype == 1 else DARK_GRAY
                sub_minutes_btn.bg_color = GOLD if selected_subtype == 2 else DARK_GRAY

                sub_pomodoro_btn.draw(screen)
                sub_minutes_btn.draw(screen)

                confirm_btn.rect.topleft = (window.x + 30, window.bottom - 60)
                cancel_btn.rect.topleft = (window.x + 170, window.bottom - 60)
                confirm_btn.draw(screen)
                cancel_btn.draw(screen)

        # Context menu (Edit / Delete)
        if context_menu:
            mx, my, _ = context_menu
            pygame.draw.rect(screen, (40, 40, 50), (mx, my, 120, 60), border_radius=6)
            pygame.draw.rect(screen, LIGHT_GRAY, (mx, my, 120, 60), 1, border_radius=6)
            edit_label = small_font.render("Edit", True, WHITE)
            del_label = small_font.render("Delete", True, WHITE)
            screen.blit(edit_label, (mx + 15, my + 8))
            screen.blit(del_label, (mx + 15, my + 35))

        # ===== Timer Window =====
        if show_timer_window:
            window = pygame.Rect(SCREEN_WIDTH // 2 - 190, 120, 380, 300)
            pygame.draw.rect(screen, (25, 25, 35), window, border_radius=14)
            pygame.draw.rect(screen, LIGHT_GRAY, window, 2, border_radius=14)

            title = normal_font.render("Pomodoro Timer", True, WHITE)
            screen.blit(title, (window.x + 20, window.y + 15))

            label = normal_font.render("Study (min):", True, WHITE)
            screen.blit(label, (window.x + 30, window.y + 70))
            study_input.rect.topleft = (window.x + 160, window.y + 65)
            study_input.draw(screen)

            label = normal_font.render("Break (min):", True, WHITE)
            screen.blit(label, (window.x + 30, window.y + 120))
            break_input.rect.topleft = (window.x + 160, window.y + 115)
            break_input.draw(screen)

            start_timer_btn.rect.topleft = (window.x + 30, window.y + 180)
            pause_timer_btn.rect.topleft = (window.x + 160, window.y + 180)
            stop_timer_btn.rect.topleft = (window.x + 30, window.y + 240)

            start_timer_btn.draw(screen)
            pause_timer_btn.draw(screen)
            stop_timer_btn.draw(screen)

        pygame.display.flip()

    music_player.stop()
    timer.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()