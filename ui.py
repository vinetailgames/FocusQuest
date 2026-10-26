# ui.py
import pygame
from constants import *

class Button:
    def __init__(self, x, y, width, height, text, font_size=28, bg_color=DARK_GRAY, text_color=WHITE, hover_color=None, wrap=False, auto_height=False, padding=8):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont(None, font_size)
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color if hover_color else tuple(min(c + 30, 255) for c in bg_color)
        self.is_hovered = False
        self.wrap = wrap
        self.auto_height = auto_height
        self.padding = padding
        self.minimum_height = height
        self._fit_height()

    def _wrapped_lines(self):
        if not self.wrap:
            return [self.text]

        max_width = max(1, self.rect.width - self.padding * 2)
        lines = []
        for paragraph in self.text.split("\n"):
            words = paragraph.split()
            if not words:
                lines.append("")
                continue

            line = ""
            for word in words:
                # Break an unusually long word rather than letting it escape the button.
                while self.font.size(word)[0] > max_width:
                    if line:
                        lines.append(line)
                        line = ""
                    split_at = len(word)
                    while split_at > 1 and self.font.size(word[:split_at])[0] > max_width:
                        split_at -= 1
                    lines.append(word[:split_at])
                    word = word[split_at:]

                test_line = f"{line} {word}" if line else word
                if self.font.size(test_line)[0] <= max_width:
                    line = test_line
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)
        return lines or [""]

    def _fit_height(self):
        if self.auto_height:
            lines = self._wrapped_lines()
            self.rect.height = max(
                self.minimum_height,
                len(lines) * self.font.get_linesize() + self.padding * 2
            )

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        self._fit_height()
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, LIGHT_GRAY, self.rect, 2, border_radius=8)

        lines = self._wrapped_lines()
        line_height = self.font.get_linesize()
        total_height = len(lines) * line_height
        y = self.rect.centery - total_height // 2
        for line in lines:
            text_surf = self.font.render(line, True, self.text_color)
            text_rect = text_surf.get_rect(center=(self.rect.centerx, y + line_height // 2))
            surface.blit(text_surf, text_rect)
            y += line_height

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def set_text(self, new_text):
        self.text = new_text
        self._fit_height()

class InputBox:
    def __init__(self, x, y, width, height, text=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = LIGHT_GRAY
        self.text = text
        self.font = pygame.font.SysFont(None, 28)
        self.active = False
        self.txt_surface = self.font.render(text, True, WHITE)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = GOLD if self.active else LIGHT_GRAY

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return "enter"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 30:
                    self.text += event.unicode
            self.txt_surface = self.font.render(self.text, True, WHITE)
        return None

    def draw(self, surface):
        pygame.draw.rect(surface, (20, 20, 30), self.rect, border_radius=6)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=6)
        surface.blit(self.txt_surface, (self.rect.x + 8, self.rect.y + 8))


class MultilineInputBox:
    def __init__(self, x, y, width, height, text=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = LIGHT_GRAY
        self.text = text
        self.font = pygame.font.SysFont(None, 26)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = GOLD if self.active else LIGHT_GRAY

        if event.type == pygame.KEYDOWN and self.active:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.text += "\n"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
                self.text = ""
            elif event.unicode and event.unicode.isprintable():
                self.text += event.unicode

    def draw(self, surface):
        pygame.draw.rect(surface, (20, 20, 30), self.rect, border_radius=6)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=6)

        viewport = self.rect.inflate(-16, -16)
        previous_clip = surface.get_clip()
        surface.set_clip(viewport)

        lines = self.text.split("\n")
        line_height = self.font.get_linesize()
        visible_rows = max(1, viewport.height // line_height)
        visible_lines = lines[-visible_rows:]
        for index, line in enumerate(visible_lines):
            line_surface = self.font.render(line, True, WHITE)
            surface.blit(line_surface, (viewport.x, viewport.y + index * line_height))

        surface.set_clip(previous_clip)
