=================
 Sudoku strategy
=================

We start with an all candidates open empty sudoku.

The givens, a list of cells obtained by their (row, col) corrdinates are set
to their values.

- For each cell remove the value from all houses the cell is in.
- This may lead more cells being solved, so repeat this with all the
  newly solved cells until no more progress is made.

This is called harvesting.

- Apply the single position rule for all numbers. 
- Do the harvesting

We now reached a state where no more progress can be made by our simple rules,
so we are down to guessing with backtrace:

- Find a cell with the minimum number of candidates, we can stop immediately
  when we find a cell with 2 candidates.
- for each possible candidate c of C:

  - save the current state on top of the stack
  - set the cell to c
  - try to solve now.
  - on an Unsolvable exception:

    - restore the state
    - exclude c from the candidates.

- when we reached the last candidate c, we can set C to value c and run the
  solve algorithm again.

We either reach a solution (number of unsolved cells == 0) or have proven the
sudoku to be insolvable (stack is empty and we got an Unsolvable exception).
