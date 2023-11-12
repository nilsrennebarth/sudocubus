#!/usr/bin/env python3
import types
import logging

import msquare

log = logging.getLogger(__name__)


class Eulero(types.SimpleNamespace):
	"""
	A general eulero puzzle is a square NxN where each cell has two positions,
	a left and a right one.

	The left positions form a magic square, i.e. there are N different symbols
	in each row, such that each column holds N different values as well. The
	right positions form a magic square as well. The added condition is that
	every combination of left an right value occurs only once in the whole
	square. The values in the left positions are usually letters of the latin
	alphabet, the values in the right positions are numbers 1..N.

	It has been shown that Euleros exist for every number except 6.
	"""
	def __init__(self, n: int = 5):
		self.n = n
		self.square = [msquare.Magicsquare(n) for i in range(2)]
