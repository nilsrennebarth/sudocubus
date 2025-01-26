#!/usr/bin/env python3
import logging

from sudoku import Sudoku

#logging.basicConfig(
#	format='%(asctime)s: %(message)s',
#	filename='test.log', filemode='w',
#	level=logging.DEBUG
#)
logging.basicConfig(
	format='%(asctime)s: %(message)s',
	level=logging.DEBUG
)
sudo = Sudoku.fromfile('../mine.txt')
sudo.print()

sol = sudo.solve()
if sol is not None:
	sol.print()
else:
	print('Sudoku has no solution')
