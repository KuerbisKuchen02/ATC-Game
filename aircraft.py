import enum
import math
import os

import pygame

from airport import Airport

TURN_SPEED = 3  # degree / s
VERT_SPEED = 30  # ft / s
ACCEL = 3  # kt / s

TAXI_SPEED = 15  # kt
TAXI_TURN_SPEED = 2  # kt

MIN_CLEAR_TO_LAND_HEIGHT = 50  # ft

MULTIPLIER = 1


class Status(enum.Enum):
    (PARKED, READY_FOR_PUSHBACK, PUSHBACK_1, PUSHBACK_2, READY_FOR_TAKI, TAXI, HOLD_POS, READY_FOR_TAKEOFF, LINE_UP,
     TAKEOFF, GO_AROUND, AIRBORNE, READY_TO_LAND, LANDING, READY_FOR_GATE) = range(15)


class Instruction(enum.Enum):
    PUSHBACK, TAXI, HOLD, CONTINUE, TAKEOFF, LINE_UP, ABORT, LAND, GO_AROUND = range(9)


class Aircraft(pygame.sprite.Sprite):
    def __init__(self, callsign: str, position: tuple[float, float], heading: float, altitude: float, speed: float,
                 status: Status):
        pygame.sprite.Sprite.__init__(self)
        self.original_image = pygame.image.load('resources/plane.svg').convert_alpha()
        self.original_image = pygame.transform.smoothscale(self.original_image, (20, 20))
        font = pygame.font.SysFont("Helvetica", 10)
        self.text = font.render(callsign, True, (255, 255, 255))
        self.image = pygame.transform.rotate(self.original_image, 180)
        self.area = pygame.display.get_surface().get_rect()
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(position[0], position[1])
        self.callsign = callsign
        self._acl_heading = self.heading = heading
        self._position: list[float] = list(position)
        self._acl_altitude = self.altitude = altitude
        self._acl_speed = self.speed = speed
        self._status = status

    def _get_heading(self, position: tuple[float, float]) -> float:
        dx = position[0] - self._position[0]
        dy = position[1] - self._position[1]
        theta = math.atan2(dy, dx)
        return math.degrees(math.pi - theta)

    def fly_towards(self, position: tuple[float, float]):
        self.heading = self._get_heading(position)

    def update(self, dt: float):
        # Speed
        if self._acl_speed < self.speed:
            self._acl_speed += min(self.speed - self._acl_speed, ACCEL * dt) * MULTIPLIER
        elif self._acl_speed > self.speed:
            self._acl_speed -= min(self._acl_speed - self.speed, ACCEL * dt) * MULTIPLIER

        if self._acl_speed != 0:

            # Heading
            if self._acl_heading < self.heading:
                self._acl_heading += (min(self.heading - self._acl_heading, TURN_SPEED * dt * abs(self.speed) * 00.1)
                                      * MULTIPLIER)
            elif self._acl_heading > self.heading:
                self._acl_heading -= (min(self._acl_heading - self.heading, TURN_SPEED * dt * abs(self.speed) * 00.1)
                                      * MULTIPLIER)

            # Altitude
            if self._acl_altitude < self.altitude:
                self._acl_altitude += min(self.altitude - self.altitude, VERT_SPEED * dt) * MULTIPLIER
            elif self._acl_altitude > self.altitude:
                self._acl_altitude -= min(self._acl_altitude - self.altitude, VERT_SPEED * dt) * MULTIPLIER

            new_pos = self._calc_new_pos(self.rect, self._acl_heading, self._acl_speed / 10, dt)
            if self.area.contains(new_pos):
                self.rect = new_pos
            self.image = pygame.transform.rotate(self.original_image, -self._acl_heading)
            self.rect = self.image.get_rect(center=self.rect.center)

        screen = pygame.display.get_surface()
        screen.blit(self.image, self.rect)
        screen.blit(self.text, self.rect.move(-(self.text.get_width() - self.rect.width) / 2,
                                              self.rect.height + self.text.get_height() / 2))

    def _calc_new_pos(self, rect, heading, speed, dt):
        angle = math.radians(heading + 90)
        dx = dt * speed * math.cos(angle)
        dy = dt * speed * math.sin(angle)
        self._position[0] -= dx * MULTIPLIER
        self._position[1] -= dy * MULTIPLIER
        rect.left = self._position[0]
        rect.top = self._position[1]
        return rect


class AiAircraft(Aircraft):
    def __init__(self, callsign: str, position: tuple[float, float], heading: float, altitude: float, speed: float,
                 status: Status, airport: Airport):
        super().__init__(callsign, position, heading, altitude, speed, status)
        self._instruction = None
        self._goal = None
        self._airport = airport
        self.track = pygame.Surface(pygame.display.get_surface().get_size())
        self.track.set_colorkey((0, 0, 0))

    def set_instruction(self, instruction: Instruction, goal: tuple[int, int] = None):
        if instruction == Instruction.PUSHBACK and self._status == Status.READY_FOR_PUSHBACK:
            self._status = Status.PUSHBACK_1
            self._goal = (self._position[0], self._position[1] - 45)
            self.speed = -20

    def _check_goal(self):
        if self._goal is None:
            return False
        return abs(self._goal[0] - self._position[0]) < 5 and abs(self._goal[1] - self._position[1]) < 5

    def update(self, dt: float):
        super().update(dt)

        if self._check_goal():
            match self._status:
                case Status.PUSHBACK_1:
                    self._status = Status.PUSHBACK_2
                    self._goal = (self._position[0] + 45, 340)
                    self.heading = 270
                case Status.PUSHBACK_2:
                    self.speed = 0
                    self._goal = None
                    self._status = Status.READY_FOR_TAKI
                case Status.READY_FOR_TAKI:
                    pass
        if self._acl_speed != 0 and False:
            os.system('clear')
            print("Aircraft data")
            print("Heading %d; Actually %d" % (self.heading, self._acl_heading))
            print("Speed %d; Actually %d" % (self.speed, self._acl_speed))
            print("Position X:%d, Y:%d" % (self._position[0], self._position[1]))
            print("Goal X:%d, Goal Y:%d" % (self._goal[0], self._goal[1]) if self._goal is not None else "Goal None")
            print("Status: %s ; Instruction: %s" % (self._status, self._instruction))

        self.track = pygame.Surface(pygame.display.get_surface().get_size())
        self.track.set_colorkey((0, 0, 0))
        if self._goal is not None:
            pygame.draw.rect(self.track, (0, 0, 255), (self._goal[0] + 5, self._goal[1] + 5, 10, 10),
                             10, 5)
            pygame.draw.line(self.track, (0, 0, 255),
                             (self._goal[0] + 9, self._goal[1] + 9),
                             (self._position[0] + 9, self._position[1] + 9))
