import enum
import math
import os
from math import degrees

import pygame
import compiler.data as data
import ground_map

from airport import Airport, Gate

TURN_SPEED = 3  # degree / s
VERT_SPEED = 30  # ft / s
ACCEL = 3  # kt / s

TAXI_SPEED = 15  # kt
TAXI_TURN_SPEED = 2  # kt

MIN_CLEAR_TO_LAND_HEIGHT = 50  # ft

MULTIPLIER = 1


class Status(enum.Enum):
    (PARKED, READY_FOR_PUSHBACK, PUSHBACK, READY_FOR_TAXI, TAXI_RUNWAY, HOLD_POS, READY_FOR_LINE_UP, LINE_UP,
     READY_FOR_TAKEOFF, TAKEOFF, GO_AROUND, AIRBORNE, READY_TO_LAND, LANDING, READY_FOR_GATE, TAXI_GATE, WAIT) = range(17)


class Instruction(enum.Enum):
    PUSHBACK, TAXI, HOLD, CONTINUE, TAKEOFF, LINE_UP, ABORT, LAND, GO_AROUND = range(9)


class Aircraft(pygame.sprite.Sprite):
    def __init__(self, callsign: str, position: tuple[float, float], heading: float, altitude: float, speed: float,
                 status: Status, airport: Airport):
        pygame.sprite.Sprite.__init__(self)
        self.original_image = pygame.image.load('resources/plane.svg').convert_alpha()
        self.original_image = pygame.transform.smoothscale(self.original_image, (20, 20))
        font = pygame.font.SysFont("Helvetica", 10)
        self.text = font.render(callsign, True, (255, 255, 255))
        self.image = pygame.transform.rotate(self.original_image, 180)
        self.area = pygame.display.get_surface().get_rect()
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(position[0] - 10, position[1] - 10)
        self.callsign = callsign
        self._acl_heading = self.heading = heading
        self._position: list[float] = list(position)
        self._acl_altitude = self.altitude = altitude
        self._acl_speed = self.speed = speed
        self._status = status
        self._airport = airport
        self.backup_state = (Status.PARKED, 0)

    def _get_heading(self, position: tuple[float, float]) -> float:
        dx = self._position[0] - position[0]
        dy = self._position[1] - position[1]
        if dy == 0:
            tan = 90
        else:
            tan = degrees(math.atan(abs(dx) / dy))
        if dx <= 0:
            return tan if tan >= 0 else 180 + tan
        else:
            return 360 - tan if tan > 0 else 180 - tan

    def get_status(self) -> Status:
        return self._status

    def fly_towards(self, position: tuple[float, float]):
        self.heading = self._get_heading(position)

    def update(self, dt: float):
        dt = 0.1
        # Speed
        if self._acl_speed < self.speed:
            self._acl_speed += min(self.speed - self._acl_speed, ACCEL * dt) * MULTIPLIER
        elif self._acl_speed > self.speed:
            self._acl_speed -= min(self._acl_speed - self.speed, ACCEL * dt) * MULTIPLIER

        if self._acl_speed != 0:

            # Heading
            div_left = (360 + self._acl_heading - self.heading) % 360
            div_right = (360 + self.heading - self._acl_heading) % 360
            if div_left > div_right:
                self._acl_heading += (
                            min(self.heading - self._acl_heading, TURN_SPEED * dt * abs(self._acl_speed) * 00.1)
                            * MULTIPLIER)
            else:
                self._acl_heading -= (
                            min(self._acl_heading - self.heading, TURN_SPEED * dt * abs(self._acl_speed) * 00.1)
                            * MULTIPLIER)

            # Altitude
            if self._acl_altitude < self.altitude:
                self._acl_altitude += min(self.altitude - self._acl_altitude, VERT_SPEED * dt) * MULTIPLIER
            elif self._acl_altitude > self.altitude:
                self._acl_altitude -= min(self._acl_altitude - self.altitude, VERT_SPEED * dt) * MULTIPLIER

        new_pos = self._calc_new_pos(self.rect, self._acl_heading, self._acl_speed / 10, dt)

        if self.area.contains(new_pos):
            self.rect = new_pos
        self.image = pygame.transform.rotate(self.original_image, -self._acl_heading)
        self.rect = self.image.get_rect(center=self.rect.center)

        screen = pygame.display.get_surface()
        screen.blit(self.image, self.rect)
        if self._status in (Status.READY_FOR_PUSHBACK, Status.PUSHBACK):
            screen.blit(self.text, self.rect.move(-(self.text.get_width() - self.rect.width) / 2,
                                                  4-self.rect.height))
        elif self._status != Status.PARKED:
            screen.blit(self.text, self.rect.move(-(self.text.get_width() - self.rect.width) / 2,
                                                  self.rect.height + self.text.get_height() / 2))

    def _calc_new_pos(self, rect, heading, speed, dt):
        angle = math.radians(heading + 90)
        dx = dt * speed * math.cos(angle)
        dy = dt * speed * math.sin(angle)
        self._position[0] -= dx * MULTIPLIER
        self._position[1] -= dy * MULTIPLIER
        rect.left = self._position[0] - 10
        rect.top = self._position[1] - 10
        return rect

    def is_colliding(self, delta=0) -> bool:
        for a in self._airport.aircraft:
            a: Aircraft
            if self.callsign == a.callsign:
                continue
            if ((a.rect.x - delta) <= self.rect[0] <= (a.rect.x + a.rect.w + delta)
                    and (a.rect.y - delta) <= self.rect[1] <= (a.rect.y + a.rect.h + delta)):
                return True
        return False


class AiAircraft(Aircraft):
    def __init__(self, callsign: str, position: tuple[float, float], heading: float, altitude: float, speed: float,
                 status: Status, airport: Airport):
        super().__init__(callsign, position, heading, altitude, speed, status, airport)
        self._instruction = None
        self._goal: list[tuple[float, float]] = []
        self.track = pygame.Surface(pygame.display.get_surface().get_size())
        self.track.set_colorkey((0, 0, 0))
        self._turn_towards = True

    @classmethod
    def parked_aircraft(cls, airport: Airport, gate: Gate):
        return cls(data.get_random_callsign(),
                   gate.get_spawn_point(),
                   180,
                   0,
                   0,
                   Status.PARKED,
                   airport)

    def fly_towards(self, position: tuple[float, float] = None):
        if position is None:
            position = self._goal[0]
        super().fly_towards(position)

    def set_goal(self, waypoint: str):
        ground_map = self._airport.ground_map
        closest_point = ground_map.find_closest(self._position)
        path = ground_map.get_shortest_path(closest_point, waypoint)
        for point_name in path:
            point = ground_map.get_point(point_name)
            self._goal.append((point.x, point.y))

    def set_instruction(self, instruction: Instruction, waypoint: str = None):
        if instruction == Instruction.PUSHBACK and self._status == Status.READY_FOR_PUSHBACK:
            self._turn_towards = False
            self._status = Status.PUSHBACK
            self._goal.append((self._position[0], self._position[1] - 35))
            self._goal.append((self._position[0] + 45, 350))
            self.speed = -20
        elif instruction == Instruction.TAXI and self._status == Status.READY_FOR_TAXI:
            self._status = Status.TAXI_RUNWAY
            self.set_goal(waypoint)
            self.speed = 20
        elif instruction == Instruction.LINE_UP and self._status == Status.READY_FOR_LINE_UP:
            self._status = Status.LINE_UP
            self._goal.append((self._position[0], self._position[1] - 25))
            self._goal.append((self._position[0] + 35, 200))
            self.speed = 20
        elif instruction == Instruction.TAKEOFF and (self._status == Status.READY_FOR_TAKEOFF or
                                                     self._status == Status.READY_FOR_LINE_UP):
            self._status = Status.TAKEOFF
            if self._status == Status.READY_FOR_LINE_UP:
                self._goal.append((self._position[0], self._position[1] - 25))
                self._goal.append((self._position[0] + 35, 200))
                self.speed = 20
            waypoint = self._airport.ground_map.get_point("rw_exit_g")
            self._goal.append((waypoint.x, waypoint.y))

    def _check_goal(self):
        if (len(self._goal) > 0
                and abs(self._goal[0][0] - self._position[0]) < 5
                and abs(self._goal[0][1] - self._position[1]) < 5):
            self._goal.pop(0)
            return True
        return False

    def update(self, dt: float):
        # if self.is_colliding(20):
        #     self.backup_state = (self._status, self.speed)
        #     self.speed = 0
        #     self._status = Status.WAIT
        # elif self._status == Status.WAIT:
        #     self._status, self.speed = self.backup_state

        if self._turn_towards and len(self._goal) > 0:
            self.fly_towards()
        super().update(dt)

        if self._check_goal():
            match self._status:
                case Status.PUSHBACK:
                    if len(self._goal) > 0:
                        self.heading = 270
                    else:
                        self.speed = 0
                        self._turn_towards = True
                        self._status = Status.READY_FOR_TAXI
                case Status.READY_FOR_TAXI:
                    pass
                case Status.TAXI_RUNWAY:
                    if len(self._goal) == 0:
                        self.speed = 0
                        self._status = Status.READY_FOR_TAKEOFF
                case Status.LINE_UP:
                    if len(self._goal) == 0:
                        self.speed = 0
                        self._status = Status.READY_FOR_TAKEOFF

        if self._status == Status.TAKEOFF:
            if len(self._goal) == 1:
                self.speed = 200
            elif len(self._goal) == 0:
                self.altitude = 10000
                if self._acl_altitude > 200:
                    self.speed = 300
                    self._status = Status.AIRBORNE

        if self._acl_speed != 0:
            os.system('clear')
            print("Aircraft data")
            print("Heading %d; Actually %d" % (self.heading, self._acl_heading))
            print("Speed %d; Actually %d" % (self.speed, self._acl_speed))
            print("Altitude %d; Actually %d" % (self.altitude, self._acl_altitude))
            print("Position X:%d, Y:%d" % (self._position[0], self._position[1]))
            print("Goal X:%d, Goal Y:%d" % (self._goal[0][0], self._goal[0][1]) if len(self._goal) > 0
                  else "Goal None")
            print("Status: %s ; Instruction: %s" % (self._status, self._instruction))

        self.track = pygame.Surface(pygame.display.get_surface().get_size())
        self.track.set_colorkey((0, 0, 0))
        self.track.set_at((int(self._position[0]), int(self._position[1])), pygame.Color("red"))
        for i, goal in enumerate(self._goal):
            pygame.draw.rect(self.track, (0, 0, 255), (goal[0] - 5, goal[1] - 5, 10, 10),
                             10, 5)
            if i == 0:
                pygame.draw.line(self.track, (0, 0, 255),
                                 (goal[0], goal[1]),
                                 (self._position[0], self._position[1]))
            else:
                pygame.draw.line(self.track, (0, 0, 255),
                                 (goal[0], goal[1]),
                                 (self._goal[i - 1][0], self._goal[i - 1][1]))
