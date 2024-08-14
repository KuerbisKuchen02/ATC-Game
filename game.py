import pygame
import threading
import queue

import speech_recognition as sr

from aircraft import AiAircraft, Status, Instruction
from airport import Airport
from compiler.lexer import Lexer
from compiler.parser import Parser

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

    airport = Airport(background, "Rocky Mountain Regional", [], [], [])
    airport.ground_map.draw(background)

    font = pygame.font.SysFont("Helvetica", 36)
    font_object = font.render("Rocky Mountain Regional", True, (255, 255, 255))
    background.blit(font_object, (50, 50))

    aircraft = pygame.sprite.Group()
    # noinspection PyTypeChecker
    aircraft.add(AiAircraft(
        "LH1234",
        (500, 400),
        180,
        0,
        0,
        Status.READY_FOR_PUSHBACK,
        airport))
    # noinspection PyTypeChecker
    aircraft.add(AiAircraft(
        "LH2",
        (550, 400),
        180,
        0,
        0,
        Status.READY_FOR_PUSHBACK,
        airport))

    clock = pygame.time.Clock()
    running = True
    dt = 0

    path = airport.ground_map.get_shortest_path("rw_exit_c", "tw_ad")
    print(path)

    screen.blit(background, (0, 0))
    pygame.display.update()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                threading.Thread(target=input_handler, daemon=True).start()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                threading.Thread(target=text_input_handler, daemon=True).start()

        while instructions.not_empty:
            try:
                callsign, instruction = instructions.get_nowait()
            except queue.Empty:
                break
            for a in aircraft:
                a: AiAircraft
                if a.callsign == callsign:
                    a.set_instruction(instruction)
                    instructions.task_done()
                    break
        screen.blit(background, (0, 0))
        aircraft.update(dt)
        for a in aircraft:
            screen.blit(a.track, (0, 0))
        pygame.display.update()
        dt = clock.tick(60) / 1000  # limits FPS to 60

    pygame.quit()


if __name__ == '__main__':
    game()
