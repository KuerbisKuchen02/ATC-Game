import pygame
import threading
import queue

import speech_recognition as sr

from aircraft import AiAircraft, Status
from airport import Airport, Gate
from compiler.lexer import Lexer
from compiler.parser import Parser
from textio import InputBox

instructions = queue.Queue()


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
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


def text_input_handler():
    input_str = input("Command: ")
    parser = Parser(Lexer(input_str))
    instructions.put(parser.valid())


def game():
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption('ATC Controller')

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((40, 40, 40))



    airport = Airport(background, "Rocky Mountain Regional")

    font = pygame.font.SysFont("Helvetica", 36)
    font_object = font.render("Rocky Mountain Regional", True, (255, 255, 255))
    background.blit(font_object, (50, 50))

    for gate in airport.gates:
        airport.add_aircraft(AiAircraft.parked_aircraft(airport, gate))
    # noinspection PyTypeChecker
    airport.add_aircraft(AiAircraft(
        "LH14",
        (842, 240),
        146,
        0,
        0,
        Status.READY_FOR_GATE,
        airport))

    airport.aircraft[0]._status = Status.READY_FOR_PUSHBACK

    # airport.add_aircraft(AiAircraft.inbound_aircraft(airport))
    airport.ground_map.draw(background)

    input_box = InputBox(0, screen.get_height() - 40, 1000, 40, instructions)

    clock = pygame.time.Clock()
    running = True
    dt = 0

    screen.blit(background, (0, 0))
    pygame.display.update()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m and not input_box.active:
                threading.Thread(target=input_handler, daemon=True).start()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_n and not input_box.active:
                threading.Thread(target=text_input_handler, daemon=True).start()
            input_box.handle_event(event)

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
