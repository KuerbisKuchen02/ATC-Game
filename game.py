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
        parser.valid()
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

    gates = [Gate(400, 410, "B1"),
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
             Gate(850, 410, "A6"),]

    airport = Airport(background, "Rocky Mountain Regional", [], [], gates)
    # airport.ground_map.draw(background)

    font = pygame.font.SysFont("Helvetica", 36)
    font_object = font.render("Rocky Mountain Regional", True, (255, 255, 255))
    background.blit(font_object, (50, 50))

    for gate in gates:
        airport.add_aircraft(AiAircraft.parked_aircraft(airport, gate))
    # noinspection PyTypeChecker
    airport.add_aircraft(AiAircraft(
        "LH14",
        (330, 200),
        90,
        0,
        0,
        Status.READY_FOR_TAKEOFF,
        airport))

    airport.aircraft[0]._status = Status.READY_FOR_PUSHBACK


    input_box = InputBox(0, screen.get_height() - 40, 1000, 40, instructions)

    #airport.aircraft[0].set_instruction(Instruction.TAXI, "rw_hold_a")
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
                callsign, instruction = instructions.get_nowait()
            except queue.Empty:
                break
            for a in airport.aircraft:
                a: AiAircraft
                if a.callsign == callsign:
                    a.set_instruction(instruction)
                    instructions.task_done()
                    break
        input_box.update()
        screen.blit(background, (0, 0))
        input_box.draw(screen)
        airport.update(dt)
        airport.draw_aircraft_status(screen)
        for a in airport.aircraft:
            screen.blit(a.track, (0, 0))
        pygame.display.update()
        dt = clock.tick(60) / 1000  # limits FPS to 60

    pygame.quit()


if __name__ == '__main__':
    game()
