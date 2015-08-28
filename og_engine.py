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

    def __repr__(self):
        return '<Bearing %s mark %s>' % (self.row, self.column)

    def __hash__(self):
        return self.row * 10 + self.column

    def __eq__(self, other):
        return self.row == other.row and self.column == other.column


class Chessman:
    def move(self, direction):
        return self.pos + direction

    @property
    def all_moves(self):
        moves = []
        for move in self.quadrant_moves:
            moves += move.mirrors
        return set(moves)

    def possible_moves(self):
        for move in self.all_moves:
            pos = self.move(move)
            if pos.is_valid():  # TODO and not self.endangered_at(pos):
                yield pos


class King(Chessman):
    quadrant_moves = [
        Direction(0, 1),
        Direction(1, 1),
        Direction(1, 0),
    ]


class Board:
    pass


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
