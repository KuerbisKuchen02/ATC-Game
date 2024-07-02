import pygame

from aircraft import Aircraft, Status


def game():
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption('ATC Controller')

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((50, 50, 50))
    screen.blit(background, (0, 0))
    pygame.display.flip()

    aircraft = pygame.sprite.Group()
    aircraft.add(Aircraft(
        "LH1234",
        (100, (screen.get_height() - 50)*10),
        45,
        0,
        0,
        Status.PARKED))


    font = pygame.font.SysFont("Helvetica", 36)
    font_object = font.render("Rocky Mountain Regional", True, (255, 255, 255))
    background.blit(font_object, (50, 50))
    clock = pygame.time.Clock()
    running = True
    dt = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.blit(background, (0, 0))
        aircraft.update(dt)
        # aircraft.draw(screen)
        pygame.display.flip()
        dt = clock.tick(60) / 1000  # limits FPS to 60

    pygame.quit()


if __name__ == '__main__':
    game()
