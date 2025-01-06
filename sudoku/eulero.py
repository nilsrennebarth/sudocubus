#!/usr/bin/env python3
import types
import logging

import cell
import msquare

log = logging.getLogger(__name__)


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
		everywhere = {c for c in self.square[0].cells}
		self.pairs = {
			(i, j): everywhere.copy()
			for i in range(n) for j in range(n)
		}
