#!/usr/bin/env python3
import types
import logging
import re

from msquare import BasePuzzle, Magicsquare
from cell import BaseCell, NCell
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


class Eulero(BasePuzzle):
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
	- pairs (dict): A dictionary where the keys are all tuples (i, j) with
	  i in 0..n-1 and j in 0..n-1. Each value is a set of cells in the primary
	  magic square. The set contains those positions where the given tuple can
	  still occur. Initially, when the Eulero is empty and no givens are set,
	  all positions are possible. Whenever a cell receives a value, the sets can
	  be reduced accordingly.
	"""
	def __init__(self, n: int = 5):
		super().__init__()
		self.n = n
		self.digits = len(str(n))
		self.square = [Magicsquare(n) for i in range(2)]
		self.square[0].name = 'Left'
		self.square[0].pos = 0
		self.square[0].parent = self
		self.square[1].name = 'Right'
		self.square[1].pos = 1
		self.square[1].parent = self
		self.remain = 2 * self.square[0].remain
		self.pairs = {
			(i, j): {c for c in self.square[0].cells}
			for i in range(1, n + 1) for j in range(1, n + 1)
		}
		self.myrules = self.square[0].myrules + self.square[1].myrules + [
			self.rule_singlepairpos
		]

	def pairname(self, pair):
		return chr(ord('A') - 1 + pair[0]) + '{n:>{w}}'.format(n=pair[1], w=self.digits)

	def posname(self, row, col):
		return f'({row + 1},{col + 1})'

	def pairstate(self):
		return {
			pair: val.copy() if isinstance(val, set) else val
			for pair, val in self.pairs.items()
		}

	def state(self):
		"""
		Current state of the puzzle
		"""
		return [(s.state(), s.remain) for s in self.square], self.pairstate()

	def restorestate(self, state):
		"""
		Restore puzzle to the given state
		"""
		squares, self.pairs = state
		for i, (s, r) in enumerate(squares):
			self.square[i].restorestate(s)
			self.square[i].remain = r

	def pcell(self, row, col):
		"""Primary cell at a position"""
		return self.square[0].getcell(row, col)

	def findtry(self) -> NCell:
		"""
		Find an unsolved cell with the smalles number of potential values
		"""
		res = None
		if self.square[0].remain != 0:
			res = self.square[0].findtry()
		if res is not None and len(res.val) == 2:
			return res
		r2 = self.square[1].findtry()
		if res is None:
			return r2
		elif r2 is None:
			return res
		elif len(res.val) < len(r2.val):
			return res
		else:
			return r2

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
					f'Pair {self.pairname(pair)} already at {self.posname(pairval.row, pairval.col)})'
				)
			log.warning(f'Pair {self.pair2str(pair)} has already been set')
			return
		log.debug(f'Pair {self.pairname(pair)} found at {self.posname(row, col)}')
		self.pairs[pair] = self.pcell(row, col)
		# Remove left value from cells where the right value is already set to
		# the right value of the pair. Same for the right value
		for (c0, c1) in zip(self.square[0].cells, self.square[1].cells):
			if c0 is cell: continue
			if c0.val == pair[0]:
				c1.xclude(pair[1])
			if c1.val == pair[1]:
				c0.xclude(pair[0])

	def cellgotval(self, square, cell, value):
		"""
		Remove potential pair locations when a cell receives a value

		Whenever a cell in any of the two magic squares receives a value, we
		can exclude various locations from holding specific pairs.

		If the other cell at the same position already has a value, we must
		check that this pair hasn't been placed anywhere else, or throw an
		Unsolvable exception. We then replace the set value of the pair with
		the (primary) cell at the given position, thus locating the pair.

		Let C be the primary cell at (row, col). For all pairs P that have
		`value` in position pos, we discard all cells != C from all houses that
		C is in from the set of P.
		"""
		self.remain -= 1
		pos, row, col = square.pos, cell.row, cell.col
		othercell = self.square[1-pos].getcell(row, col)
		# Construct tuples from values at the variable positions pos and 1-pos
		lpair = [-1, -1]
		lpair[pos] = value
		if othercell.is_fix():
			# We found the location of a new pair
			lpair[1-pos] = othercell.val
			self.setpair(tuple(lpair), row, col)
		else:
			# We fixed one value (left or right) in a previously empty cell.
			# Exclude all values from the other cell position, where the
			# corresponding pair has been found already
			for otherval in othercell.val.copy():
				lpair[1-pos] = otherval
				if isinstance(self.pairs[tuple(lpair)], BaseCell):
					log.debug(f'Exclude {otherval} from {othercell.name}')
					othercell.xclude(otherval)

	def cellnotval(self, square, cell, value):
		"""
		Remove potential pair locations when a value has been excluded from a cell
		"""
		pos, row, col = square.pos, cell.row, cell.col
		cell = self.pcell(row, col)
		lpair = [-1, -1]
		lpair[pos] = value
		for otherval in range(1, self.n + 1):
			lpair[1 - pos] = otherval
			pair = tuple(lpair)
			locations = self.pairs[pair]
			if isinstance(locations, BaseCell): continue
			if cell not in locations: continue
			# log.debug(f'{self.pairname(pair)} not at {self.posname(row,col)}')
			locations.remove(cell)
			if len(locations) == 0:
				raise Unsolvable(f'No location for {self.pairname(pair)}')

	def rule_singlepairpos(self) -> bool:
		"""
		Check if there is a pair that can only occur at a single position. If
		yes, set both values at that position (left and right) to the fixed value
		and return True, otherwise return False.
		"""
		for pair, val in self.pairs.items():
			if isinstance(val, BaseCell): continue
			if len(val) > 1: continue
			if len(val) == 0:
				raise Unsolvable(f'No remaining location for pair {pair}')
			pro = False
			cell = val.pop()  # cell is in left Magicsquare
			log.debug(f'Pair {self.pair2str(pair)} must be at ({cell.row + 1}, {cell.col + 1})')
			if isinstance(cell.val, set):
				pro = True
				cell.setval(pair[0], "Left of single location pair")
			othercell = self.square[1].getcell(cell.row, cell.col)
			if isinstance(othercell.val, set):
				pro = True
				othercell.setval(pair[1], "Right of single location pair")
			self.pairs[pair] = cell
			return pro

	def setgivens(self, *args):
		"""
		Set multiple givens in an Eulero

		Each must be given as a (pos, row, col, val) tuple, where pos is
		the position of the magic square (left 0, right 1) and row, col,
		val have the usual meaning for magic squares.
		"""
		for pos, row, col, val in args:
			msquare = self.square[pos]
			msquare.getcell(row,col).setval(val, "Set Givens")

	def cell2str(self, cell):
		"""
		String representation of a cell value.

		The left cell is rendered as an uppercase char, the right cell as a number,
		blank for each if no value has been found yet. Then padded to the max width + 1
		"""
		v1 = chr(ord('A') + cell.val - 1) if isinstance(cell.val, int) else ' '
		v2 = self.square[1].getcell(cell.row, cell.col).val
		v2 = str(v2) if isinstance(v2, int) else ' '
		v2 += ' ' * (len(str(self.n)) - len(v2))
		return v1 + v2

	def pair2str(self, p) -> str:
		"""String representation of an eulero cell value"""
		return chr(ord('A') + p[0] - 1) + str(p[1])

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

	def print(self):
		self.quickprint()

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

if __name__ == '__main__':
	import sys

	logging.basicConfig(
		format='%(levelname).1s:%(message)s', level=logging.DEBUG,
		stream=sys.stdout
	)
	puzzle = Eulero.fromfile(sys.argv[1])
	puzzle.quickprint()
	sol = puzzle.solve()
	if sol is None:
		print('Eulero has no solution')
	else:
		sol.print()
