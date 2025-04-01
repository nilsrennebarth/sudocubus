#!/usr/bin/env python3
"""
A Cell in a symbol puzzle
"""
import logging
from exceptions import Unsolvable

log = logging.getLogger(__name__)


class BaseCell:
	"""
	Base class for a cell. A cell knows its location and the
	puzzle it is part of.
	"""
	def __init__(self, r: int, c: int, parent):
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
		"""Puzzle we belong to"""
		return self._parent

	@property
	def name(self):
		loc = getattr(self._parent, 'name', '')
		if loc:
			loc += ': '
		return f'{loc}cell({self.row + 1}, {self.col + 1})'


class NCell(BaseCell):
	"""
	A cell that can hold exactly one value in the range 1..N

	A cell starts as a set holding the values 1..N. As long as
	its value has not yet been determined, its value is the set
	of all (still) possible values. Once its value is determined,
	its value is the corresponding number.
	"""
	def __init__(self, N: int, r: int, c: int, parent):
		super().__init__(r, c, parent)
		self._val = {i for i in range(1, N + 1)}

	@property
	def val(self):
		return self._val

	def setval(self, num, comment='unknown reason'):
		"""
		Set cell to given value

		We protect the cell from being set to a different value if
		it already has one.

		We also protect the cell from being set to a value that has
		been excluded already.

		When the value actually changed from a set to a fixed value,
		we propagate this to the parent puzzle by calling its cellgotvalue
		method.
		"""
		log.debug(f'Set {self.name} = {num} ({comment})')
		if isinstance(self._val, int):
			if self._val == num:
				return
			raise Unsolvable(f'{self.name} already set to {self._val}')
		if num not in self._val:
			raise Unsolvable(f'{self.name} value {num} not available')
		if hasattr(self.parent, 'cellnotval'):
			# Exlude all other currently existing values
			for v in self._val - {num}:
				self.parent.cellnotval(self, v)
		self._val = num
		if hasattr(self.parent, 'cellgotval'):
			self.parent.cellgotval(self, num)

	def xclude(self, num: int):
		"""
		Remove a candidate.

		Removing a candidate from a fixed cell is ignored.

		Removing a candidate from a cell where it does not exist is
		ignored.

		Removing the last candidate from a cell raises an Unsolvable
		exception.

		When the value was indeed included before, propagate this
		to the parent puzzle by calling its cellnotvalue method.
		"""
		if isinstance(self._val, int):
			return
		if num not in self._val:
			return
		self._val.discard(num)
		if len(self._val) == 0:
			raise Unsolvable(f'No candidate for {self.name}')
		if hasattr(self.parent, 'cellnotval'):
			self.parent.cellnotval(self, num)

	def is_fix(self):
		return isinstance(self._val, int)

	def getany(self):
		"""
		Get any candidate for the cell
		"""
		if self.is_fix():
			raise ValueError(f'Cell C({self.row}, {self.col}) is fixed')
		return iter(self._val).__next__()

	def state(self):
		"""
		Value representing the current state.

		Must not contain any reference to the original. Thus we need to
		use a copy for sets.
		"""
		if isinstance(self._val, int):
			return self._val
		else:
			return self._val.copy()

	def restore(self, val):
		"""
		Restore value from a backup
		"""
		self._val = val
