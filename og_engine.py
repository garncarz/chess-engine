#!/usr/bin/env python3

import logging

log = logging.getLogger(__name__)


class Position:
    def __init__(self, row, column):
        self.row = row
        self.column = column

    def __add__(self, other):
        return Position(self.row + other.row, self.column + other.column)

    def is_valid(self):
        return 1 <= self.row <= 8 and 1 <= self.column <= 8

    def __repr__(self):
        return '<%s%s>' % (self.row, chr(ord('a') - 1 + self.column))


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

    def __repr__(self):
        return '<Bearing %s mark %s>' % (self.row, self.column)

    def __hash__(self):
        return self.row * 10 + self.column

    def __eq__(self, other):
        return self.row == other.row and self.column == other.column


class Chessman:
    def __init__(self, row, column):
        self.pos = Position(row, column)

    def move(self, direction):
        return self.pos + direction

    @property
    def all_moves(self):
        moves = []
        for move in self.quadrant_moves:
            moves += move.mirrors
            moves += move.switched.mirrors
        return set(moves)

    def possible_moves(self):
        for move in self.all_moves:
            pos = self.move(move)
            # TODO could be used as a decorator
            if pos.is_valid():  # TODO and not self.endangered_at(pos):
                yield pos

    def __repr__(self):
        return '<%s on %s>' % (self.__class__.__name__, self.pos)


class King(Chessman):
    quadrant_moves = [
        Direction(0, 1),
        Direction(1, 1),
    ]


class Queen(Chessman):
    quadrant_moves = Rook.quadrant_moves + Bishop.quadrant_moves


class Rook(Chessman):
    quadrant_moves = [Direction(0, i) for i in range(1, 8)]


class Bishop(Chessman):
    quadrant_moves = [Direction(i, i) for i in range(1, 8)]


class Knight(Chessman):
    quadrant_moves = [Direction(2, 1)]


class Pawn(Chessman):
    # TODO starting example
    def possible_moves(self):
        pos = self.move(Direction(1, 0))
        if pos.is_valid():
            yield pos



class Player:
    def __init__(self, color):
        if color == 'white':
            row, pawn_row = 1, 2
        elif color == 'black':
            row, pawn_row = 8, 7
        else:
            raise ValueError('bad color')
        self.pieces = (
            [King(row, 5)] +
            [Queen(row, 4)] +
            [Bishop(row, c) for c in [3, 6]] +
            [Knight(row, c) for c in [2, 7]] +
            [Rook(row, c) for c in [1, 8]] +
            [Pawn(pawn_row, c) for c in range(1, 8)]
        )


class Board:
    def __init__(self):
        self.white = Player('white')
        self.black = Player('black')


def main():
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
            print('bestmove e7e6')

if __name__ == '__main__':
    log.addHandler(logging.FileHandler('og-engine.log'))
    log.setLevel(logging.DEBUG)

    log.debug('start')
    main()
    log.debug('end')
