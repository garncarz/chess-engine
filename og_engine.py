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
        return Direction(1 if self.column else 0,
                         1 if self.row else 0)

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

    def __init__(self, *args):
        """
        Can be initialized both as old_pos, new_pos or 'e2e4'.
        """
        if isinstance(args[0], str):
            notation = args[0]
            old_pos = Position(notation[:2])
            new_pos = Position(notation[2:])
        else:
            old_pos = args[0]
            new_pos = args[1]
        self.old_pos = old_pos
        self.new_pos = new_pos

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
            if self.check_move(pos):
                yield Move(self.pos, pos)

    def check_move(self, pos):
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

    def __repr__(self):
        return '<%s on %s>' % (self.__class__.__name__, self.pos)

    @property
    def sign(self):
        return self.player.piece_sign(self.__class__)


class King(Piece):
    quadrant_dirs = [
        Direction(0, 1),
        Direction(1, 1),
    ]


class StraightLineMixin:
    def check_move(self, pos):
        return super().check_move(pos) and self.straight_line_to(pos)


class Rook(StraightLineMixin, Piece):
    quadrant_dirs = [Direction(0, i) for i in range(1, 9)]


class Bishop(StraightLineMixin, Piece):
    quadrant_dirs = [Direction(i, i) for i in range(1, 9)]


class Queen(StraightLineMixin, Piece):
    quadrant_dirs = Rook.quadrant_dirs + Bishop.quadrant_dirs


class Knight(Piece):
    quadrant_dirs = [Direction(2, 1)]


class Pawn(Piece):
    def __init__(self, *args, **kwargs):
        self.heading = kwargs.pop('heading')
        super().__init__(*args, **kwargs)

    # TODO starting example
    @property
    def all_dirs(self):
        yield Direction(0, self.heading)


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

    # TODO
    def bestmove(self):
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
        if isinstance(move, str):
            move = Move(move)
        piece = self[move.old_pos]
        piece.pos = move.new_pos

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
        else:
            print('bestmove %s' % board.active.bestmove())

if __name__ == '__main__':
    log.addHandler(logging.FileHandler('og-engine.log'))
    log.setLevel(logging.DEBUG)

    log.debug('start')
    main()
    log.debug('end')
