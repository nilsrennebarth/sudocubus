#!/usr/bin/env python3
import types
import logging

import cell
from exceptions import Unsolvable

log = logging.getLogger(__name__)


class Magicsquare(types.SimpleNamespace):
	"""
	A magic square.

	For a solution of a magic square each cell must have a value such that each
	row	and each column hold exactly N differnent numbers.

	The cells are a simple linear list, containing the first row, then
	the second row, etc.

	The rows and cols are lists containing just references to the actual cells.

	The `givens` are the values initially given.

	The `found` property is a list that gets added to automatically, whenever
	a cell changes from unknown to a fixed value.  It is supposed to be added
	to exclusively in this way and can be used to check if any progress has
	been made.  The remain` property on the other hand is supposed to be
	decreased by the length of `found`, and `found` cleared whenever various
	tries had been made.

	"""
	def __init__(self, N: int = 5, mkcell=None):
		"""
		Create a magic square

		Args:
			N: number of rows and columns.
			mkcell: constructor for a cell taking arguments
				row, column and the container object.
		"""
		self.N = N
		self.mkcell = mkcell or cell.NCell
		self.digits = len(str(self.N))
		self.remain = self.N * self.N
		self.stack = []
		self.givens = []
		self.cells = [
			self.mkcell(self.N, i, j, self)
			for i in range(self.N)
			for j in range(self.N)
		]
		self.rows = [
			[self.cells[j * self.N + i] for i in range(self.N)]
			for j in range(self.N)
		]
		self.cols = [
			[self.cells[j + i * self.N] for i in range(self.N)]
			for j in range(self.N)
		]
		self.houses = [self.rows, self.cols]
		self.housenames = ['row', 'col']
		self.myhouse = [self.row, self.col]

	def cell(self, row: int, col: int):
		"""Cell by row and column numbers"""
		return self.cells[self.N * row + col]

	def row(self, cell):
		"""Row containing the given cell"""
		return self.rows[cell.row]

	def col(self, cell):
		"""Column containing the given cell"""
		return self.cols[cell.col]

	def setcell(self, cell, value, comment):
		"""
		Set cell to value

		After setting the cell is done also remove the value from all
		other candidate cell in all other houses the cell is in. This
		may raise an Unsolvable exception.
		"""
		log.debug(f'Set {cell.name} = {value} ({comment})')
		cell.val = value
		self.remain -= 1
		for func in self.myhouse:
			for c in func(cell):
				if c is not cell: c.xclude(cell.val)

	def state(self):
		"""
		Value representing the complete state

		This is a value that will be pushed to or popped off the stack.
		It must be a copy containing no references into the original state,
		and must contain everything that we want to restore.

		For a sudoku this is the number of remaining cells to be solved and
		a list of current cells.
		"""
		return self.remain, [cell.state() for cell in self.cells]

	def backup(self):
		"""
		Push a backup of our current state on the stack
		"""
		self.stack.append(self.state())

	def restore(self):
		"""
		Restore the cell values from the state at top of the stack
		"""
		remain, states = self.stack.pop()
		for i, val in enumerate(states):
			self.cells[i].restore(val)
		self.remain = remain

	def add_given(self, row: int, col: int, val: int) -> None:
		"""
		Register a given value
		"""
		self.givens.append((self.cell(row, col), val))

	def apply_givens(self):
		for cell, val in self.givens:
			try:
				self.setcell(cell, val, 'given')
			except Unsolvable as e:
				log.debug(f'Error applying givens: {e}')
				return False
		return True

	def housename(self, memberlist, n):
		"""
		Return human readable name for a given house

		Args:
			memberlist: List containing the house
			n: Number in the list

		Return:
			Name of the given house
		"""
		for idx, mlist in enumerate(self.houses):
			if memberlist is mlist:
				return f'{self.housenames[idx]}({n + 1})'
		raise ValueError(f'Unknown Container {memberlist}')

	def rule_singlecandidate(self):
		"""
		Check if a cell has only one remaining candidate

		If yes, the cell is set to the candidate. This may rise an Unsolvable
		exception.
		"""
		for cell in self.cells:
			if cell.is_fix() or len(cell.val) > 1: continue
			log.debug('Found single candidate')
			self.setcell(cell, cell.getany(), 'single-candidate')

	def try_singlepos_x(self, x):
		"""
		Apply single position rule

		If for a number x only a single cell in
		a row, column or box exists where x is a candidate,
		set that cell to x
		"""
		log.debug(f'Try singlepos for {x}')
		for houses in self.houses:
			# When we searched a house for possible locations of x, we need to
			# differentiate between having found no cell (unsolvable), one
			# cell that is set already (rule does not apply), one cell that is
			# not already set (jay) and multiple cells. We use two variables:
			# `cell` which is set to the cell where the rule apples, or None,
			# and `found` if the value can be found at all
			for n, house in enumerate(houses):
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
					where = self.housename(houses, n)
					raise Unsolvable(f'In {where}: no {x}')
				if cell:
					self.setcell(cell, x, f'single-position-{x}')

	def rule_singlepos(self):
		"""
		Try singleposition rule for all numbers
		"""
		for x in range(1, self.N + 1):
			self.try_singlepos_x(x)
