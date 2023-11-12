#!/usr/bin/env python3
import logging

import sudoku

#logging.basicConfig(
#	format='%(asctime)s: %(message)s',
#	filename='test.log', filemode='w',
#	level=logging.DEBUG
#)
logging.basicConfig(
	format='%(asctime)s: %(message)s',
	level=logging.DEBUG
)
sudo = sudoku.Importer('../mine.txt').sudoku
sudo.apply_givens()
sudo.print()

sol = sudo.solve()
if sol is not None:
	sol.print()
else:
	print('Sudoku has no solution')
