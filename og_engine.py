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
            self.old_pos = piece.pos
            self.new_pos = new_pos
        elif board and notation:
            self.board = board
            self.old_pos = Position(notation[:2])
            self.new_pos = Position(notation[2:])
            self.piece = self.board[self.old_pos]

        self.player = self.piece.player
        self.captured = self.board[self.new_pos]

    def evaluate(self):
        score = 0
        captured = self.board[self.new_pos]
        if captured:
            score += captured.capture_score
        return score

    def evaluate_complete(self):
        log.debug('evaluating %s...' % self)
        score = self.evaluate()

        board = self.board.sandbox
        board.make_move(self)
        board.undo_move()
        score += 0.3 * board.evaluate()

        log.debug('evaluated %s as %f' % (self, score))
        return score

    def __str__(self):
        return '%s%s%s' % (self.piece.sign, self.old_pos, self.new_pos)

    @property
    def short_str(self):
        return '%s%s' % (self.old_pos, self.new_pos)

    def __repr__(self):
        return '<%s at %s>' % (self, hex(id(self)))

    # TODO is it right? it can mean a movement of another piece at another time
    def __eq__(self, other):
        if isinstance(other, str):
            return self.short_str == other
        return self.old_pos == other.old_pos and self.new_pos == other.new_pos


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

    def leave(self):
        """Removes itself from playing pieces."""
        self.player.pieces.remove(self)

    def revive(self):
        """Returns to game."""
        self.player.pieces.append(self)

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
                log.debug('rnd_move: %s' % move)
                return move
            except IndexError:
                pass

    def piece_sign(self, piece):
        return self.pieces_signs[self.color][piece]


class Board:
    def __init__(self, sandbox=False):
        self.white = Player(Player.Color.white, self)
        self.black = Player(Player.Color.black, self)
        self.history = []
        self.sandbox = Board(sandbox=True) if not sandbox else None

    @property
    def active(self):
        return list({self.white, self.black} - {self.history[-1].player})[0] \
               if self.history else self.white

    @property
    def opponent(self):
        return list({self.white, self.black} - {self.active})[0]

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

        if self.sandbox:
            assert len(self.history) == len(self.sandbox.history)
            if self.history:
                assert self.history[-1] == self.sandbox.history[-1]

        if isinstance(move, str):
            move = Move(board=self, notation=move)

        if move.captured:
            move.captured.leave()

        piece = self[move.old_pos]
        piece.pos = move.new_pos

        self.history.append(move)

        if self.sandbox:
            self.sandbox.make_move(move.short_str)

    def undo_move(self):
        move = self.history.pop()

        piece = self[move.new_pos]
        piece.pos = move.old_pos

        if move.captured:
            move.captured.revive()

        if self.sandbox:
            self.sandbox.undo_move()

    def sync_moves(self, moves):
        recreate = False
        if len(moves) <= len(self.history):
            recreate = True
        else:
            for i, move in enumerate(moves[:len(self.history)]):
                if self.history[i] != move:
                    log.debug('history diverges at %d: my %s x their %s'
                              % (i, self.history[i], move))
                    recreate = True
                    break

        if recreate:
            log.debug('recreating board')
            self.__init__()

        for move in moves[len(self.history):]:
            self.make_move(move)

    def bestmove(self):
        move = sorted([self.active.rnd_move() for _ in range(20)],
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


def send(msg):
    log.debug('sending: %s' % msg)
    print(msg)

def main():
    while True:
        cmd = input()
        log.debug('received: %s' % cmd)

        if cmd == 'quit':
            break
        elif cmd == 'uci':
            send('id name og-engine')
            send('id author og')
            send('uciok')
        elif cmd == 'isready':
            send('readyok')
        elif cmd == 'ucinewgame':
            board = Board()
        elif cmd.startswith('position startpos'):
            moves = cmd.split()[3:]
            board.sync_moves(moves)
        elif cmd.startswith('go '):
            send('bestmove %s' % board.bestmove().short_str)

if __name__ == '__main__':
    log.addHandler(logging.FileHandler('og-engine.log'))
    log.setLevel(logging.DEBUG)

    log.debug('start')
    main()
    log.debug('end')
