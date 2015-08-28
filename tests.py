#!/usr/bin/env python3

from subprocess import Popen, PIPE
import unittest

import og_engine


class EngineTestCase(unittest.TestCase):

    def setUp(self):
        self.board = og_engine.Board()

    def assertEqualMoves(self, moves, moves2):
        """
        moves expected to be Move instances,
        moves2 expected to be in form ['e2e4', 'd2d3'].
        """
        moves = map(lambda m: str(m), moves)
        self.assertEqual(set(moves), set(moves2))

    def test_possible_moves(self):
        pawn = self.board['e2']
        self.assertTrue(isinstance(pawn, og_engine.Pawn))
        moves = pawn.possible_moves()
        self.assertEqualMoves(moves, ['e2e3'])


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
