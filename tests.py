#!/usr/bin/env python3

from subprocess import Popen, PIPE
import unittest

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
