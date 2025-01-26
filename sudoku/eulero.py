#!/usr/bin/env python3
import types
import logging
import re

import msquare
from cell import BaseCell
from exceptions import Unsolvable

log = logging.getLogger(__name__)


def euleroval(v:str):
	"""
	Split a letter + numeric string for an eulero

	The String is supposed to represent a given in an Eulero. The first part
	is composed of uppercase letters (only the first one matters currently) and
	may be empty. The second part is composed of decimal digits and may be empty
	as well.

	Return:
	  A list of (pos, val) tuples. `pos` is the number of the Eulero square (left 0,
	  right 1) `val` is the value to be set in the magic square at that position.
	"""
	res = []
	match = re.match('([A-Z]*)([0-9]*)', v)
	ltr, num = match.group(1, 2)
	if len(ltr) > 0:
		res.append((0, ord(ltr[0]) - ord('A') + 1))
	if len(num) > 0:
		res.append((1, int(num)))
	return res


class Eulerosquare(msquare.Magicsquare):
	"""A magic square inside of an Eulero

	There are only two differences to a regular magic square: An Eulerosquare
	knows its parent, the Eulero itself, and its position inside it(left: 0 or
	right: 1), and the setpos method is intercepted to also exclude the
	corresponding pairs of the eulero.
	"""


class Eulero(types.SimpleNamespace):
	"""
	A general eulero puzzle is a square NxN where each cell has two positions, a
	left and a right one.

	The left positions form a magic square, i.e. there are N different symbols
	in each row, such that each column holds N different values as well. The
	right positions form a magic square as well. The added condition is that
	every combination of left and right value occurs only once in the whole
	square.

	In puzzles (e.g. janko.at), the values in the left positions are usually
	letters of the latin alphabet, the values in the right positions are the
	numbers 1..N.

	It has been shown that Euleros exist for every number except 6.

	Properties:
	- square (list): A list of two magic squares, the first (primary) square
	  represents the numbers in the left positions, the second square represents
	  the numbers in the right positions.
	- pairpos (dict): A dictionary where the keys are all tuples (i, j) with
	  i in 0..n-1 and j in 0..n-1. Each value is a set of cells in the primary
	  magic square. The set contains those positions where the given tuple can
	  still occur. Initially, when the Eulero is empty and no givens are set,
	  all positions are possible. Whenever a cell receives a value, the sets can
	  be reduced accordingly.
	"""
	def __init__(self, n: int = 5):
		self.n = n
		self.square = [msquare.Magicsquare(n) for i in range(2)]
		self.square[0].name = 'Left'
		self.square[1].name = 'Right'
		self.pairs = {
			(i, j): {c for c in self.square[0].cells}
			for i in range(1, n + 1) for j in range(1, n + 1)
		}

	def pcell(self, row, col):
		"""Primary cell at a position"""
		return self.square[0].cell(row, col)

	def setpair(self, pair:tuple, row, col):
		"""
		Set location of a pair

		Must be called whenever both locations in an Eulero cell, receive a
		fixed value. This will mark the pair as being found and will exclude
		the left value from cells where the right value has already been found
		and the right value from cells where the left value has already been
		found.
		"""
		pairval = self.pairs[pair]
		cell = self.pcell(row, col)
		if isinstance(pairval, BaseCell):
			# Pair has been found already
			if pairval.row != row or pairval.col != col:
				raise Unsolvable(
					f'Pair {pair} already at ({pairval.row}{pairval.col})'
				)
			log.warning(f'Pair {pair} has already been set')
			return
		log.debug(f'Pair {pair} found at ({row}, {col})')
		self.pairs[pair] = self.pcell(row, col)
		# Remove left value from cells where the right value is already set to
		# the right value of the pair. Same for the right value
		for (c0, c1) in zip(self.square[0].cells, self.square[1].cells):
			if c0 is cell: continue
			if c0.val == pair[0]:
				c1.xclude(pair[1])
			if c1.val == pair[1]:
				c0.xclude(pair[0])

	def setcell(self, pos:int, row:int, col:int, value:int):
		"""
		Remove pairs when a cell receives a value

		Whenever a cell in any of the two magic squares receives a value, we
		can exclude various location from holding specific pairs.

		If the other cell at the same position already has a value, we must
		check that this pair hasn't been placed anywhere else, or throw an
		Unsolvable exception. We then replace the set value of the pair with
		the (primary) cell at the given position, thus locating the pair.

		Let C be the primary cell at (row, col). For all pairs P that have
		`value` in position pos, we discard all cells != C from all houses that
		C is in from the set of P.
		"""
		othercell = self.square[1-pos].cell(row, col)
		# Construct tuples from values at the variable positions pos and 1-pos
		lpair = [-1, -1]
		lpair[pos] = value
		if othercell.is_fix():
			lpair[1-pos] = othercell.val
			pair = tuple(lpair)
			self.setpair(pair, row, col)
		for otherval in range(1, self.n + 1):
			lpair[1-pos] = otherval
			pair = tuple(lpair)
			locations = self.pairs[pair]
			if not isinstance(locations, set):
				continue
			current = self.pcell(row, col)
			for house in self.square[0].myhouse:
				for c in house(current):
					if c is not current:
						locations.discard(c)
						if len(locations) == 0:
							raise Unsolvable(
								f'No remaining location for pair {pair}'
							)

	def setgivens(self, *args):
		"""
		Set multiple givens in an Eulero

		Each must be given as a (pos, row, col, val) tuple, where pos is
		the position of the magic square (left 0, right 1) and row, col,
		val have the usual meaning for magic squares.
		"""
		for pos, row, col, val in args:
			msquare = self.square[pos]
			msquare.setcell(msquare.cell(row,col), val, "Set Givens")
			self.setcell(pos, row, col, val)

	def cell2str(self, cell):
		"""
		String representation of a cell value.

		The left cell is rendered as an uppercase char, the right cell as a number,
		blank for each if no value has been found yet. Then padded to the max width + 1
		"""
		v1 = chr(ord('A') + cell.val - 1) if isinstance(cell.val, int) else ' '
		v2 = self.square[1].cell(cell.row, cell.col).val
		v2 = str(v2) if isinstance(v2, int) else ' '
		v2 += ' ' * (len(str(self.n)) - len(v2))
		return v1 + v2

	def quickprint(self, withlines=True):
		"""
		Simple ASCII output for debugging

		only show already fixed values, using 1 or 2 digits for the
		numbers, optionally add lines around.
		"""
		lines = [
			' '.join(self.cell2str(self.pcell(row, col)) for col in range(self.n))
		    for row in range(self.n)
		]
		width = len(str(self.n)) + 2
		if withlines:
			for r in range(self.n):
				lines[r] = f'|{lines[r]}|'
			border = '+' + ('-' * (width * self.n - 1)) + '+'
			lines.append(border)
			lines.insert(0, border)
		print('\n'.join(lines))

	@classmethod
	def fromfile(cls, file:str):
		"""
		Import Eulero from file

		The first line of the file is optional and if present must contain two
		numbers separated by whitespace used for the class constructor. Otherwise
		the class constructor is called with the number of items when the line is
		split by whitespace.
		Each line must then yield the same number of items when split by
		whitespace. Whenever an item is zero or more uppercase letters followed
		by zero or more decimal digits it is a given in that same position, the
		letter(s) giving the value for the left and the number the value for the
		right square.
		"""

		off = 0
		with open(file, 'r') as fd:
			for row, line in enumerate(fd):
				if row == 0:
					if len(line.split()) == 2:
						n, m = map(int, line.split())
						puzzle = cls(n, m)
						off = 1
						continue
					else:
						puzzle = cls(len(line.split()))
				puzzle.setgivens(*[(pos, row - off, col, val)
					 for col, fullval in enumerate(line.split())
					 for pos, val in euleroval(fullval)]
				)
		return puzzle
