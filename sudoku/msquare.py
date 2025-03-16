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
	row	and each column hold exactly N different numbers.

	The cells are a simple linear list, containing the first row, then
	the second row, etc.

	The rows and cols are lists containing just references to the actual cells.

	The `givens` are the values initially given.

	The `remain` property counts the number of cells that have an unknown value and
	must be decreased every time the value for a new cell becomes known.

	Properties:
	- N (int): number of rows and columns
	- digits (int): Number of digits needed to represent all values
		as decimal numbers
	- remain (int): Number of positions that don't have a fixed value
		yet. Cache to measure progress.
	- stack (list): Stack of state backups for backtracking
	- givens (list): List of positions and values given initially
	- cells (list): Linear list of all cells in the puzzle
	- myhouse (iterator): iterator over all kinds of houses. Returns
	  a function that takes a cell C as argument and returns that house
	  of the given kind that contains C.
	- myrules (iterator): iterator over rules to apply. A rule is a
	  method without an argument that returns True if any progress in
	  finding a solution has been made. It searches
	  various patterns and deducts new values or exclusions.
	"""
	def __init__(self, N: int = 5, mkcell=None, name=None):
		"""
		Create a magic square

		Args:
			N: number of rows and columns.
			mkcell: constructor for a cell taking arguments
				row, column and the container object.
		"""
		self.N = N
		self.mkcell = mkcell or cell.NCell
		if name is not None:
			self.name = name
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
		self.myrules = [self.rule_singlecandidate, self.rule_singlepos]

	def getcell(self, row: int, col: int):
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
		for house in self.myhouse:
			for c in house(cell):
				if c is not cell: c.xclude(cell.val)

	def setgivens(self, *args):
		"""
		Set multiple givens

		Each must be given as a (row, col, val) tuple. Note that this
		may already rise an Unsolvable exception.
		"""
		for row, col, val in args:
			self.setcell(self.getcell(row, col), val, "Set Givens")

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

	def housename(self, memberlist, n) -> str:
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

	def rule_singlecandidate(self) -> bool:
		"""
		Check if a cell has only one remaining candidate

		If yes, the cell is set to the candidate. This may rise an Unsolvable
		exception.

		Return:
			True if a new cell got a fixed value
		"""
		for cell in self.cells:
			if cell.is_fix() or len(cell.val) > 1: continue
			log.debug('Found single candidate')
			self.setcell(cell, cell.getany(), 'single-candidate')
			return True
		return False

	def try_singlepos_x(self, x) -> bool:
		"""
		Apply single position rule

		If for a number x only a single cell in
		a row, column or box exists where x is a candidate,
		set that cell to x

		Return:
			True if a new cell got a fixed value
		"""
		log.debug(f'Try singlepos for {x}')
		for houses in self.houses:
			# When we searched a house for possible locations of x, we need to
			# differentiate between having found no cell (unsolvable), one
			# cell that is set already (rule does not apply), one cell that is
			# not already set (jay) and multiple cells. We use two variables:
			# `cell` which is set to the cell where the rule applies, or None,
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
					return True
		return False

	def rule_singlepos(self):
		"""
		Try singleposition rule for all numbers
		"""
		for x in range(1, self.N + 1):
			if self.try_singlepos_x(x):
				return True
		return False

	def apply_rules(self) -> bool:
		for rule in self.myrules:
			if rule():
				return True
		return False

	def findtry(self) -> cell.NCell:
		"""
		Find an unsolved cell with the smallest number of potential values
		"""
		res = None
		for c in self.cells:
			if c.is_fix(): continue
			if len(c.val) == 2:
				return c
			if res is None or len(c.val) < len(res.val):
				res = c
		return res

	def solve_r(self):
		level = len(self.stack)
		try:
			while self.apply_rules() and self.remain > 0:
				pass
		except Unsolvable as e:
			log.debug(f'[{level}] Applying rules: {e}')
			return False
		if self.remain == 0:
			return True
		self.print()
		cell = self.findtry()
		log.debug(f'Pivot {cell.name} with {len(cell.val)} candidates')
		tryset = cell.state()
		for cand in tryset:
			log.debug(f'[{level}] Try setting {cell.name} = {cand}')
			self.backup()
			self.setcell(cell, cand, f'try-{cand}')
			try:
				if self.solve_r():
					return True
			except Unsolvable as e:
				log.debug(f'[{level}] {cand} leads to {e}')
			self.restore()
		raise Unsolvable(f'Tried all candidates for {cell.name}')

	def solve(self):
		if self.solve_r():
			return self
		else:
			return None
