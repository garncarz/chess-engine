#!/usr/bin/env python3

from enum import Enum
import logging
import random

log = logging.getLogger(__name__)


class Position:
    def __init__(self, *args):
        """
        Can be initialized as both 'e2' or 5, 2.
        """
        if isinstance(args[0], str):
            notation = args[0]
            column = ord(notation[0]) - ord('a') + 1
            row = ord(notation[1]) - ord('1') + 1
        else:
            column = args[0]
            row = args[1]
        self.column = column
        self.row = row

    def __add__(self, other):
        return Position(self.column + other.column, self.row + other.row)

    def __sub__(self, other):
        return Direction(self.column - other.column, self.row - other.row)

    @property
    def is_valid(self):
        return 1 <= self.row <= 8 and 1 <= self.column <= 8

    def __str__(self):
        return '%s%s' % (chr(ord('a') - 1 + self.column), self.row)

    def __repr__(self):
        return '<%s>' % str(self)

    def __eq__(self, other):
        return self.row == other.row and self.column == other.column


class Direction:
    """
    Relative position diff, e.g. +2 columns, -1 row.
    """

    def __init__(self, column, row):
        self.column = column
        self.row = row

    @property
    def mirrors(self):
        yield self
        yield Direction(self.column, -self.row)
        yield Direction(-self.column, self.row)
        yield Direction(-self.column, -self.row)

    @property
    def switched(self):
        return Direction(self.row, self.column)

    @property
    def normalized(self):
        sign = lambda i: 0 if i == 0 \
                         else 1 if i > 0 \
                         else -1
        return Direction(sign(self.column), sign(self.row))

    def __repr__(self):
        return '<Bearing %s mark %s>' % (self.column, self.row)

    def __hash__(self):
        return self.column * 10 + self.row

    def __eq__(self, other):
        return self.row == other.row and self.column == other.column


class Move:
    """
    Particular move, e.g. e2e4.
    """

    def __init__(self, piece=None, new_pos=None, board=None, notation=None):
        """
        Can be initialized with:
          - piece & new_pos
          - board & notation
        """
        if piece and new_pos:
            self.piece = piece
            self.board = piece.board
            self.player = piece.player
            self.old_pos = piece.pos
            self.new_pos = new_pos
        elif board and notation:
            self.board = board
            self.old_pos = Position(notation[:2])
            self.new_pos = Position(notation[2:])

    def evaluate(self):
        score = 0
        captured = self.board[self.new_pos]
        if captured:
            score += captured.capture_score
        return score

    def evaluate_complete(self):
        score = self.evaluate()

        # FIXME should be done in a lighter manner
        # e.g. working with history of moves, being able to get back
        import copy
        board = copy.deepcopy(self.board)
        board.make_move(self)
        score += 0.3 * board.evaluate()

        return score

    def __str__(self):
        return '%s%s' % (self.old_pos, self.new_pos)

    def __repr__(self):
        return '<%s at %s>' % (str(self), hex(id(self)))


class Piece:
    def __init__(self, player, board, column, row):
        self.player = player
        self.board = board
        self.pos = Position(column, row)

    @property
    def all_dirs(self):
        dirs = []
        for dir in self.quadrant_dirs:
            dirs += dir.mirrors
            dirs += dir.switched.mirrors
        return set(dirs)

    def possible_moves(self):
        for dir in self.all_dirs:
            pos = self.pos + dir
            if self.check_move_to(pos):
                yield Move(self, pos)

    def check_move_to(self, pos):
        if not pos.is_valid:
            return False
        destination = self.board[pos]
        if destination and destination.player == self.player:
            return False
        # TODO check for check
        return True

    def straight_line_to(self, end_pos):
        dir = (end_pos - self.pos).normalized
        pos = self.pos + dir
        while pos != end_pos and pos.is_valid:
            if self.board[pos]:
                return False
            pos += dir
        return True

    def evaluate(self):
        score = 0
        for move in self.possible_moves():
            score += move.evaluate()
        return score

    def __repr__(self):
        return '<%s on %s>' % (self.sign, self.pos)

    @property
    def sign(self):
        return self.player.piece_sign(self.__class__)


class King(Piece):
    capture_score = 100
    quadrant_dirs = [
        Direction(0, 1),
        Direction(1, 1),
    ]


class StraightLineMixin:
    def check_move_to(self, pos):
        return super().check_move_to(pos) and self.straight_line_to(pos)


class Rook(StraightLineMixin, Piece):
    capture_score = 30
    quadrant_dirs = [Direction(0, i) for i in range(1, 9)]


class Bishop(StraightLineMixin, Piece):
    capture_score = 20
    quadrant_dirs = [Direction(i, i) for i in range(1, 9)]


class Queen(StraightLineMixin, Piece):
    capture_score = 50
    quadrant_dirs = Rook.quadrant_dirs + Bishop.quadrant_dirs


class Knight(Piece):
    capture_score = 15
    quadrant_dirs = [Direction(2, 1)]


class Pawn(Piece):
    capture_score = 1

    def __init__(self, *args, **kwargs):
        self.heading = kwargs.pop('heading')
        super().__init__(*args, **kwargs)

        self.dir_forward = Direction(0, self.heading)
        self.dir_captures = [
            Direction(1, self.heading),
            Direction(-1, self.heading),
        ]

    # TODO starting example
    @property
    def all_dirs(self):
        yield self.dir_forward
        for dir in self.dir_captures:
            capture = self.board[self.pos + dir]
            if capture and capture.player != self.player:
                yield dir

    def check_move_to(self, pos):
        if pos.column == self.pos.column:
            # TODO en passant
            destination = self.board[pos]
            if destination:
                return False
        return super().check_move_to(pos)


class Player:
    class Color(Enum):
        white = 0
        black = 1

    pieces_signs = {
        Color.white: {
            King: '♔',
            Queen: '♕',
            Rook: '♖',
            Bishop: '♗',
            Knight: '♘',
            Pawn: '♙',
        },
        Color.black: {
            King: '♚',
            Queen: '♛',
            Rook: '♜',
            Bishop: '♝',
            Knight: '♞',
            Pawn: '♟',
        },
    }

    def __init__(self, color, board):
        self.color = color
        self.board = board
        kwargs = {'player': self, 'board': self.board}
        if color == Player.Color.white:
            kwargs.update({'row': 1})
            pawn_kwargs = kwargs.copy()
            pawn_kwargs.update({'row': 2, 'heading': 1})
        else:
            kwargs.update({'row': 8})
            pawn_kwargs = kwargs.copy()
            pawn_kwargs.update({'row': 7, 'heading': -1})
        self.pieces = (
            [King(column=5, **kwargs)] +
            [Queen(column=4, **kwargs)] +
            [Bishop(column=c, **kwargs) for c in [3, 6]] +
            [Knight(column=c, **kwargs) for c in [2, 7]] +
            [Rook(column=c, **kwargs) for c in [1, 8]] +
            [Pawn(column=c, **pawn_kwargs) for c in range(1, 9)]
        )

    def rnd_move(self):
        while True:
            try:
                piece = random.choice(self.pieces)
                move = random.choice(list(piece.possible_moves()))
                return move
            except IndexError:
                pass

    def piece_sign(self, piece):
        return self.pieces_signs[self.color][piece]


class Board:
    def __init__(self):
        self.white = Player(Player.Color.white, self)
        self.black = Player(Player.Color.black, self)
        self.active = self.black
        self.opponent = self.white

    @property
    def pieces(self):
        return self.white.pieces + self.black.pieces

    def __getitem__(self, key):
        if isinstance(key, tuple):
            key = Position(key[0], key[1])
        elif isinstance(key, str):
            key = Position(key)
        return next(filter(lambda piece: piece.pos == key, self.pieces), None)

    def make_move(self, move):
        # TODO promotions

        if isinstance(move, str):
            move = Move(board=self, notation=move)

        captured = self[move.new_pos]
        if captured:
            captured.player.pieces.remove(captured)

        piece = self[move.old_pos]
        piece.pos = move.new_pos

    def bestmove(self):
        move = sorted([self.active.rnd_move() for _ in range(100)],
                      key=lambda move: move.evaluate_complete())[-1]
        self.make_move(move)
        return move

    def evaluate(self):
        sum_eval = lambda player: sum(map(lambda piece: piece.evaluate(),
                                          player.pieces))
        return sum_eval(self.active) - 2 * sum_eval(self.opponent)

    def __str__(self):
        board = ''
        for row in range(8, 0, -1):
            for column in range(1, 9):
                piece = self[column, row]
                board += piece.sign if piece else '.'
            board += '\n'
        return board


def main():
    board = Board()
    while True:
        cmd = input()
        log.debug('received: %s' % cmd)

        if cmd == 'quit':
            break
        elif cmd == 'uci':
            print('id name og-engine')
            print('id author og')
            print('uciok')
        elif cmd == 'isready':
            print('readyok')
        elif cmd.startswith('position '):
            board.make_move(cmd.split()[-1])
        elif cmd.startswith('go '):
            print('bestmove %s' % board.bestmove())

if __name__ == '__main__':
    log.addHandler(logging.FileHandler('og-engine.log'))
    log.setLevel(logging.DEBUG)

    log.debug('start')
    main()
    log.debug('end')
