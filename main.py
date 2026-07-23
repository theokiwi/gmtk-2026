import pygame
clock = pygame.time.Clock()

while running:
    dt = min(clock.tick(60) / 1000, 0.05)