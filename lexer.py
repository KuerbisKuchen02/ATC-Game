from enum import Enum


class Iterator:
    def __init__(self, data_list: list):
        self.data_list = data_list
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.data_list):
            raise StopIteration
        self.current = self.data_list[self.index]
        self.index += 1
        return self.current

    def peek(self):
        if self.index >= len(self.data_list):
            return None
        else:
            return self.data_list[self.index]


class TokenType(Enum):
    EOF = 0
    ABORT = 1
    CALLSIGN = 2
    CLEAR = 3
    CONTINUE = 4
    CROSS = 5
    FLIGHT = 6
    GATE = 7
    GO_AROUND = 8
    GREETING = 9
    HEADING = 10
    HEIGHT = 11
    HOLD = 12
    LAND = 13
    LINE_UP = 14
    NEWLINE = 15
    NUMBER = 16
    POS = 17
    PREPOSITION = 18
    PUSHBACK = 19
    RUNWAY = 20
    SHORT = 21
    SPEED = 22
    TAXI = 23
    TAXIWAY = 24
    TAKEOFF = 25
    VIA = 26
    WAIT = 27
    WIND = 28
    WORD = 29
    WS = 30


class Token:
    def __init__(self, token_type: TokenType, value):
        self.token_type = token_type
        self.value = value

    def __str__(self):
        return "<'%s', '%s'>" % (self.value, self.token_type.name)


KEYWORDS = {
    "abort": TokenType.ABORT,
    "clear": TokenType.CLEAR,
    "continue": TokenType.CONTINUE,
    "cross": TokenType.CROSS,
    "flight": TokenType.FLIGHT,
    "gate": TokenType.GATE,
    "hold": TokenType.HOLD,
    "land": TokenType.LAND,
    "position": TokenType.POS,
    "pushback": TokenType.PUSHBACK,
    "runway": TokenType.RUNWAY,
    "short": TokenType.SHORT,
    "takeoff": TokenType.TAKEOFF,
    "taxi": TokenType.TAXI,
    "via": TokenType.VIA,
    "wait": TokenType.WAIT,
    "word": TokenType.WORD
}


class Lexer:

    def __init__(self, string: str):
        self.string = string.lower().strip()
        self.iterator = Iterator(self.string.split())

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.next_token())

    def next_token(self):
        for word in self.iterator:
            word: str
            if word in KEYWORDS:
                yield Token(KEYWORDS[word], word)
            elif word in ("clear", "cleared"):
                yield Token(TokenType.CLEAR, word)
            elif word in ("to", "for"):
                yield Token(TokenType.PREPOSITION, word)
            elif word == "go" and self.iterator.peek() == "around":
                next(self.iterator)
                yield Token(TokenType.GO_AROUND, "go around")
            elif word == "line" and self.iterator.peek() == "up":
                next(self.iterator)
                yield Token(TokenType.LINE_UP, "line up")
            elif word == "good" and self.iterator.peek() in ("morning", "afternoon", "evening"):
                value = "%s %s" % (word, self.iterator.peek())
                next(self.iterator)
                yield Token(TokenType.GREETING, value)
            elif word.isnumeric():
                yield Token(TokenType.NUMBER, int(word))
            elif word.isalpha():
                yield Token(TokenType.WORD, word)
            else:
                raise RuntimeError("Unknown token: %s" % word)

