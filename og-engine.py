#!/usr/bin/env python3

import logging

log = logging.getLogger(__name__)
log_handler = logging.FileHandler('og-engine.log')
log.addHandler(log_handler)
log.setLevel(logging.DEBUG)

log.debug('start')

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

log.debug('end')
