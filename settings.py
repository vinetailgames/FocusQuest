"""Quest settings actions and their bottom-right gear menu."""

import math
import random

import pygame

from constants import DARK_GRAY, GOLD, GREEN, LIGHT_GRAY, RED, WHITE


class QuestSettings:
    """Operations that change quest-wide settings or ordering."""

    def __init__(self, quest_manager):
        self.quest_manager = quest_manager

    def toggle_quests_paused(self):
        manager = self.quest_manager
        manager.quests_paused = not manager.quests_paused
        manager.save()
        return manager.quests_paused

    def shuffle_quests(self):
        """Randomize quest order without changing goals or quest categories."""
        manager = self.quest_manager
        if len(manager.quests) < 2:
            return False

        previous_order = tuple(id(quest) for quest in manager.quests)
        random.shuffle(manager.quests)
        if tuple(id(quest) for quest in manager.quests) == previous_order:
            manager.quests[0], manager.quests[1] = manager.quests[1], manager.quests[0]
        manager.save()
        return True

    def reset_quests(self):
        """Make every quest active again and restore its starting progress."""
        manager = self.quest_manager
        for quest in manager.quests:
            quest.completed = False
            quest.progress = 0
            if quest.quest_type == "task_list":
                quest.tasks = list(quest.source_tasks)
        manager.save()

    def delete_all(self):
        """Remove every quest and saved task while preserving the coin balance."""
        manager = self.quest_manager
        manager.quests.clear()
        manager.task_catalog.clear()
        manager.save()


class SettingsMenu:
    """Gear menu and Yes/No confirmations for quest management actions."""

    def __init__(self, quest_window_rect):
        self.quest_window_rect = pygame.Rect(quest_window_rect)
        self.icon_rect = pygame.Rect(
            self.quest_window_rect.right - 64,
            self.quest_window_rect.bottom - 62,
            44,
            44,
        )
        self.popup_rect = pygame.Rect(
            self.quest_window_rect.right - 244,
            self.icon_rect.top - 188 - 10,
            224,
            188,
        )
        self.pause_rect = pygame.Rect(
            self.popup_rect.x + 12, self.popup_rect.y + 34, self.popup_rect.width - 24, 30
        )
        self.shuffle_rect = pygame.Rect(
            self.popup_rect.x + 12, self.popup_rect.y + 69, self.popup_rect.width - 24, 30
        )
        self.reset_rect = pygame.Rect(
            self.popup_rect.x + 12, self.popup_rect.y + 104, self.popup_rect.width - 24, 30
        )
        self.delete_rect = pygame.Rect(
            self.popup_rect.x + 12, self.popup_rect.y + 139, self.popup_rect.width - 24, 30
        )
        self.confirm_rect = pygame.Rect(
            self.quest_window_rect.centerx - 190,
            self.quest_window_rect.centery - 70,
            380,
            140,
        )
        self.yes_rect = pygame.Rect(
            self.confirm_rect.centerx - 105, self.confirm_rect.y + 88, 90, 36
        )
        self.no_rect = pygame.Rect(
            self.confirm_rect.centerx + 15, self.confirm_rect.y + 88, 90, 36
        )
        self.font = pygame.font.SysFont(None, 23)
        self.small_font = pygame.font.SysFont(None, 21)
        self.confirm_font = pygame.font.SysFont(None, 25)
        self.is_open = False
        self.pending_action = None
        self.icon_hovered = False
        self.pause_hovered = False
        self.shuffle_hovered = False
        self.reset_hovered = False
        self.delete_hovered = False
        self.yes_hovered = False
        self.no_hovered = False

    def update(self, mouse_pos, visible=True):
        if not visible:
            self.is_open = False
            self.icon_hovered = False
            self.pause_hovered = False
            self.shuffle_hovered = False
            self.reset_hovered = False
            self.delete_hovered = False
            self.yes_hovered = False
            self.no_hovered = False
            self.pending_action = None
            return
        self.icon_hovered = self.icon_rect.collidepoint(mouse_pos)
        if self.pending_action:
            self.yes_hovered = self.yes_rect.collidepoint(mouse_pos)
            self.no_hovered = self.no_rect.collidepoint(mouse_pos)
            self.pause_hovered = False
            self.shuffle_hovered = False
            self.reset_hovered = False
            self.delete_hovered = False
        else:
            self.pause_hovered = self.is_open and self.pause_rect.collidepoint(mouse_pos)
            self.shuffle_hovered = self.is_open and self.shuffle_rect.collidepoint(mouse_pos)
            self.reset_hovered = self.is_open and self.reset_rect.collidepoint(mouse_pos)
            self.delete_hovered = self.is_open and self.delete_rect.collidepoint(mouse_pos)
            self.yes_hovered = False
            self.no_hovered = False

    def handle_event(self, event, visible=True):
        if not visible:
            self.is_open = False
            self.pending_action = None
            return None
        if self.pending_action:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.pending_action = None
                return "cancel_confirmation"
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                return None
            if self.yes_rect.collidepoint(event.pos):
                action = self.pending_action
                self.pending_action = None
                return f"confirm_{action}"
            if self.no_rect.collidepoint(event.pos):
                self.pending_action = None
                return "cancel_confirmation"
            return "confirmation_inside"

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self.icon_rect.collidepoint(event.pos):
            self.is_open = not self.is_open
            return "toggle"

        if not self.is_open:
            return None

        if self.pause_rect.collidepoint(event.pos):
            self.is_open = False
            return "pause"
        if self.shuffle_rect.collidepoint(event.pos):
            self.is_open = False
            self.pending_action = "shuffle"
            return "confirm_required"
        if self.reset_rect.collidepoint(event.pos):
            self.is_open = False
            self.pending_action = "reset"
            return "confirm_required"
        if self.delete_rect.collidepoint(event.pos):
            self.is_open = False
            self.pending_action = "delete"
            return "confirm_required"
        if self.popup_rect.collidepoint(event.pos):
            return "inside"

        self.is_open = False
        return None

    def _draw_gear(self, surface):
        background = (30, 30, 40)
        border = GOLD if self.icon_hovered or self.is_open else LIGHT_GRAY
        pygame.draw.rect(surface, background, self.icon_rect, border_radius=8)
        pygame.draw.rect(surface, border, self.icon_rect, 2, border_radius=8)

        center = self.icon_rect.center
        gear_points = []
        for tooth in range(8):
            tooth_angle = tooth * 45
            for offset, radius in (
                (-22, 13), (-15, 13), (-15, 18),
                (15, 18), (15, 13), (22, 13),
            ):
                angle = math.radians(tooth_angle + offset)
                gear_points.append((
                    round(center[0] + math.cos(angle) * radius),
                    round(center[1] + math.sin(angle) * radius),
                ))
        pygame.draw.polygon(surface, LIGHT_GRAY, gear_points)
        pygame.draw.circle(surface, background, center, 6)
        pygame.draw.circle(surface, WHITE, center, 6, 1)

    def draw(self, surface, quests_paused, visible=True):
        if not visible:
            return
        self._draw_gear(surface)
        if self.pending_action:
            shade = pygame.Surface(self.quest_window_rect.size, pygame.SRCALPHA)
            shade.fill((0, 0, 0, 150))
            surface.blit(shade, self.quest_window_rect.topleft)

            pygame.draw.rect(surface, (25, 25, 35), self.confirm_rect, border_radius=10)
            pygame.draw.rect(surface, LIGHT_GRAY, self.confirm_rect, 2, border_radius=10)
            prompt = self.confirm_font.render(
                self._confirmation_prompt(), True, WHITE
            )
            surface.blit(prompt, prompt.get_rect(center=(
                self.confirm_rect.centerx, self.confirm_rect.y + 43
            )))
            self._draw_confirmation_option(surface, self.yes_rect, "Yes", GREEN, self.yes_hovered)
            self._draw_confirmation_option(surface, self.no_rect, "No", RED, self.no_hovered)
        elif self.is_open:
            pygame.draw.rect(surface, (25, 25, 35), self.popup_rect, border_radius=10)
            pygame.draw.rect(surface, LIGHT_GRAY, self.popup_rect, 2, border_radius=10)
            heading = self.font.render("Quest Settings", True, GOLD)
            surface.blit(heading, (self.popup_rect.x + 12, self.popup_rect.y + 8))

            self._draw_option(
                surface, self.pause_rect,
                "Start Quests" if quests_paused else "Pause Quests",
                self.pause_hovered,
            )
            self._draw_option(surface, self.shuffle_rect, "Shuffle", self.shuffle_hovered)
            self._draw_option(surface, self.reset_rect, "Reset Quests", self.reset_hovered)
            self._draw_option(surface, self.delete_rect, "Delete All", self.delete_hovered)

    def _confirmation_prompt(self):
        action_text = {
            "shuffle": "shuffle quests",
            "reset": "reset quests",
            "delete": "delete all",
        }[self.pending_action]
        return f"Are you sure you want to {action_text}?"

    def _draw_option(self, surface, rect, label, hovered):
        fill = (75, 75, 88) if hovered else DARK_GRAY
        pygame.draw.rect(surface, fill, rect, border_radius=6)
        pygame.draw.rect(surface, LIGHT_GRAY, rect, 1, border_radius=6)
        text = self.small_font.render(label, True, WHITE)
        surface.blit(text, text.get_rect(center=rect.center))

    def _draw_confirmation_option(self, surface, rect, label, color, hovered):
        fill = tuple(min(channel + 25, 255) for channel in color) if hovered else color
        pygame.draw.rect(surface, fill, rect, border_radius=6)
        pygame.draw.rect(surface, LIGHT_GRAY, rect, 1, border_radius=6)
        text = self.small_font.render(label, True, WHITE)
        surface.blit(text, text.get_rect(center=rect.center))
