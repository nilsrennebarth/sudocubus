#!/usr/bin/env python3
import logging

from eulero import Eulero

#logging.basicConfig(
#	format='%(asctime)s: %(message)s',
#	filename='test.log', filemode='w',
#	level=logging.DEBUG
#)
logging.basicConfig(
	format='%(asctime)s: %(message)s',
	level=logging.DEBUG
)
puzzle = Eulero.fromfile('../eu100.txt')
puzzle.quickprint()

# sol = sudo.solve()
# if sol is not None:
# 	sol.print()
# else:
# 	print('Sudoku has no solution')
