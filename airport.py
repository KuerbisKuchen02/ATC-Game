import pygame
import math

from ground_map import GroundMap, Waypoint

RUNWAY_COLOR = (70, 70, 70)  # pygame.Color('blue')
TAXI_COLOR = (100, 100, 100)  # pygame.Color('red')
GATE_COLOR = (120, 120, 120)  # pygame.Color('green')
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SIZE = 700


# runway (name, length, orientation)
class Gate:
    def __init__(self, x: int, y: int, name: str):
        self.x: int = x
        self.y: int = y
        self.name: str = name
        self.text_box = draw_text_box(name)
        self.is_occupied: bool = False

    def get_spawn_point(self) -> tuple[int, int]:
        return int(self.x + self.text_box.get_width() / 2), self.y - 10


class Airport:
    def __init__(self, surface: pygame.Surface, name: str):
        self.surface = surface
        self.name = name
        self.runways = []
        self.taxiways = []
        self.gates = []
        self.aircraft = []
        self.ground_map = GroundMap()
        self.draw()

    def add_aircraft(self, aircraft):
        self.aircraft.append(aircraft)

    def number_of_landing_aircraft(self):
        cnt = 0
        for aircraft in self.aircraft:
            if aircraft.is_landing():
                cnt += 1
        return cnt

    def update(self, *args):
        for aircraft in self.aircraft:
            aircraft.update(*args)

    def draw(self):
        length = 700
        start = (self.surface.get_width() - length) / 2

        # gate
        pygame.draw.rect(self.surface, GATE_COLOR, (start + 100, 347, length - 200, 100))
        # taxiways
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
        # diagonal
        pygame.draw.line(self.surface, TAXI_COLOR, (start + length / 4, 210), (start + length / 6, 270), 20)
        self.draw_corner(start + length / 4 - 10, 205, False, False)
        self.draw_corner(start + length / 6 + 15, 251, True, True)
        pygame.draw.line(self.surface, TAXI_COLOR, (start + 3 * length / 4, 210), (start + 5 * length / 6, 270), 20)
        self.draw_corner(start + 3 * length / 4 + 10, 205, True, False)
        self.draw_corner(start + 5 * length / 6 - 15, 251, False, True)

        # runways
        self.draw_runway(800, 200, 18)

        draw_text("C", 290, 230, self.surface)
        draw_text("F", 435, 230, self.surface)
        draw_text("B", 635, 230, self.surface)
        draw_text("G", 830, 230, self.surface)
        draw_text("A", 985, 230, self.surface)

        draw_text("E", 350, 263, self.surface)
        draw_text("E", 530, 263, self.surface)
        draw_text("E", 750, 263, self.surface)
        draw_text("E", 930, 263, self.surface)

        draw_text("C", 290, 300, self.surface)
        draw_text("B", 635, 300, self.surface)
        draw_text("A", 985, 300, self.surface)

        draw_text("D", 350, 343, self.surface)
        draw_text("D", 930, 343, self.surface)

        self.gates = [Gate(400, 410, "B1"),
                      Gate(430, 410, "B2"),
                      Gate(460, 410, "B3"),
                      Gate(490, 410, "B4"),
                      Gate(520, 410, "B5"),
                      Gate(550, 410, "B6"),
                      Gate(580, 410, "B7"),
                      Gate(700, 410, "A1"),
                      Gate(730, 410, "A2"),
                      Gate(760, 410, "A3"),
                      Gate(790, 410, "A4"),
                      Gate(820, 410, "A5"),
                      Gate(850, 410, "A6"), ]

        for gate in self.gates:
            self.surface.blit(gate.text_box, (gate.x, gate.y))

        self.ground_map.add_point(Waypoint("rw_exit_c", 295, 200, ["rw_exit_f", "rw_hold_c"]))
        self.ground_map.add_point(Waypoint("rw_exit_f", 455, 200, ["rw_exit_c", "rw_exit_b", "rw_hold_f"]))
        self.ground_map.add_point(Waypoint("rw_exit_b", 638, 200, ["rw_exit_f", "rw_exit_g", "rw_hold_b"]))
        self.ground_map.add_point(Waypoint("rw_exit_g", 810, 200, ["rw_exit_b", "rw_exit_a", "rw_hold_g"]))
        self.ground_map.add_point(Waypoint("rw_exit_a", 988, 200, ["rw_exit_g", "rw_hold_a"]))

        self.ground_map.add_point(Waypoint("rw_hold_c", 295, 240, ["rw_exit_c", "tw_ce"]))
        self.ground_map.add_point(Waypoint("rw_hold_f", 437, 240, ["rw_exit_f", "tw_fe"]))
        self.ground_map.add_point(Waypoint("rw_hold_b", 638, 240, ["rw_exit_b", "tw_be"]))
        self.ground_map.add_point(Waypoint("rw_hold_g", 842, 240, ["rw_exit_g", "tw_ge"]))
        self.ground_map.add_point(Waypoint("rw_hold_a", 988, 240, ["rw_exit_a", "tw_ae"]))

        self.ground_map.add_point(Waypoint("tw_ce", 298, 270, ["rw_hold_c", "tw_fe", "tw_cd"]))
        self.ground_map.add_point(Waypoint("tw_fe", 417, 270, ["rw_hold_f", "tw_ce", "tw_be"]))
        self.ground_map.add_point(Waypoint("tw_be", 641, 270, ["rw_hold_b", "tw_fe", "tw_ge", "tw_bd"]))
        self.ground_map.add_point(Waypoint("tw_ge", 864, 270, ["rw_hold_g", "tw_be", "tw_ae"]))
        self.ground_map.add_point(Waypoint("tw_ae", 987, 270, ["rw_hold_a", "tw_ge", "tw_ad"]))

        self.ground_map.add_point(Waypoint("tw_cd", 303, 350, ["tw_ce", "tw_bd"]))
        self.ground_map.add_point(Waypoint("tw_bd", 638, 350, ["tw_cd", "tw_ad", "tw_be"]))
        self.ground_map.add_point(Waypoint("tw_ad", 983, 350, ["tw_bd", "tw_ae"]))

        for gate in self.gates:
            name = "gate-{}".format(gate.name.lower())
            if "a" in gate.name.lower():
                self.ground_map.add_point(Waypoint(name, gate.x + 18, gate.y - 58, ["tw_ad"]))
                self.ground_map.get_point("tw_ad").connected_points.append(name)
            else:
                self.ground_map.add_point(Waypoint(name, gate.x + 18, gate.y - 58, ["tw_bd"]))
                self.ground_map.get_point("tw_bd").connected_points.append(name)

    def draw_corner(self, start_x, start_y, right: bool, top: bool):
        if right and top:
            pygame.draw.arc(self.surface, TAXI_COLOR,
                            (start_x - 6, start_y - 24, 50, 50),
                            math.pi, 3 * math.pi / 2, 15)
        elif not right and top:
            pygame.draw.arc(self.surface, TAXI_COLOR,
                            (start_x - 42, start_y - 24, 50, 50),
                            3 * math.pi / 2, 2 * math.pi, 15)
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
        text = draw_text_box("RWY %d" % orientation, angle=90)
        self.surface.blit(text, (start, y_pos - text.get_height() / 2))
        text = draw_text_box("RWY %d" % (orientation + 18), angle=90)
        self.surface.blit(text, (start + length, y_pos - text.get_height() / 2))

    def draw_aircraft_status(self, surface: pygame.Surface):
        offset = 0
        for aircraft in self.aircraft:
            draw_text(aircraft.callsign + ": " + str(aircraft.get_status()), 5, self.surface.get_height() - 65 - offset,
                      surface)
            offset += 20


def draw_text_box(text: str,
                  text_color: tuple[int, int, int] = BLACK,
                  background_color: tuple[int, int, int] = WHITE,
                  angle: int = 0) -> pygame.Surface:
    font = pygame.font.SysFont("Helvetica", 12)
    text = font.render(text, True, text_color)
    text = pygame.transform.rotate(text, angle)
    text_surface = pygame.Surface((text.get_width() + 5, text.get_height() + 5))
    pygame.draw.rect(text_surface, background_color,
                     ((0, 0), (text.get_width() + 5, text.get_height() + 5)),
                     border_radius=5)
    text_surface.blit(text, (2.5, 2.5))
    return text_surface


def draw_text(text: str, x: int, y: int, surface: pygame.Surface):
    text = draw_text_box(text, WHITE, BLACK)
    surface.blit(text, (x, y))
