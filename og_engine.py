#!/usr/bin/env python3

import logging

log = logging.getLogger(__name__)


class Position:
    def __init__(self, row, column):
        self.row = row
        self.column = column

    def __add__(self, other):
        return Position(self.row + other.row, self.column + other.column)

    def __sub__(self, other):
        return Direction(self.row - other.row, self.column - other.column)

    @property
    def is_valid(self):
        return 1 <= self.row <= 8 and 1 <= self.column <= 8

    def __repr__(self):
        return '<%s%s>' % (self.row, chr(ord('a') - 1 + self.column))

    def __eq__(self, other):
        return self.row == other.row and self.column == other.column


class Direction:
    def __init__(self, row, column):
        self.row = row
        self.column = column

    @property
    def mirrors(self):
        yield self
        yield Direction(self.row, -self.column)
        yield Direction(-self.row, self.column)
        yield Direction(-self.row, -self.column)

    @property
    def switched(self):
        return Direction(self.column, self.row)

    @property
    def normalized(self):
        return Direction(1 if self.row else 0,
                         1 if self.column else 0)

    def __repr__(self):
        return '<Bearing %s mark %s>' % (self.row, self.column)

    def __hash__(self):
        return self.row * 10 + self.column

    def __eq__(self, other):
        return self.row == other.row and self.column == other.column


class Chessman:
    def __init__(self, player, board, row, column):
        self.player = player
        self.board = board
        self.pos = Position(row, column)

    @property
    def all_moves(self):
        moves = []
        for move in self.quadrant_moves:
            moves += move.mirrors
            moves += move.switched.mirrors
        return set(moves)

    def possible_moves(self):
        for move in self.all_moves:
            pos = self.pos + move
            if self.check_move(pos):
                yield pos

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


class King(Chessman):
    quadrant_moves = [
        Direction(0, 1),
        Direction(1, 1),
    ]


class StraightLineMixin:
    def check_move(self, pos):
        return super().check_move(pos) and self.straight_line_to(pos)


class Queen(StraightLineMixin, Chessman):
    quadrant_moves = Rook.quadrant_moves + Bishop.quadrant_moves


class Rook(StraightLineMixin, Chessman):
    quadrant_moves = [Direction(0, i) for i in range(1, 9)]


class Bishop(StraightLineMixin, Chessman):
    quadrant_moves = [Direction(i, i) for i in range(1, 9)]


class Knight(Chessman):
    quadrant_moves = [Direction(2, 1)]


class Pawn(Chessman):
    def __init__(self, *args, **kwargs):
        self.heading = kwargs.pop('heading')
        super().__init__(*args, **kwargs)

    # TODO starting example
    @property
    def all_moves(self):
        yield Direction(self.heading, 0)


class Player:
    def __init__(self, color, board):
        self.board = board
        kwargs = {'player': self, 'board': self.board}
        if color == 'white':
            kwargs.update({'row': 1})
            pawn_kwargs = kwargs.copy()
            pawn_kwargs.update({'row': 2, 'heading': 1})
        elif color == 'black':
            kwargs.update({'row': 8})
            pawn_kwargs = kwargs.copy()
            pawn_kwargs.update({'row': 7, 'heading': -1})
        else:
            raise ValueError('bad color')
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
        return


class Board:
    def __init__(self):
        self.white = Player('white', self)
        self.black = Player('black', self)
        self.active = self.black

    def __getitem__(self, key):
        for piece in self.white.pieces + self.black.pieces:
            if piece.pos == key:
                return piece
        return None


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
