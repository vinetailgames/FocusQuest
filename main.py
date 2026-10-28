# main.py
import pygame
import sys
import os
from constants import *
from ui import Button, InputBox, MultilineInputBox
from music_player import MusicPlayer
from quest import QuestManager
from timer import PomodoroTimer
from updater import UpdateService, launch_installer
from coin_ui import CoinUI

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


def to_logical_pos(pos, window_size):
    """Map a window-space mouse position to the fixed game canvas."""
    window_width, window_height = window_size
    if window_width <= 0 or window_height <= 0:
        return 0, 0
    return (
        round(pos[0] * SCREEN_WIDTH / window_width),
        round(pos[1] * SCREEN_HEIGHT / window_height)
    )


def to_logical_event(event, window_size):
    """Translate mouse event coordinates to the fixed game canvas."""
    if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
        return event

    event_data = event.dict.copy()
    if "pos" in event_data:
        event_data["pos"] = to_logical_pos(event_data["pos"], window_size)
    if "rel" in event_data:
        window_width, window_height = window_size
        if window_width > 0 and window_height > 0:
            event_data["rel"] = (
                round(event_data["rel"][0] * SCREEN_WIDTH / window_width),
                round(event_data["rel"][1] * SCREEN_HEIGHT / window_height)
            )
    return pygame.event.Event(event.type, event_data)


def draw_bell_icon(surface, rect, has_announcement):
    pygame.draw.rect(surface, (30, 30, 40), rect, border_radius=8)
    pygame.draw.rect(surface, LIGHT_GRAY, rect, 1, border_radius=8)

    center_x = rect.centerx
    center_y = rect.centery
    bell_color = WHITE
    pygame.draw.ellipse(surface, bell_color, (center_x - 7, center_y - 12, 14, 18))
    pygame.draw.polygon(surface, bell_color, [
        (center_x - 7, center_y - 5),
        (center_x + 7, center_y - 5),
        (center_x + 10, center_y + 8),
        (center_x - 10, center_y + 8)
    ])
    pygame.draw.line(
        surface, (30, 30, 40),
        (center_x - 8, center_y + 5), (center_x + 8, center_y + 5), 2
    )
    pygame.draw.ellipse(surface, bell_color, (center_x - 4, center_y + 7, 8, 4))
    pygame.draw.circle(surface, bell_color, (center_x, center_y - 13), 2)

    if has_announcement:
        dot_center = (rect.right - 2, rect.bottom - 2)
        pygame.draw.circle(surface, RED, dot_center, 6)
        pygame.draw.circle(surface, WHITE, dot_center, 6, 1)


def main():
    pygame.init()
    pygame.mixer.init()
    display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    background = load_background()
    music_player = MusicPlayer()
    quest_manager = QuestManager()
    timer = PomodoroTimer()
    update_service = UpdateService(BASE_DIR)
    update_service.start()

    coin_ui = CoinUI()
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
    quest_list_scroll = 0

    name_input = InputBox(0, 0, 400, 40)
    task_list_input = MultilineInputBox(0, 0, 500, 300)
    study_input = InputBox(0, 0, 80, 36, "25")
    break_input = InputBox(0, 0, 80, 36, "5")

    add_button = Button(0, 0, 140, 40, "+ Add Quest")
    shuffle_button = Button(0, 0, 140, 40, "Shuffle")
    type_main_btn = Button(0, 0, 120, 36, "Main")
    type_side_btn = Button(0, 0, 120, 36, "Side")
    type_task_btn = Button(0, 0, 140, 36, "Task List")
    confirm_btn = Button(0, 0, 120, 40, "Confirm")
    cancel_btn = Button(0, 0, 120, 40, "Cancel")

    start_timer_btn = Button(0, 0, 120, 40, "Start")
    pause_timer_btn = Button(0, 0, 120, 40, "Pause")
    stop_timer_btn = Button(0, 0, 120, 40, "Stop")
    quest_window_rect = pygame.Rect(SCREEN_WIDTH // 2 - 280, 80, 560, 520)
    pause_quests_button = Button(0, 0, 160, 40, "Pause Quests")
    quest_list_visible_rows = 12

    bell_rect = pygame.Rect(20, 18, 40, 40)
    announcements_open = False
    confirm_update_install = False
    update_install_error = None
    announcements_rect = pygame.Rect(
        SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 150, 600, 300
    )
    announcements_close_button = Button(
        announcements_rect.right - 52, announcements_rect.y + 14,
        36, 34, "X", font_size=22
    )
    update_install_button = Button(
        announcements_rect.right - 150, announcements_rect.y + 100,
        120, 40, "Install", font_size=24, bg_color=GREEN
    )
    confirm_yes_button = Button(
        announcements_rect.x + 165, announcements_rect.y + 190,
        110, 40, "Yes", font_size=24, bg_color=GREEN
    )
    confirm_no_button = Button(
        announcements_rect.x + 325, announcements_rect.y + 190,
        110, 40, "No", font_size=24, bg_color=RED
    )

    def quest_list_row_rect(visible_index):
        row_y = quest_window_rect.y + 55 + visible_index * 32
        return pygame.Rect(quest_window_rect.x + 25, row_y, 510, 30)

    def max_quest_list_scroll():
        return max(0, len(quest_manager.quests) - quest_list_visible_rows)

    def rebuild_music_list():
        nonlocal music_buttons
        music_buttons.clear()
        for i, name in enumerate(music_player.get_song_names()):
            y = SCREEN_HEIGHT - 110 - (i * 48)
            music_buttons.append(Button(20, y, 300, 42, name, font_size=24))

    rebuild_music_list()

    def update_quest_button():
        if quest_manager.quests_paused:
            quest_button.set_text("Quests paused")
        else:
            q = quest_manager.get_current_quest()
            if q:
                quest_button.set_text(q.description)
            else:
                quest_button.set_text("No Quest Available")

    def update_pause_quests_button():
        pause_quests_button.set_text(
            "Start Quests" if quest_manager.quests_paused else "Pause Quests"
        )

    def task_panel_top():
        return max(80, quest_button.rect.bottom + 10)

    update_quest_button()
    update_pause_quests_button()

    running = True
    while running:
        dt = clock.tick(FPS)
        mouse_pos = to_logical_pos(pygame.mouse.get_pos(), display.get_size())

        for raw_event in pygame.event.get():
            if raw_event.type == getattr(pygame, "VIDEORESIZE", -1):
                new_size = (raw_event.w, raw_event.h)
            elif raw_event.type in (
                getattr(pygame, "WINDOWRESIZED", -1),
                getattr(pygame, "WINDOWSIZECHANGED", -1)
            ):
                new_size = (raw_event.x, raw_event.y)
            else:
                new_size = None

            if new_size and min(new_size) > 0 and new_size != display.get_size():
                display = pygame.display.set_mode(new_size, pygame.RESIZABLE)
                mouse_pos = to_logical_pos(pygame.mouse.get_pos(), display.get_size())
                continue

            event = to_logical_event(raw_event, display.get_size())
            context_menu_was_open = context_menu is not None
            if event.type == pygame.QUIT:
                running = False
                continue

            if announcements_open:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    announcements_open = False
                    confirm_update_install = False
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if confirm_update_install:
                        if confirm_yes_button.is_clicked(event):
                            snapshot = update_service.snapshot()
                            version = snapshot["available_version"]
                            commit = snapshot["available_commit"]
                            asset_url = snapshot.get("available_asset_url")
                            try:
                                launch_installer(
                                    BASE_DIR, version, commit, asset_url
                                )
                                update_service.stop()
                                running = False
                            except Exception as error:
                                update_install_error = str(error)
                        elif confirm_no_button.is_clicked(event):
                            confirm_update_install = False
                    elif announcements_close_button.is_clicked(event):
                        announcements_open = False
                    elif update_install_button.is_clicked(event):
                        confirm_update_install = True
                        update_install_error = None
                continue

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and bell_rect.collidepoint(event.pos)
            ):
                announcements_open = True
                update_service.request_check()
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE:
                quest_manager.reset_all()
                update_quest_button()
                update_pause_quests_button()
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
            if show_quest_window and not creating_quest and context_menu is None and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for visible_index in range(quest_list_visible_rows):
                    quest_index = quest_list_scroll + visible_index
                    if quest_index >= len(quest_manager.quests):
                        break
                    if quest_list_row_rect(visible_index).collidepoint(event.pos):
                        quest_manager.set_current_quest(quest_index)
                        update_quest_button()
                        break

            # Right click → context menu
            if show_quest_window and not creating_quest and event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                for visible_index in range(quest_list_visible_rows):
                    quest_index = quest_list_scroll + visible_index
                    if quest_index >= len(quest_manager.quests):
                        break
                    if quest_list_row_rect(visible_index).collidepoint(event.pos):
                        context_menu = (event.pos[0], event.pos[1], quest_manager.quests[quest_index])
                        break

            if show_quest_window and not creating_quest and event.type == pygame.MOUSEWHEEL:
                if quest_window_rect.collidepoint(mouse_pos):
                    quest_list_scroll = max(
                        0,
                        min(max_quest_list_scroll(), quest_list_scroll - event.y * 3)
                    )

            # Context menu actions
            if context_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my, selected_quest = context_menu
                idx = next(
                    (i for i, quest in enumerate(quest_manager.quests) if quest is selected_quest),
                    None
                )
                if idx is None:
                    context_menu = None
                elif pygame.Rect(mx, my, 120, 30).collidepoint(event.pos):
                    editing_index = idx
                    selected_type = selected_quest.quest_type
                    if selected_type == "task_list":
                        task_list_input.text = "\n".join(quest_manager.task_catalog)
                        task_list_input.active = False
                        task_list_input.color = LIGHT_GRAY
                    else:
                        name_input.text = selected_quest.task_name
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
                    if not context_menu_was_open and pause_quests_button.is_clicked(event):
                        quest_manager.toggle_quests_paused()
                        update_quest_button()
                        update_pause_quests_button()
                    elif not context_menu_was_open and shuffle_button.is_clicked(event):
                        quest_manager.shuffle_quests()
                        update_quest_button()
                    elif not context_menu_was_open and add_button.is_clicked(event):
                        creating_quest = True
                        editing_index = None
                        name_input.text = ""
                        name_input.txt_surface = name_input.font.render("", True, WHITE)
                        task_list_input.text = ""
                        task_list_input.active = False
                        task_list_input.color = LIGHT_GRAY
                else:
                    if editing_index is None:
                        if type_main_btn.is_clicked(event): selected_type = "main"
                        if type_side_btn.is_clicked(event): selected_type = "side"
                        if type_task_btn.is_clicked(event): selected_type = "task_list"

                    result = None
                    if selected_type == "task_list":
                        task_list_input.handle_event(event)
                    else:
                        result = name_input.handle_event(event)

                    if result == "enter" or confirm_btn.is_clicked(event):
                        if selected_type == "task_list":
                            task_names = [line.strip() for line in task_list_input.text.splitlines() if line.strip()]
                            if editing_index is not None:
                                quest_manager.replace_task_catalog(task_names)
                                update_quest_button()
                                creating_quest = False
                                editing_index = None
                            elif task_names:
                                quest_manager.add_task_list(task_names)
                                update_quest_button()
                                creating_quest = False
                        elif name_input.text.strip():
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
                        task_list_input.active = False
                        task_list_input.color = LIGHT_GRAY

            # Clicking tasks in the task list (right panel)
            current = quest_manager.get_current_quest()
            if not quest_manager.quests_paused and current and current.quest_type == "task_list" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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

            if timer.just_finished_study and not quest_manager.quests_paused:
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
            if creating_quest:
                type_main_btn.update(mouse_pos)
                type_side_btn.update(mouse_pos)
                type_task_btn.update(mouse_pos)
                confirm_btn.update(mouse_pos)
                cancel_btn.update(mouse_pos)
            else:
                add_button.update(mouse_pos)
                shuffle_button.update(mouse_pos)
                pause_quests_button.update(mouse_pos)

        if show_timer_window:
            start_timer_btn.update(mouse_pos)
            pause_timer_btn.update(mouse_pos)
            stop_timer_btn.update(mouse_pos)

        if announcements_open:
            announcements_close_button.update(mouse_pos)
            update_install_button.update(mouse_pos)
            confirm_yes_button.update(mouse_pos)
            confirm_no_button.update(mouse_pos)

        # ===== DRAW =====
        screen.blit(background, (0, 0))

        coin_ui.draw(screen, quest_manager.coin_amount)

        update_snapshot = update_service.snapshot()
        draw_bell_icon(
            screen, bell_rect,
            update_snapshot["available_version"] is not None
        )

        quest_button.draw(screen)
        timer_button.draw(screen)
        music_button.draw(screen)

        if show_music_list:
            for btn in music_buttons:
                btn.draw(screen)

        # ===== Task List Panel (right side) =====
        current = quest_manager.get_current_quest()
        if not quest_manager.quests_paused and current and current.quest_type == "task_list" and current.tasks:
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
            window = quest_window_rect
            pygame.draw.rect(screen, (25, 25, 35), window, border_radius=14)
            pygame.draw.rect(screen, LIGHT_GRAY, window, 2, border_radius=14)

            current = quest_manager.get_current_quest()
            if quest_manager.quests_paused:
                info = "Quests paused"
            elif current:
                info = f"Current: {current.description}"
            else:
                info = "No active quest"
            title = normal_font.render(info[:55], True, GOLD)
            screen.blit(title, (window.x + 20, window.y + 12))

            if not creating_quest:
                quest_list_scroll = min(quest_list_scroll, max_quest_list_scroll())
                for visible_index in range(quest_list_visible_rows):
                    quest_index = quest_list_scroll + visible_index
                    if quest_index >= len(quest_manager.quests):
                        break
                    q = quest_manager.quests[quest_index]
                    status = "✓" if q.completed else "○"
                    color = GREEN if q.completed else WHITE
                    text = f"{status} {q.description}"
                    label = normal_font.render(text[:50], True, color)
                    screen.blit(label, quest_list_row_rect(visible_index).topleft)

                if len(quest_manager.quests) > quest_list_visible_rows:
                    track = pygame.Rect(window.right - 14, window.y + 55, 5, quest_list_visible_rows * 32 - 2)
                    thumb_height = max(24, track.height * quest_list_visible_rows // len(quest_manager.quests))
                    scroll_range = max_quest_list_scroll()
                    thumb_offset = (track.height - thumb_height) * quest_list_scroll // scroll_range
                    thumb = pygame.Rect(track.x, track.y + thumb_offset, track.width, thumb_height)
                    pygame.draw.rect(screen, (80, 80, 90), track, border_radius=3)
                    pygame.draw.rect(screen, LIGHT_GRAY, thumb, border_radius=3)

                add_button.rect.topleft = (window.x + 20, window.bottom - 60)
                pause_quests_button.rect.topleft = (
                    window.centerx - pause_quests_button.rect.width // 2,
                    window.bottom - 60
                )
                shuffle_button.rect.topleft = (window.right - 160, window.bottom - 60)
                add_button.draw(screen)
                pause_quests_button.draw(screen)
                shuffle_button.draw(screen)
            else:
                label = normal_font.render("Type:", True, WHITE)
                screen.blit(label, (window.x + 30, window.y + 45))

                type_main_btn.rect.topleft = (window.x + 30, window.y + 70)
                type_side_btn.rect.topleft = (window.x + 160, window.y + 70)
                type_task_btn.rect.topleft = (window.x + 290, window.y + 70)

                type_main_btn.bg_color = GOLD if selected_type == "main" else DARK_GRAY
                type_side_btn.bg_color = GOLD if selected_type == "side" else DARK_GRAY
                type_task_btn.bg_color = GOLD if selected_type == "task_list" else DARK_GRAY

                type_main_btn.draw(screen)
                type_side_btn.draw(screen)
                type_task_btn.draw(screen)

                if selected_type == "task_list":
                    label = normal_font.render("Tasks (one task per line; Enter starts a new line):", True, WHITE)
                    screen.blit(label, (window.x + 30, window.y + 112))
                    task_list_input.rect.topleft = (window.x + 30, window.y + 140)
                    task_list_input.rect.size = (500, 300)
                    task_list_input.draw(screen)
                else:
                    label = normal_font.render("Task Name:", True, WHITE)
                    screen.blit(label, (window.x + 30, window.y + 130))
                    name_input.rect.topleft = (window.x + 30, window.y + 160)
                    name_input.draw(screen)

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

        if announcements_open:
            shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 165))
            screen.blit(shade, (0, 0))

            pygame.draw.rect(
                screen, (25, 25, 35), announcements_rect, border_radius=14
            )
            pygame.draw.rect(
                screen, LIGHT_GRAY, announcements_rect, 2, border_radius=14
            )
            title = normal_font.render("Announcements", True, GOLD)
            screen.blit(title, (announcements_rect.x + 28, announcements_rect.y + 22))

            if confirm_update_install:
                prompt = small_font.render(
                    "Do you want to install latest version now?", True, WHITE
                )
                screen.blit(prompt, prompt.get_rect(center=(
                    announcements_rect.centerx, announcements_rect.y + 125
                )))
                confirm_yes_button.draw(screen)
                confirm_no_button.draw(screen)
                if update_install_error:
                    error_text = small_font.render(
                        "Could not start the updater.", True, RED
                    )
                    screen.blit(error_text, error_text.get_rect(center=(
                        announcements_rect.centerx, announcements_rect.bottom - 28
                    )))
            elif update_snapshot["connection_available"] is None:
                message = "Checking for announcements..."
                message_surface = normal_font.render(message, True, WHITE)
                screen.blit(message_surface, (
                    announcements_rect.x + 30, announcements_rect.y + 112
                ))
            elif not update_snapshot["connection_available"]:
                message = "Connection required for announcements"
                message_surface = normal_font.render(message, True, WHITE)
                screen.blit(message_surface, (
                    announcements_rect.x + 30, announcements_rect.y + 112
                ))
            elif update_snapshot["check_error"]:
                message = "GitHub announcements are unavailable"
                message_surface = normal_font.render(message, True, WHITE)
                screen.blit(message_surface, (
                    announcements_rect.x + 30, announcements_rect.y + 112
                ))
            elif update_snapshot["available_version"]:
                message = (
                    f"Update {update_snapshot['available_version']} "
                    "is ready to install"
                )
                message_surface = small_font.render(message, True, WHITE)
                screen.blit(message_surface, (
                    announcements_rect.x + 30, announcements_rect.y + 112
                ))
                update_install_button.draw(screen)
            else:
                message = "No announcements available"
                message_surface = normal_font.render(message, True, WHITE)
                screen.blit(message_surface, (
                    announcements_rect.x + 30, announcements_rect.y + 112
                ))

            announcements_close_button.draw(screen)

        display.blit(pygame.transform.smoothscale(screen, display.get_size()), (0, 0))
        pygame.display.flip()

    update_service.stop()
    music_player.stop()
    timer.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
