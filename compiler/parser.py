from compiler.lexer import Lexer, TokenType, Token
from aircraft import Instruction
from compiler.data import get_airline_from_callsign, Airline


class Parser:
    lookahead: Token

    def __init__(self, lexer: Lexer):
        self.input = lexer
        self.consume()

    def match(self, x: TokenType):
        if self.lookahead.token_type == x:
            self.consume()
        else:
            raise RuntimeError("Parsing exception. Expected %s but was %s" % (x.name, self.lookahead))

    def consume(self):
        self.lookahead = next(self.input)

    def valid(self):
        ret = self.expression()
        if self.lookahead.token_type is not TokenType.EOF:
            raise RuntimeError("Parsing exception. Expected EOF, but was %s" % self.lookahead)
        return ret

    def expression(self):
        meta = ""
        if self.lookahead.token_type == TokenType.GREETING:
            self.match(TokenType.GREETING)
        callsign = self.exp_start()
        if self.lookahead.token_type == TokenType.GREETING:
            self.match(TokenType.GREETING)
        if self.lookahead.token_type == TokenType.CLEAR:
            meta, instruction = self.clearance()
        elif self.lookahead.token_type == TokenType.HOLD:
            self.hold_exp()
            instruction = Instruction.HOLD
        elif self.lookahead.token_type == TokenType.CONTINUE:
            self.cont_taxi()
            instruction = Instruction.CONTINUE
        elif self.lookahead.token_type == TokenType.ABORT:
            self.abort_to()
            instruction = Instruction.ABORT
        elif self.lookahead.token_type == TokenType.LINE_UP:
            self.line_up_exp()
            instruction = Instruction.LINE_UP
        elif self.lookahead.token_type == TokenType.GO_AROUND:
            self.match(TokenType.GO_AROUND)
            instruction = Instruction.GO_AROUND
        elif self.lookahead.token_type == TokenType.TAXI:
            meta = self.taxi_clr()
            instruction = Instruction.TAXI
        else:
            raise RuntimeError()
        return callsign, instruction, meta

    def exp_start(self) -> str:
        ret: str = ""
        if self.lookahead.token_type == TokenType.FLIGHT:
            self.match(TokenType.FLIGHT)
        while self.lookahead.token_type == TokenType.WORD:
            ret += self.lookahead.value.upper()
            self.match(TokenType.WORD)
        airline: Airline = get_airline_from_callsign(ret)
        if airline is not None:
            ret = airline.iata
            if len(ret) == 0:
                ret = airline.icao
        ret += str(self.lookahead.value)
        self.match(TokenType.NUMBER)
        return ret

    def clearance(self) -> tuple[str, Instruction]:
        self.match(TokenType.CLEAR)
        if self.lookahead.token_type == TokenType.PREPOSITION:
            self.match(TokenType.PREPOSITION)
        if self.lookahead.token_type == TokenType.TAKEOFF:
            self.takeoff_clr()
            return "", Instruction.TAKEOFF
        elif self.lookahead.token_type == TokenType.CROSS:
            self.cross_clr()
        elif self.lookahead.token_type == TokenType.LAND:
            return self.landing_clr()
        elif self.lookahead.token_type == TokenType.TAXI:
            self.taxi_clr()
        elif self.lookahead.token_type == TokenType.PUSHBACK:
            self.match(TokenType.PUSHBACK)
            return "", Instruction.PUSHBACK
        else:
            raise RuntimeError()

    def takeoff_clr(self):
        self.match(TokenType.TAKEOFF)
        self.runway()
        # if self.lookahead.token_type == TokenType.WIND:
        #     self.match(TokenType.WIND)
        # TODO wind

    def cross_clr(self):
        self.match(TokenType.CROSS)
        self.runway()

    def landing_clr(self) -> tuple[str, Instruction]:
        self.match(TokenType.LAND)
        if self.lookahead.token_type == TokenType.PREPOSITION:
            self.match(TokenType.PREPOSITION)
        return self.runway(), Instruction.LAND

    def taxi_clr(self) -> list[str]:
        points: list[str] = []
        goal: str = ""
        self.match(TokenType.TAXI)
        if self.lookahead.token_type == TokenType.PREPOSITION:
            self.match(TokenType.PREPOSITION)
        if self.lookahead.token_type == TokenType.RUNWAY:
            goal = self.runway()
        elif self.lookahead.token_type == TokenType.GATE:
            self.match(TokenType.GATE)
            goal = self.lookahead.value.lower()[:1]
            self.match(TokenType.WORD)
            goal += str(self.lookahead.value)
            self.match(TokenType.NUMBER)
        if self.lookahead.token_type == TokenType.VIA:
            self.match(TokenType.VIA)
            while self.lookahead.token_type == TokenType.WORD:
                points.append(self.lookahead.value)
                self.match(TokenType.WORD)
        points.append(goal)
        return points

    def hold_exp(self):
        self.match(TokenType.HOLD)
        if self.lookahead.token_type == TokenType.SHORT:
            self.match(TokenType.SHORT)
        elif self.lookahead.token_type == TokenType.POS:
            self.match(TokenType.POS)

    def cont_taxi(self):
        self.match(TokenType.CONTINUE)
        self.match(TokenType.TAXI)

    def abort_to(self):
        self.match(TokenType.ABORT)
        self.match(TokenType.TAKEOFF)

    def line_up_exp(self):
        self.match(TokenType.LINE_UP)
        if self.lookahead.token_type == TokenType.WAIT:
            self.match(TokenType.WAIT)

    def runway(self) -> str:
        if self.lookahead.token_type == TokenType.RUNWAY:
            self.match(TokenType.RUNWAY)
        runway = self.lookahead.value
        self.match(TokenType.NUMBER)
        if self.lookahead.token_type == TokenType.WORD:
            self.match(TokenType.WORD)
            runway += self.lookahead.value
        return runway