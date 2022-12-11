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


class Unsolvable(Exception):
	pass


class Cell:
	"""
	A single cell

	If its value is a number, the cell is either a given or its has
	a fixed value already.

	If its value is a set, it contains the numbers that have not been
	excluded yet.

	A cell is initialized with the full set of candidates of course.

	A cell 'knows' its row and column and the sudoku (parent) it
	belongs to.
	"""
	def __init__(self, N: int, r: int, c: int, parent):
		self._val = {i + 1 for i in range(N)}
		self._row = r
		self._col = c
		self._parent = parent

	@property
	def row(self):
		"""Row number of cell"""
		return self._row

	@property
	def col(self):
		"""Col number of cell"""
		return self._col

	@property
	def parent(self):
		"""Sudoku we belong to"""
		return self._parent

	@property
	def val(self):
		return self._val

	@val.setter
	def val(self, num):
		"""
		We protect the cell from being set to a different value if
		it already has one.

		We also protect the cell from being set to a value that has
		been excluded already.
		"""
		if isinstance(self._val, int):
			if self._val == num:
				return
			raise Unsolvable(f'Is already set to {self._val}')
		if num not in self._val:
			raise Unsolvable(f'Value {num} not available')
		self._val = num

	def xclude(self, num: int):
		"""
		Remove a candidate.

		Removing a candidate from a fixed cell is ignored.

		Removing a candidate from a cell where it does not exist is
		ignored.

		When excluding a value will leave a single candidate, the cell
		automatically takes on that value.
		"""
		if isinstance(self._val, int):
			return
		self._val.discard(num)
		if len(self._val) == 1:
			self._val = self._val.pop()

	def is_fix(self):
		return isinstance(self._val, int)

	def copy(self):
		"""
		Get a copy of the value for backup

		If the current value is and int, we can simply return it,
		but if it is a set we need to return a copy, not just a
		reference to it.
		"""
		if isinstance(self._val, int):
			return self._val
		else:
			return self._val.copy()

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


class Sudoku(types.SimpleNamespace):
	"""
	The cells in a sudoku are a simple linear list, containing
	the first row, then the second row, etc.

	The rows, columns and boxes are just references to the proper
	cells.

	The boxes are n columns wide and m rows hign. Box number 0 is
	in the upper left coner, boxes are numbered first left to right,
	then top to down.

	The `found` property is the counter that gets increased
	automatically whenever a cell changes from unknown to a fixed
	value. It is supposed to be increased exclusively in this way and
	can be used to check if any progress has been made.
	The `completed` property on the other hand is supposed to be
	increased by `found`, and found cleared whenever various tries
	had been made.
	"""

	def __init__(self, n: int = 3, m: int = 3):
		self.n = n
		self.m = m
		self.N = n * m
		self.digits = len(str(self.N))
		self.found = 0
		self.computed = 0
		self.remain = self.N * self.N
		self.cells = [
			Cell(self.N, i, j, self)
			for i in range(self.N)
			for j in range(self.N)
		]
		self.givens = []
		self.rows = [
			[self.cells[j * self.N + i] for i in range(self.N)]
			for j in range(self.N)
		]
		self.cols = [
			[self.cells[j + i * self.N] for i in range(self.N)]
			for j in range(self.N)
		]
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

	def cell(self, row: int, col: int) -> Cell:
		"""Cell by row and column numbers"""
		return self.cells[self.N * row + col]

	def row(self, cell: Cell):
		"""Row containing the given cell"""
		return self.rows[cell.row]

	def col(self, cell: Cell):
		"""Col containing the given cell"""
		return self.cols[cell.col]

	def box(self, cell: Cell):
		"""Box containing the given cell"""
		boxr = cell.row // self.m
		boxc = cell.col // self.n
		return self.boxs[boxr * self.m + boxc]

	def add_given(self, row: int, col: int, val: int) -> None:
		cell = self.cell(row, col)
		cell.val = val
		self.givens.append(cell)

	def apply_singlepos(self, x):
		"""
		Apply single position rule

		If for a number x only a single cell in
		a row, column or box exists where x is a candidate,
		set that cell to x
		"""
		cells = []
		for house in [self.rows, self.cols, self.boxs]:
			# When we searched a house for possible locations of x, we need to
			# differentiate between having found no cell (unsolvable), one
			# cell that is set already (rule does not apply), one cell that is
			# not already set (jay) and multiple cells. We use two variables:
			# `cell` which is set to the cell where the rule apples, or None,
			# and `found` if the value can be found at all
			cell = None
			found = False
			for c in house:
				if c.is_fix():
					if c.val == x:
						# Value already set in that house
						found = True
						break
				else:
					continue
				if x not in c.val:
					continue
				# c has x as candidate
				found = True
				if cell is None:
					# we found the first cell with x as candidate
					cell = c
				else:
					# rule not applicable in this house
					cell = None
					break
			if not found:
				raise Unsolvable(f'No position found for {x}')
			if cell:
				cell.val = x
				cells.append(cell)
		return cells

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
				cell = self.cell(r, c).print()
				for i in range(self.m):
					lines[i].append(cell[i])
					lines[i].append('|')
			for line in lines:
				print(''.join(line))
			print('+' + ('-' * cw + '+') * self.N)


class Importer(types.SimpleNamespace):

	def __init__(self, file):
		self.file = file
		self.importfile()

	def importfile(self):
		with open(self.file, 'r') as fd:
			line = fd.readline()
			if line.split() == 2:
				n, m = map(int, line.split())
				self.sudoku = Sudoku(n, m)
				off = 0
			else:
				self.sudoku = Sudoku(3, 3)
				self.importline(0, line)
				off = 1
			for r, line in enumerate(fd, start=off):
				self.importline(r, line)

	def importline(self, row, line):
		ele = line.split()
		if len(ele) != self.sudoku.N:
			raise ValueError(
				f'Error in line {row}: {self.sudoku.N} values expected'
			)
		for col, e in enumerate(ele):
			try:
				v = int(e)
			except ValueError:
				continue
			self.sudoku.add_given(row, col, v)
