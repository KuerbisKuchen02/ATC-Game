import pygame as pg
import queue

from compiler.lexer import Lexer
from compiler.parser import Parser


class InputBox:

    COLOR_INACTIVE = pg.Color('lightskyblue3')
    COLOR_ACTIVE = pg.Color('dodgerblue2')
    FONT = None

    def __init__(self, x: int, y: int, w: int, h: int, instructions: queue.Queue, text:str ="",):
        if InputBox.FONT is None:
            InputBox.FONT = pg.font.SysFont("Helvetica", 20)
        self.rect = pg.Rect(x, y, w, h)
        self.color = InputBox.COLOR_INACTIVE
        self.text = text
        self.txt_surface = InputBox.FONT.render(text, True, pg.Color('white'))
        self.active = False
        self.instructions = instructions

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = InputBox.COLOR_ACTIVE if self.active else InputBox.COLOR_INACTIVE
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    parser = Parser(Lexer(self.text))
                    self.instructions.put(parser.valid())
                    self.text = ''
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = InputBox.FONT.render(self.text, True, pg.Color('white'))

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pg.draw.rect(screen, self.color, self.rect, 2)
