#!/usr/bin/env python3
"""
Solve sudokus

A Sudoku is a square of cells arranged in N rows and columns, In the standard
case, N is equal to 9. N is written as a product nxm, and the NxN rectangle is
completely covered by N `boxes`, rectangles of size nxm. Again in the standard
case n and m are both equal to 3. A sudoku is solved when the numbers 1..N are
entered in the cells such that each row, each column and each box holds every
number exacty once.

A sudoku is started with a certain number of `givens`, cells where a number has
alrady been placed.

A sudoku is implemented as a list of NxN objects of type Cell. Rows, columns
and boxes are lists of references to the corresponding cells.
"""
import types
import logging

from cell import NCell
import msquare
from exceptions import Unsolvable

log = logging.getLogger(__name__)


def intornone(i):
	"""Helper: String to int or None"""
	try:
		return int(i)
	except ValueError:
		return None


class Cell(NCell):
	"""
	A single cell
	"""
	def print(self):
		"""
		ASCII art representation

		We return a list of strings, all of the same length
		"""
		def cnd(r, c):
			num = r * n + c + 1
			if num in self._val:
				return f'{num:{digits}}'
			else:
				return ' ' * digits

		def fix():
			"""Fixed cell"""
			width = (digits + 1) * m - 1
			res = [' ' * width for ll in range(n)]
			res[n // 2] = f'({self._val})'.center(width)
			return res

		def uns():
			"""Unsolved cell"""
			return [
				' '.join([cnd(r, c) for c in range(n)])
				for r in range(m)
			]

		n = self.parent.n
		m = self.parent.m
		digits = self.parent.digits
		return fix() if self.is_fix() else uns()


class Sudoku(msquare.Magicsquare):
	"""
	A sudoku puzzle

	A sudoku is a magic square with additional structure: boxes.
	For a solution, not only rows and columns but also all boxes
	must not contain the same value in different positions.
	The N of the magic square is the product of the numbers n and m
	being the width and height of rectangles that cover the square.

	As usual, the boxes are just references to the proper cells.

	The boxes are n columns wide and m rows hign. Box number 0 is
	in the upper left coner, boxes are numbered first left to right,
	then top to down.
	"""
	def __init__(self, n: int = 3, m: int = 3):
		super().__init__(n * m, Cell)
		self.n = n
		self.m = m
		self.boxs = [
			[
				self.cells[
					r * self.n + j +
					self.N * (c * self.m + i)
				]
				for i in range(self.m)
				for j in range(self.n)
			]
			for c in range(self.n)
			for r in range(self.m)
		]
		self.houses.append(self.boxs)
		self.housenames.append('box')
		self.myhouse.append(self.box)

	def box(self, cell: Cell):
		"""Box containing the given cell"""
		boxr = cell.row // self.m
		boxc = cell.col // self.n
		return self.boxs[boxr * self.m + boxc]

	def print(self):
		"""
		ASCII art representation

		We assume that a fixed width character is about twice as tall
		as it is wide.

		A single cell is made (digits + 1) * n wide and m lines high.
		If it is solved, it shows its number in the middle, repeated
		three times with no spaces in between. If it is still unsolved,
		the candidates are shown at their respective places,
		"""
		cw = (self.digits + 1) * self.m - 1
		print('+' + ('-' * cw + '+') * self.N)
		for r in range(self.N):
			lines = [['|'] for cl in range(self.m)]
			for c in range(self.N):
				cell = self.getcell(r, c).print()
				for i in range(self.m):
					lines[i].append(cell[i])
					lines[i].append('|')
			for line in lines:
				print(''.join(line))
			print('+' + ('-' * cw + '+') * self.N)

	@classmethod
	def fromfile(cls, file: str):
		"""
		Import sudoku from file

		The file must start with the numbers n and m on the first line.
		For a standard sudoku where n and m are both 3, that line can be
		omitted however.
		The next lines must yield n * m strings when split at whitespace,
		and each of the strings that can be converted to an int represents
		a given.
		"""

		off = 0
		with open(file, 'r') as fd:
			for row, line in enumerate(fd):
				if row == 0:
					if len(line.split()) == 2:
						n, m = map(int, line.split())
						sudoku = cls(n, m)
						off = 1
						continue
					else:
						sudoku = cls(3,3)
				sudoku.setgivens(*[(row - off, col, val)
					for col, val in enumerate(map(intornone, line.split()))
					if val is not None
				])
		return sudoku
