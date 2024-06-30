from lexer import Lexer
from parser import Parser

parser = Parser(Lexer("Flight Lufthansa 4713 good morning cleared to land runway 18 left"))
parser.valid()
