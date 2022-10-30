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


class Cell:

	def __init__(self, N: int):
		self.num = 0
		self.candidates = {i+1 for i in range(N)}


class Sudoku(types.SimpleNamespace):

	def __init__(self, n: int = 3, m: int = 3):
		self.n = n
		self.m = m
		self.N = n * m
		self.cells = [Cell(self.N) for i in range(self.N * self.N)]
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
					r * self.m + j +
					self.N * (c * self.n + i)
				]
				for i in range(self.n)
				for j in range(self.m)
			]
			for c in range(self.m)
			for r in range(self.n)
		]

	def print(self):
		for r in range(self.N):
			print(' '.join(
				str(c.num)
				for c in self.cells[r * self.N:(r + 1) * self.N]
			))


def test1():
	s = Sudoku(2, 3)
	for n, row in enumerate(s.rows):
		for c in row:
			c.num = n + 1
	s.print()


def test2():
	s = Sudoku(2, 3)
	for n, col in enumerate(s.cols):
		for c in col:
			c.num = n + 1
	s.print()


def test3():
	s = Sudoku(2, 3)
	for n, box in enumerate(s.boxs):
		for m, c in enumerate(box):
			c.num = 10 * (n + 1) + m + 1
	s.print()


if __name__ == '__main__':
	test1()
	print('')
	test2()
	print('')
	test3()
