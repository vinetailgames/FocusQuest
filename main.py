# main.py
import pygame
import sys
import os
from constants import *
from ui import Button

def load_background():
    """Safely load background. Falls back to solid color if file is missing."""
    try:
        if os.path.exists(BACKGROUND_PATH):
            img = pygame.image.load(BACKGROUND_PATH).convert()
            return pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            print(f"Background not found at {BACKGROUND_PATH}. Using fallback.")
    except Exception as e:
        print(f"Error loading background: {e}")

    # Fallback surface
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surface.fill(DARK_GRAY)
    return surface

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Load background safely
    background = load_background()

    # Game state
    coin_amount = 0

    # Fonts
    coin_font = pygame.font.SysFont(None, FONT_LARGE)

    # Example button (we'll use this pattern later for music/quest/timer)
    # For now just a placeholder so the structure is ready
    test_button = Button(20, SCREEN_HEIGHT - 60, 160, 40, "Music")

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if test_button.is_clicked(event):
                print("Music button clicked (placeholder)")

        # Update
        test_button.update(mouse_pos)

        # Draw
        screen.blit(background, (0, 0))

        # Coin counter (top right)
        coin_text = coin_font.render(f"Coins: {coin_amount}", True, GOLD)
        coin_rect = coin_text.get_rect(topleft=(20, 20))
        # Small background for readability
        bg_rect = coin_rect.inflate(20, 10)
        pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect, border_radius=6)
        screen.blit(coin_text, coin_rect)

        # Draw button
        test_button.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()