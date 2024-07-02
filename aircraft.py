import enum
import math

import pygame

TURN_SPEED = 3  # degree / s
VERT_SPEED = 30  # ft / s
ACCEL = 3  # kt / s

TAXI_SPEED = 15  # kt
TAXI_TURN_SPEED = 2  # kt

MIN_CLEAR_TO_LAND_HEIGHT = 50  # ft


class Status(enum.Enum):
    (PARKED, READY_FOR_PUSHBACK, PUSHBACK, READY_FOR_TAKI, TAXI, HOLD_POS, READY_FOR_TAKEOFF, LINE_UP,
     TAKEOFF, AIRBORNE, READY_TO_LAND, LANDING, READY_FOR_GATE) = range(13)


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
        self.rect = self.rect.move(position[0] / 10, position[1] / 10)
        self.callsign = callsign
        self._acl_heading = self.heading = heading
        self._position: list[float] = list(position)
        self._acl_altitude = self.altitude = altitude
        self._acl_speed = self.speed = speed

    def fly_towards(self, position: tuple[float, float]):
        dx = position[0] - self._position[0]
        dy = position[1] - self._position[1]
        theta = math.atan2(dy, dx)
        self.heading = math.degrees(math.pi - theta)

    def update(self, dt: float):
        if self._acl_heading < self.heading:
            self._acl_heading += min(self.heading - self._acl_heading, TURN_SPEED * dt)
        elif self._acl_heading > self.heading:
            self._acl_heading -= min(self._acl_heading - self.heading, TURN_SPEED * dt)
        # Speed
        if self._acl_speed < self.speed:
            self._acl_speed += min(self.speed - self._acl_speed, ACCEL * dt)
        elif self._acl_speed > self.speed:
            self._acl_speed -= min(self._acl_speed - self.speed, ACCEL * dt)
        # Altitude
        if self._acl_altitude < self.altitude:
            self._acl_altitude += min(self.altitude - self.altitude, VERT_SPEED * dt)
        elif self._acl_altitude > self.altitude:
            self._acl_altitude -= min(self._acl_altitude - self.altitude, VERT_SPEED * dt)

        new_pos = self._calc_new_pos(self.rect, self.heading, self.speed, dt)
        if self.area.contains(new_pos):
            self.rect = new_pos
        self.image = pygame.transform.rotate(self.original_image, -self.heading)
        self.rect = self.image.get_rect(center=self.rect.center)
        screen = pygame.display.get_surface()
        screen.blit(self.image, self.rect)
        screen.blit(self.text, self.rect.move(-(self.text.get_width() - self.rect.width) / 2,
                                              self.rect.height + self.text.get_height() / 2))

    def _calc_new_pos(self, rect, heading, speed, dt):
        angle = math.radians(heading + 90)
        dx = dt * speed * math.cos(angle)
        dy = dt * speed * math.sin(angle)
        self._position[0] -= dx
        self._position[1] -= dy
        rect.left = self._position[0] / 10
        rect.top = self._position[1] / 10
        return rect
