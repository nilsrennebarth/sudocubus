#!/usr/bin/env python3
import types
import logging

import cell
import msquare
from exceptions import Unsolvable

log = logging.getLogger(__name__)


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
		self.pairs = {
			(i, j): {c for c in self.square[0].cells}
			for i in range(n) for j in range(n)
		}

	def pcell(self, row, col):
		"""Primary cell at a position"""
		return self.square[0].cell(row, col)

	def setpair(self, pair:tuple, row, col):
		"""
		Set location of a tuple
		"""
		pairval = self.pairs[pair]
		cell = self.pcell(row, col)
		if isinstance(pairval, cell.BaseCell):
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
		for otherval in range(self.n):
			lpair[1-pos] = otherval
			pair = tuple(lpair)
			locations = self.pairs[pair]
			if not isinstance(locations, set):
				continue
			current = self.pcell(row, col)
			for house in self.square[0].houses:
				for c in house(current):
					if c is not current:
						locations.discard(c)
						if len(locations) == 0:
							raise Unsolvable(
								f'No remaining location for pair {pair}'
							)
