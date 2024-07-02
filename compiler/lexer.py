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
    (EOF, ABORT, CALLSIGN, CLEAR, CONTINUE, CROSS, FLIGHT, GATE, GO_AROUND, GREETING, HEADING, HEIGHT, HOLD, LAND,
     LINE_UP, NEWLINE, NUMBER, POS, PREPOSITION, PUSHBACK, RUNWAY, SHORT, SPEED, TAXI, TAXIWAY, TAKEOFF, VIA, WAIT,
     WIND, WORD, WS) = range(31)


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

