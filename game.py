import pygame
import threading
import queue
import random
import re

import speech_recognition as sr

from aircraft import AiAircraft
from airport import Airport
from compiler.lexer import Lexer
from compiler.parser import Parser
from textio import InputBox

instructions = queue.Queue()
inbound = queue.Queue()
inbound_timer: threading.Timer | None = None

timers = []
boarding_timer: threading.Timer | None = None


def input_handler():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something!")
        audio = r.listen(source)
    try:
        input_str = r.recognize_google(audio)
        print(input_str)
        parser = Parser(Lexer(input_str))
        instructions.put(parser.valid())
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {}".format(e))


def text_input_handler():
    input_str = input("Command: ")
    input_str = re.sub(r"([a-zA-Z]+)(\d+)", "%1 %2", input_str)
    parser = Parser(Lexer(input_str))
    instructions.put(parser.valid())


def start_boarding(airport: Airport):
    global boarding_timer
    for aircraft in airport.aircraft:
        if aircraft.timer is None:
            aircraft.start_boarding(1, 60)
            break

    if boarding_timer and not boarding_timer.is_alive():
        boarding_timer = threading.Timer(180, start_boarding, args=(airport,))
        boarding_timer.start()

def handle_inbound(airport: Airport):
    global inbound
    global inbound_timer
    if not inbound.empty():
        inbound.get(timeout=5)
        airport.add_aircraft(AiAircraft.inbound_aircraft(airport))
        inbound_timer = threading.Timer(20, handle_inbound, args=(airport,))
        inbound_timer.start()
        inbound.task_done()

def handle_inbound_queue(airport: Airport):
    global inbound
    global inbound_timer
    inbound.put(airport)
    if not inbound_timer or not inbound_timer.is_alive():
        handle_inbound(airport)

def game():
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption('ATC Controller')

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((40, 40, 40))

    airport = Airport(background, "Rocky Mountain Regional")

    for gate in airport.gates:
        airport.add_aircraft(AiAircraft.parked_aircraft(airport, gate))

    font = pygame.font.SysFont("Helvetica", 36)
    font_object = font.render("Rocky Mountain Regional", True, (255, 255, 255))
    background.blit(font_object, (50, 50))

    input_box = InputBox(0, screen.get_height() - 40, 1000, 40, instructions)

    clock = pygame.time.Clock()
    running = True
    dt = 0

    start_boarding(airport)
    start_boarding(airport)
    start_boarding(airport)
    global boarding_timer
    boarding_timer = threading.Timer(180, start_boarding, args=(airport,))
    boarding_timer.start()

    screen.blit(background, (0, 0))
    pygame.display.update()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                for timer in timers:
                    timer.cancel()
                for aircraft in airport.aircraft:
                    if aircraft.timer:
                        aircraft.timer.cancel()
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m and not input_box.active:
                threading.Thread(target=input_handler, daemon=True).start()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_n and not input_box.active:
                threading.Thread(target=text_input_handler, daemon=True).start()
            input_box.handle_event(event)

        for timer in timers:
            if not timer.is_alive():
                timers.remove(timer)

        if (len(airport.gates) > len(airport.aircraft) + len(timers)
                and airport.number_of_landing_aircraft() < 3
                and len(timers) < 3):
            t = random.randint(1, 60)
            print("Started timer for {} sec...".format(t))
            timer = threading.Timer(t, handle_inbound_queue, (airport,))
            timers.append(timer)
            timer.start()

        while instructions.not_empty:
            try:
                callsign, instruction, meta = instructions.get_nowait()
            except queue.Empty:
                break
            for a in airport.aircraft:
                a: AiAircraft
                if a.callsign == callsign:
                    a.set_instruction(instruction, meta)
                    instructions.task_done()
                    break
        input_box.update()
        screen.blit(background, (0, 0))
        input_box.draw(screen)
        airport.update(dt)
        airport.draw_aircraft_status(screen)
        for a in airport.aircraft:
            screen.blit(a.track, (0, 0))
            if a.is_outside_game():
                airport.aircraft.remove(a)
        pygame.display.update()
        dt = clock.tick(60) / 1000  # limits FPS to 60

    pygame.quit()


if __name__ == '__main__':
    game()
