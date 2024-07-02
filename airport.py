import pygame
import math

RUNWAY_COLOR = pygame.Color('blue')
TAXI_COLOR = pygame.Color('red')
GATE_COLOR = pygame.Color('green')
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# runway (name, length, orientation)

class Airport:
    def __init__(self, surface: pygame.Surface, name: str, runways: list, taxiways: list, gates: list):
        self.surface = surface
        self.name = name
        self.runways = runways
        self.taxiways = taxiways
        self.gates = gates
        self.font = pygame.font.SysFont("Helvetica", 12)
        self.draw()

    def draw(self):
        # taxiways
        length = 700
        start = (self.surface.get_width() - length) / 2
        pygame.draw.line(self.surface, TAXI_COLOR, (start, 270), (start + length, 270), 15)
        self.draw_round_intersection((start + 6, 204), False, False, True, True)
        self.draw_round_intersection((start + length / 2, 204), False, False, True, True)
        self.draw_round_intersection((start + length - 1, 204), False, False, True, True)

        pygame.draw.line(self.surface, TAXI_COLOR, (start + 25, 350), (start + length - 19, 350), 15)
        # left
        pygame.draw.line(self.surface, TAXI_COLOR, (start + 6, 210), (start + 6, 332), 15)
        self.draw_corner(start + 6, 332, True, True)
        self.draw_round_intersection((start + 6, 270), False, True, False, True)
        # right
        pygame.draw.line(self.surface, TAXI_COLOR, (start + length, 210), (start + length, 332), 15)
        self.draw_corner(start + length, 332, False, True)
        self.draw_round_intersection((start + length - 1, 270), True, False, True, False)
        # center
        pygame.draw.line(self.surface, TAXI_COLOR, (start + length / 2, 210), (start + length / 2, 345), 15)
        self.draw_corner(start + length / 2, 330, True, True)
        self.draw_corner(start + length / 2, 330, False, True)

        self.draw_round_intersection((start + length / 2, 270), True, True, True, True)

        # runways
        self.draw_runway(800, 200, 18)

    def draw_corner(self, start_x, start_y, right: bool, top: bool):
        if right and top:
            pygame.draw.arc(self.surface, TAXI_COLOR,
                            (start_x - 6, start_y - 24, 50, 50),
                            math.pi, 3 * math.pi / 2, 15)
        elif not right and top:
            pygame.draw.arc(self.surface, TAXI_COLOR,
                            (start_x - 42, start_y - 24, 50, 50),
                            3 * math.pi / 2,  2 * math.pi, 15)
        elif right and not top:
            pygame.draw.arc(self.surface, TAXI_COLOR,
                            (start_x - 7, start_y - 7, 50, 50),
                            math.pi / 2, math.pi, 15)
        elif not right and not top:
            pygame.draw.arc(self.surface, TAXI_COLOR,
                            (start_x - 42, start_y - 7, 50, 50),
                            2 * math.pi, math.pi / 2, 15)

    def draw_round_intersection(self, pos, tl: bool, tr: bool, bl: bool, br: bool):
        if tl:
            self.draw_corner(pos[0], pos[1] - 19, False, True)
        if tr:
            self.draw_corner(pos[0], pos[1] - 19, True, True)
        if bl:
            self.draw_corner(pos[0], pos[1] + 2, False, False)
        if br:
            self.draw_corner(pos[0], pos[1] + 2, True, False)

    def draw_runway(self, length, y_pos, orientation):
        start = (self.surface.get_width() - length) / 2
        pygame.draw.line(self.surface, RUNWAY_COLOR, (start, y_pos), (start + length, y_pos), 20)
        text = self.draw_text_box("RWY %d" % orientation)
        self.surface.blit(text, (start, y_pos - text.get_height() / 2))
        text = self.draw_text_box("RWY %d" % (orientation + 18))
        self.surface.blit(text, (start + length, y_pos - text.get_height() / 2))

    def draw_text_box(self, text: str,
                      text_color: tuple[int, int, int] = BLACK,
                      background_color: tuple[int, int, int] = WHITE) -> pygame.Surface:
        text = self.font.render(text, True, text_color)
        text = pygame.transform.rotate(text, 90)
        text_surface = pygame.Surface((text.get_width() + 5, text.get_height() + 5), pygame.SRCALPHA)
        pygame.draw.rect(text_surface, background_color,
                         ((0, 0), (text.get_width() + 5, text.get_height() + 5)),
                         border_radius=5)
        text_surface.blit(text, (2.5, 2.5))
        return text_surface
