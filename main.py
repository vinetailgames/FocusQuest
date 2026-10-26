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

    music_button = Button(20, SCREEN_HEIGHT - 60, 160, 40, "Music")
    quest_button = Button(
        SCREEN_WIDTH - 280, 20, 260, 40, "No Quest",
        wrap=True, auto_height=True
    )
    timer_button = Button(SCREEN_WIDTH // 2 - 90, 20, 180, 50, "Study: 25:00")

    show_music_list = False
    show_quest_window = False
    show_timer_window = False
    music_buttons = []
    creating_quest = False
    editing_index = None
    context_menu = None
    selected_type = "main"

    name_input = InputBox(0, 0, 400, 40)
    study_input = InputBox(0, 0, 80, 36, "25")
    break_input = InputBox(0, 0, 80, 36, "5")

    add_button = Button(0, 0, 140, 40, "+ Add Quest")
    type_main_btn = Button(0, 0, 120, 36, "Main")
    type_side_btn = Button(0, 0, 120, 36, "Side")
    type_task_btn = Button(0, 0, 140, 36, "Task List")
    confirm_btn = Button(0, 0, 120, 40, "Confirm")
    cancel_btn = Button(0, 0, 120, 40, "Cancel")

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
            quest_button.set_text(q.description)
        else:
            quest_button.set_text("No Quest Available")

    def task_panel_top():
        return max(80, quest_button.rect.bottom + 10)

    update_quest_button()

    running = True
    while running:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE:
                quest_manager.reset_all()
                update_quest_button()
                print("All data reset!")

            # Main buttons
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

            if show_music_list:
                for i, btn in enumerate(music_buttons):
                    if btn.is_clicked(event):
                        music_player.play(i)

            # Left click on quest list → select
            if show_quest_window and not creating_quest and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                y = 145
                for i, q in enumerate(quest_manager.quests):
                    rect = pygame.Rect(SCREEN_WIDTH // 2 - 255, y, 510, 30)
                    if rect.collidepoint(event.pos):
                        quest_manager.set_current_quest(i)
                        update_quest_button()
                        break
                    y += 32

            # Right click → context menu
            if show_quest_window and not creating_quest and event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                y = 145
                for i, q in enumerate(quest_manager.quests):
                    rect = pygame.Rect(SCREEN_WIDTH // 2 - 255, y, 510, 30)
                    if rect.collidepoint(event.pos):
                        context_menu = (event.pos[0], event.pos[1], i)
                        break
                    y += 32

            # Context menu actions
            if context_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my, idx = context_menu
                if pygame.Rect(mx, my, 120, 30).collidepoint(event.pos):
                    editing_index = idx
                    name_input.text = quest_manager.quests[idx].task_name
                    name_input.txt_surface = name_input.font.render(name_input.text, True, WHITE)
                    creating_quest = True
                    context_menu = None
                elif pygame.Rect(mx, my + 30, 120, 30).collidepoint(event.pos):
                    quest_manager.delete_quest(idx)
                    update_quest_button()
                    context_menu = None
                else:
                    context_menu = None

            # Quest creation
            if show_quest_window:
                if not creating_quest:
                    if add_button.is_clicked(event):
                        creating_quest = True
                        editing_index = None
                        name_input.text = ""
                        name_input.txt_surface = name_input.font.render("", True, WHITE)
                else:
                    if type_main_btn.is_clicked(event): selected_type = "main"
                    if type_side_btn.is_clicked(event): selected_type = "side"
                    if type_task_btn.is_clicked(event): selected_type = "task_list"
                    result = name_input.handle_event(event)
                    if result == "enter" or confirm_btn.is_clicked(event):
                        if name_input.text.strip():
                            if editing_index is not None:
                                quest_manager.edit_quest(editing_index, name_input.text.strip())
                            else:
                                quest_manager.add_quest(name_input.text.strip(), selected_type)
                            update_quest_button()
                            creating_quest = False
                            editing_index = None
                    if cancel_btn.is_clicked(event):
                        creating_quest = False
                        editing_index = None

            # Clicking tasks in the task list (right panel)
            current = quest_manager.get_current_quest()
            if current and current.quest_type == "task_list" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                y = task_panel_top() + 45
                for i in range(len(current.tasks)):
                    checkbox_rect = pygame.Rect(SCREEN_WIDTH - 260, y, 20, 20)
                    if checkbox_rect.collidepoint(event.pos):
                        quest_manager.complete_task(i)
                        update_quest_button()
                        break
                    y += 32

            # Timer window
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
                    timer.stop()

        # Update timer
        timer.update(dt)
        timer_button.set_text(timer.get_time_str())

        if timer.just_finished:
            if music_player.is_playing:
                music_player.stop()

            if timer.just_finished_study:
                q = quest_manager.get_current_quest()
                if q and (q.quest_type != "task_list" or q.subtype == 2):
                    if q.subtype == 1:
                        earned = quest_manager.add_progress(1)
                    else:
                        earned = quest_manager.add_progress(timer.study_seconds // 60)
                    if earned > 0:
                        print(f"Quest completed! +{earned} coins")
                        update_quest_button()

        # Update hover
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
                confirm_btn.update(mouse_pos)
                cancel_btn.update(mouse_pos)

        if show_timer_window:
            start_timer_btn.update(mouse_pos)
            pause_timer_btn.update(mouse_pos)
            stop_timer_btn.update(mouse_pos)

        # ===== DRAW =====
        screen.blit(background, (0, 0))

        # Coins
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

        # ===== Task List Panel (right side) =====
        current = quest_manager.get_current_quest()
        if current and current.quest_type == "task_list" and current.tasks:
            panel_top = task_panel_top()
            panel = pygame.Rect(SCREEN_WIDTH - 280, panel_top, 260, 420)
            pygame.draw.rect(screen, (20, 20, 30), panel, border_radius=10)
            pygame.draw.rect(screen, LIGHT_GRAY, panel, 2, border_radius=10)

            title = small_font.render("Task List", True, WHITE)
            screen.blit(title, (panel.x + 15, panel.y + 12))

            y = panel_top + 45
            for i, task in enumerate(current.tasks):
                # Checkbox
                checkbox = pygame.Rect(SCREEN_WIDTH - 260, y, 20, 20)
                pygame.draw.rect(screen, WHITE, checkbox, 2)
                label = small_font.render(task, True, WHITE)
                screen.blit(label, (SCREEN_WIDTH - 230, y + 1))
                y += 32

        # ===== Quest Window =====
        if show_quest_window:
            window = pygame.Rect(SCREEN_WIDTH // 2 - 280, 80, 560, 520)
            pygame.draw.rect(screen, (25, 25, 35), window, border_radius=14)
            pygame.draw.rect(screen, LIGHT_GRAY, window, 2, border_radius=14)

            current = quest_manager.get_current_quest()
            if current:
                info = f"Current: {current.description}"
            else:
                info = "No active quest"
            title = normal_font.render(info[:55], True, GOLD)
            screen.blit(title, (window.x + 20, window.y + 12))

            if not creating_quest:
                y = window.y + 55
                for q in quest_manager.quests:
                    status = "✓" if q.completed else "○"
                    color = GREEN if q.completed else WHITE
                    text = f"{status} {q.description}"
                    label = normal_font.render(text[:50], True, color)
                    screen.blit(label, (window.x + 25, y))
                    y += 32

                add_button.rect.topleft = (window.x + 20, window.bottom - 60)
                add_button.draw(screen)
            else:
                label = normal_font.render("Task Name:", True, WHITE)
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

                confirm_btn.rect.topleft = (window.x + 30, window.bottom - 60)
                cancel_btn.rect.topleft = (window.x + 170, window.bottom - 60)
                confirm_btn.draw(screen)
                cancel_btn.draw(screen)

        # Context menu
        if context_menu:
            mx, my, _ = context_menu
            pygame.draw.rect(screen, (40, 40, 50), (mx, my, 120, 60), border_radius=6)
            pygame.draw.rect(screen, LIGHT_GRAY, (mx, my, 120, 60), 1, border_radius=6)
            screen.blit(small_font.render("Edit", True, WHITE), (mx + 15, my + 8))
            screen.blit(small_font.render("Delete", True, WHITE), (mx + 15, my + 35))

        # Timer window
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
