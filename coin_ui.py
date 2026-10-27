"""Rendering for the coin counter."""

import pygame
from constants import FONT_LARGE, GOLD


# Change this (x, y) pair to reposition the coin counter on the game canvas.
COIN_UI_POSITION = (102, 24)


class CoinUI:
    def __init__(self, position=COIN_UI_POSITION):
        self.position = position
        self.font = pygame.font.SysFont(None, FONT_LARGE)

    def draw(self, surface, coin_amount):
        coin_text = self.font.render(f"Coins: {coin_amount}", True, GOLD)
        coin_rect = coin_text.get_rect(topleft=self.position)
        pygame.draw.rect(
            surface,
            (0, 0, 0, 180),
            coin_rect.inflate(20, 10),
            border_radius=6
        )
        surface.blit(coin_text, coin_rect)
