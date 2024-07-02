from compiler.lexer import Lexer, TokenType, Token


class Parser:
    lookahead: Token

    def __init__(self, i: Lexer):
        self.input = i
        self.consume()

    def match(self, x: TokenType):
        if self.lookahead.token_type == x:
            self.consume()
        else:
            raise RuntimeError("Parsing exception. Expected %s but was %s" % (x.name, self.lookahead))

    def consume(self):
        self.lookahead = next(self.input)

    def valid(self):
        self.expression()

    def expression(self):
        if self.lookahead == TokenType.GREETING:
            self.match(TokenType.GREETING)
        self.exp_start()
        if self.lookahead == TokenType.GREETING:
            self.match(TokenType.GREETING)
        if self.lookahead == TokenType.CLEAR:
            self.clearance()
        elif self.lookahead == TokenType.HOLD:
            self.hold_exp()
        elif self.lookahead == TokenType.CONTINUE:
            self.cont_taxi()
        elif self.lookahead == TokenType.ABORT:
            self.abort_to()
        elif self.lookahead == TokenType.LINE_UP:
            self.line_up_exp()
        elif self.lookahead == TokenType.GO_AROUND:
            self.match(TokenType.GO_AROUND)
        elif self.lookahead == TokenType.TAXI:
            self.taxi_clr()
        else:
            raise RuntimeError()

    def exp_start(self):
        if self.lookahead == TokenType.FLIGHT:
            self.match(TokenType.FLIGHT)
        while self.lookahead == TokenType.WORD:
            self.match(TokenType.WORD)
        self.match(TokenType.NUMBER)

    def clearance(self):
        self.match(TokenType.CLEAR)
        if self.lookahead == TokenType.PREPOSITION:
            self.match(TokenType.PREPOSITION)
        if self.lookahead == TokenType.TAKEOFF:
            self.takeoff_clr()
        elif self.lookahead == TokenType.CROSS:
            self.cross_clr()
        elif self.lookahead == TokenType.LAND:
            self.landing_clr()
        elif self.lookahead == TokenType.TAXI:
            self.taxi_clr()
        else:
            raise RuntimeError()

    def takeoff_clr(self):
        self.match(TokenType.TAKEOFF)
        self.runway()
        if self.lookahead == TokenType.WIND:
            self.match(TokenType.WIND)
        # TODO wind

    def cross_clr(self):
        self.match(TokenType.CROSS)
        self.runway()

    def landing_clr(self):
        self.match(TokenType.LAND)
        if self.lookahead == TokenType.PREPOSITION:
            self.match(TokenType.PREPOSITION)
        self.runway()

    def taxi_clr(self):
        self.match(TokenType.TAXI)
        if self.lookahead == TokenType.PREPOSITION:
            self.match(TokenType.PREPOSITION)
        if self.lookahead == TokenType.RUNWAY:
            self.runway()
        elif self.lookahead == TokenType.GATE:
            self.match(TokenType.GATE)
        if self.lookahead == TokenType.VIA:
            self.match(TokenType.VIA)
            while self.lookahead == TokenType.WORD:
                self.match(TokenType.WORD)

    def hold_exp(self):
        self.match(TokenType.HOLD)
        if self.lookahead == TokenType.SHORT:
            self.match(TokenType.SHORT)
        elif self.lookahead == TokenType.POS:
            self.match(TokenType.POS)

    def cont_taxi(self):
        self.match(TokenType.CONTINUE)
        self.match(TokenType.TAXI)

    def abort_to(self):
        self.match(TokenType.ABORT)
        self.match(TokenType.TAKEOFF)

    def line_up_exp(self):
        self.match(TokenType.LINE_UP)
        if self.lookahead == TokenType.WAIT:
            self.match(TokenType.WAIT)
        self.runway()

    def runway(self):
        if self.lookahead == TokenType.RUNWAY:
            self.match(TokenType.RUNWAY)
        self.match(TokenType.NUMBER)
        if self.match(TokenType.WORD):
            self.match(TokenType.WORD)
