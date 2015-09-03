#!/usr/bin/env python3

from subprocess import Popen, PIPE
import unittest

import og_engine


class EngineTestCase(unittest.TestCase):

    def setUp(self):
        self.board = og_engine.Board()

    def assertPossibleMoves(self, piece, moves):
        """
        moves expected to be in form ['e2e4', 'd2d3'].
        """
        moves2 = map(lambda m: str(m), piece.possible_moves())
        self.assertEqual(set(moves), set(moves2))

    def test_possible_moves(self):
        pawn = self.board['e2']
        self.assertTrue(isinstance(pawn, og_engine.Pawn))
        self.assertPossibleMoves(pawn, ['e2e3'])

        queen = self.board['d1']
        self.assertTrue(isinstance(queen, og_engine.Queen))
        self.assertPossibleMoves(queen, [])

        self.board.make_move('e2e3')
        self.assertPossibleMoves(queen, ['d1e2', 'd1f3', 'd1g4', 'd1h5'])

    def test_history(self):
        history = lambda: list(map(lambda m: str(m), self.board.history))
        self.board.make_move('d2d4')
        self.assertEqual(history(), ['d2d4'])
        self.board.make_move('e7e5')
        self.assertEqual(history(), ['d2d4', 'e7e5'])
        self.assertEqual(self.board.history[-1].captured, None)
        self.board.make_move('d4e5')
        self.assertEqual(history(), ['d2d4', 'e7e5', 'd4e5'])
        self.assertEqual(str(self.board.history[-1].captured), '<♟ on e5>')


class EngineIOTestCase(unittest.TestCase):

    def setUp(self):
        self.proc = Popen(['./og_engine.py'], stdin=PIPE, stdout=PIPE)

    def tearDown(self):
        self.write('quit')
        self.proc.stdin.close()
        self.proc.stdout.close()

    def assertRead(self, msg):
        self.assertEqual(msg, self.read())

    def read(self):
        return self.proc.stdout.readline().decode('utf8').strip()

    def write(self, msg):
        self.proc.stdin.write(('%s\n' % msg).encode('utf8'))
        self.proc.stdin.flush()

    def test_start(self):
        self.write('uci')
        self.assertRead('id name og-engine')
        self.assertRead('id author og')
        self.assertRead('uciok')
        self.write('isready')
        self.assertRead('readyok')


if __name__ == '__main__':
    unittest.main()
