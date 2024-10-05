import enum
import math
import random
import threading
from math import degrees

import pygame

import compiler.data as data

from airport import Airport, Gate

TURN_SPEED = 10  # degree / s
VERT_SPEED = 30  # ft / s
ACCEL = 3  # kt / s

TAXI_SPEED = 20  # kt
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

    def is_landing(self) -> bool:
        return self._status in (Status.LANDING, Status.READY_TO_LAND)

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
            if self.callsign == a.callsign or a._status == Status.PARKED:
                continue
            if ((a.rect.x - delta) <= self.rect[0] <= (a.rect.x + a.rect.w + delta)
                    and (a.rect.y - delta) <= self.rect[1] <= (a.rect.y + a.rect.h + delta)):
                return True
        return False

    def is_outside_game(self, delta=2000) -> bool:
        return not (-5000 - delta <= self.rect[0] <= self._airport.surface.get_width() + delta
                and -delta <= self.rect[1] <= self._airport.surface.get_height() + delta)


class AiAircraft(Aircraft):
    def __init__(self, callsign: str, position: tuple[float, float], heading: float, altitude: float, speed: float,
                 status: Status, airport: Airport):
        super().__init__(callsign, position, heading, altitude, speed, status, airport)
        self._instruction = None
        self._goal: list[tuple[float, float]] = []
        self.track = pygame.Surface(pygame.display.get_surface().get_size())
        self.track.set_colorkey((0, 0, 0))
        self._turn_towards = True
        self.timer: threading.Timer | None = None

    @classmethod
    def parked_aircraft(cls, airport: Airport, gate: Gate):
        aircraft = cls(data.get_random_callsign(),
                   gate.get_spawn_point(),
                   180,
                   0,
                   0,
                   Status.PARKED,
                   airport)
        return aircraft

    @classmethod
    def inbound_aircraft(cls, airport: Airport):
        a = cls(data.get_random_callsign(),
                   (-5000, 200),
                   90,
                   8400,
                   200,
                   Status.READY_TO_LAND,
                   airport)
        a.altitude = 0
        return a

    def start_boarding(self, a = 60, b = 180):
        if self.timer and self.timer.is_alive():
            raise RuntimeError("Boarding already started!")
        t = random.randint(a, b)
        print("Boarding aircraft for {} sec".format(t))
        self.timer = threading.Timer(t, self.boarding_complete_handler)
        self.timer.start()

    def boarding_complete_handler(self):
        self._status = Status.READY_FOR_PUSHBACK

    def fly_towards(self, position: tuple[float, float] = None):
        if position is None:
            position = self._goal[0]
        super().fly_towards(position)

    def set_goal(self, waypoint: str):
        gmap = self._airport.ground_map
        closest_point = gmap.find_closest(self._position)
        path = gmap.get_shortest_path(closest_point, waypoint)
        for point_name in path:
            point = gmap.get_point(point_name)
            self._goal.append((point.x, point.y))

    def set_instruction(self, instruction: Instruction, waypoints: str | list[str]):
        if instruction == Instruction.PUSHBACK and self._status == Status.READY_FOR_PUSHBACK:
            self._turn_towards = False
            self._status = Status.PUSHBACK
            self._goal.append((self._position[0], self._position[1] - 50))
            self._goal.append((self._position[0] + 45, 350))
            self.speed = -20
        elif instruction == Instruction.LINE_UP and self._status == Status.READY_FOR_LINE_UP:
            self._status = Status.LINE_UP
            self._goal.append((self._position[0], self._position[1] - 25))
            self._goal.append((self._position[0] + 35, 200))
            self.speed = 20
        elif instruction == Instruction.TAKEOFF and (self._status == Status.READY_FOR_TAKEOFF or
                                                     self._status == Status.READY_FOR_LINE_UP):
            if self._status == Status.READY_FOR_LINE_UP:
                self._goal.append((self._position[0], self._position[1] - 25))
                self._goal.append((self._position[0] + 35, 200))
                self.speed = 20
            waypoint = self._airport.ground_map.get_point("rw_exit_g")
            self._goal.append((waypoint.x, waypoint.y))
            self._status = Status.TAKEOFF
        elif instruction == Instruction.TAXI and self._status == Status.READY_FOR_TAXI:
            self._status = Status.TAXI_RUNWAY
            prev = ""
            for point in waypoints:
                match point:
                    case 18:
                        start = "tw_cd"
                        waypoint = "rw_hold_c"
                    case "bravo":
                        start = "tw_bd"
                        waypoint = "tw_be"
                    case _:
                        start = "tw_cd"
                        waypoint = "tw_ce"
                prev = self.add_points(start, waypoint, prev)
            self.speed = 20
        elif instruction == Instruction.TAXI and self._status == Status.READY_FOR_GATE:
            self._status = Status.TAXI_GATE
            prev = ""
            gate = ""
            for point in waypoints:
                match point:
                    case "alpha":
                        start = "rw_hold_g"
                        waypoint = "tw_ad"
                    case "bravo":
                        start = "rw_hold_g"
                        waypoint = "tw_bd"
                    case _:
                        start = "rw_hold_g"
                        gate = waypoint = "gate-{}".format(point)
                prev = self.add_points(start, waypoint, prev)
            g = self._airport.ground_map.get_point(gate)
            self._goal.append((g.x - 13, g.y + 47))
            self.speed = 20

        elif instruction == Instruction.LAND and self._status == Status.READY_TO_LAND:
            self._status = Status.LANDING
            wp = self._airport.ground_map.get_point("rw_exit_g")
            self._goal.append((wp.x, wp.y))
            wp = self._airport.ground_map.get_point("rw_hold_g")
            self._goal.append((wp.x, wp.y))

    def add_points(self, start, end, prev):
        if prev:
            start = prev
        prev = end
        points = self._airport.ground_map.get_shortest_path(start, end)
        for p in points:
            wp = self._airport.ground_map.get_point(p)
            self._goal.append((wp.x, wp.y))
        return prev

    def _check_goal(self):
        if (len(self._goal) > 0
                and abs(self._goal[0][0] - self._position[0]) < 5
                and abs(self._goal[0][1] - self._position[1]) < 5):
            self._goal.pop(0)
            return True
        return False

    def update(self, dt: float):
        if self._status in [Status.TAXI_RUNWAY, Status.TAXI_GATE] and self.is_colliding(20):
            self.backup_state = (self._status, self.speed)
            self.speed = 0
            self._status = Status.WAIT
        elif self._status == Status.WAIT and not self.is_colliding(20):
            self._status, self.speed = self.backup_state

        if self._turn_towards and self._goal:
            self.fly_towards()
        super().update(dt)

        if self._check_goal():
            match self._status:
                case Status.PUSHBACK:
                    if self._goal:
                        self.heading = 270
                    else:
                        self.speed = 0
                        self._turn_towards = True
                        self._status = Status.READY_FOR_TAXI
                case Status.READY_FOR_TAXI:
                    pass
                case Status.TAXI_RUNWAY:
                    if not self._goal:
                        self.speed = 0
                        self._status = Status.READY_FOR_LINE_UP
                case Status.TAXI_GATE:
                    if not self._goal:
                        self.speed = 0
                        self._status = Status.PARKED
                        self.start_boarding()
                case Status.LINE_UP:
                    if not self._goal:
                        self.speed = 0
                        self._status = Status.READY_FOR_TAKEOFF
                case Status.LANDING:
                    if not self._goal:
                        self.speed = 0
                        self._status = Status.READY_FOR_GATE

        if self._status == Status.TAKEOFF:
            if len(self._goal) == 1:
                self.speed = 200
            elif len(self._goal) == 0:
                self.altitude = 10000
                if self._acl_altitude > 200:
                    self.speed = 300
                    self._status = Status.AIRBORNE
        elif self._status == Status.READY_TO_LAND:
            if self.rect.x > 0:
                self._status = Status.GO_AROUND
                self.altitude = 10000
                self.speed = 300
        elif self._status == Status.GO_AROUND:
            if self.altitude > 1000:
                self._status = Status.AIRBORNE
        elif self._status == Status.LANDING:
            if self._acl_altitude < 10:
                self.speed = 20

        if self._status in [Status.READY_TO_LAND, Status.LANDING]:
            if 100 < self._acl_altitude < 2000:
                self.speed = 160

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
