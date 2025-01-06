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

	note that the internal representation actually uses the
	value 0..N-1.

	A cell starts as a set holding the values 1..N. As long as
	its value has not yet been determined, its value is the set
	of all (still) possible values. Once its value is determined,
	its value is the corresponding number.
	"""
	def __init__(self, N: int, r: int, c: int, parent):
		super().__init__(r, c, parent)
		self._val = {i + 1 for i in range(N)}

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
			raise Unsolvable(f'{self.name} already set to {self._val}')
		if num not in self._val:
			raise Unsolvable(f'{self.name} value {num} not available')
		self._val = num

	def xclude(self, num: int):
		"""
		Remove a candidate.

		Removing a candidate from a fixed cell is ignored.

		Removing a candidate from a cell where it does not exist is
		ignored.

		Removing the last candidate from a cell raises an Unsolvable
		exception.
		"""
		if isinstance(self._val, int):
			return
		self._val.discard(num)
		if len(self._val) == 0:
			raise Unsolvable(f'No candidate for {self.name}')

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
