# ui.py
import pygame
from constants import *

class Button:
    def __init__(self, x, y, width, height, text, font_size=28, bg_color=DARK_GRAY, text_color=WHITE, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont(None, font_size)
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color if hover_color else tuple(min(c + 30, 255) for c in bg_color)
        self.is_hovered = False

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, LIGHT_GRAY, self.rect, 2, border_radius=8)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def set_text(self, new_text):
        self.text = new_text