import heapq
import copy
import time

def parse_board_string(board_str):
    """Parses an 81-character string into a 9x9 grid representation."""
    grid = []
    board_str = board_str.replace('.', '0')
    for r in range(9):
        row = [int(board_str[r*9 + c]) for c in range(9)]
        grid.append(row)
    return grid

def is_valid_board(board):
    """
    Validates the Sudoku board.
    Checks if there are any duplicate numbers in any row, column, or 3x3 box.
    Allows 0 (empty cells).
    """
    # Check rows
    for r in range(9):
        seen = set()
        for c in range(9):
            val = board[r][c]
            if val != 0:
                if val in seen:
                    return False
                seen.add(val)
                
    # Check columns
    for c in range(9):
        seen = set()
        for r in range(9):
            val = board[r][c]
            if val != 0:
                if val in seen:
                    return False
                seen.add(val)
                
    # Check 3x3 boxes
    for box_row in range(3):
        for box_col in range(3):
            seen = set()
            for r in range(3):
                for c in range(3):
                    val = board[box_row*3 + r][box_col*3 + c]
                    if val != 0:
                        if val in seen:
                            return False
                        seen.add(val)
                        
    return True

def get_candidates(board, r, c):
    """Returns the set of valid numbers (1-9) that can be placed in cell (r, c)."""
    if board[r][c] != 0:
        return set()
        
    candidates = set(range(1, 10))
    
    # Check row
    for col in range(9):
        if board[r][col] in candidates:
            candidates.remove(board[r][col])
            
    # Check column
    for row in range(9):
        if board[row][c] in candidates:
            candidates.remove(board[row][c])
            
    # Check 3x3 box
    box_r, box_c = (r // 3) * 3, (c // 3) * 3
    for row in range(box_r, box_r + 3):
        for col in range(box_c, box_c + 3):
            if board[row][col] in candidates:
                candidates.remove(board[row][col])
                
    return candidates

def get_mrv_cell(board):
    """
    Finds the empty cell with the Minimum Remaining Values (MRV) constraint.
    Returns: (row, col, candidates_set)
    If there are no empty cells, returns (None, None, set()).
    If there is an empty cell with NO candidates, returns (row, col, set()).
    """
    best_cell = None
    min_candidates = 10
    best_candidates = set()
    
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                candidates = get_candidates(board, r, c)
                num_candidates = len(candidates)
                
                # If a cell has 0 candidates, the current board state is unsolvable
                if num_candidates == 0:
                    return r, c, set()
                
                if num_candidates < min_candidates:
                    min_candidates = num_candidates
                    best_cell = (r, c)
                    best_candidates = candidates
                    
    if best_cell is None:
        return None, None, set()
        
    return best_cell[0], best_cell[1], best_candidates

def count_empty_cells(board):
    """Returns the count of empty cells on the board."""
    return sum(1 for r in range(9) for c in range(9) if board[r][c] == 0)

def solve_sudoku_astar_generator(initial_board, max_explored=15000):
    """
    An A* search solver implemented as a generator.
    Yields: (current_board, active_cell, explored_count, status)
    
    Status values:
    - 'running': Searching, yields intermediate board
    - 'solved': Solved successfully, yields solved board
    - 'unsolvable': Explored search space, no solution exists
    - 'limit_reached': Search space too large
    """
    # Check if initial board itself is valid
    if not is_valid_board(initial_board):
        yield initial_board, None, 0, 'invalid'
        return
        
    # Count initial empty cells
    initial_empty = count_empty_cells(initial_board)
    if initial_empty == 0:
        yield initial_board, None, 0, 'solved'
        return
        
    # Priority Queue state element: 
    # (priority_tuple, state_id, board, g_cost, path_history)
    # priority_tuple = (f_cost, h_cost, mrv_size)
    # - g_cost: number of moves filled from start
    # - h_cost: empty cells remaining
    # - f_cost = g_cost + h_cost (will be constant = initial_empty)
    # - mrv_size: size of candidate options (breaks ties by prioritizing cells with fewest options)
    # - state_id: counter to resolve comparisons of elements with same priority
    
    state_id_counter = 0
    
    # A state is stored as a tuple of tuples to be hashable if we want to track visited,
    # though with MRV DFS tree exploration it's mostly a tree search.
    board_tuple = tuple(tuple(row) for row in initial_board)
    
    # We find the MRV cell for the start state
    r_start, c_start, candidates_start = get_mrv_cell(initial_board)
    if r_start is not None and len(candidates_start) == 0:
        yield initial_board, None, 1, 'unsolvable'
        return
        
    mrv_size = len(candidates_start) if r_start is not None else 0
    
    # Initial state entry
    # g_cost = 0, h_cost = initial_empty, f_cost = 0 + initial_empty
    heap = []
    
    # Let's push initial states for each candidate of the MRV cell to boot the heap,
    # or just push the starting board itself.
    # Pushing starting board:
    heapq.heappush(heap, ((initial_empty, initial_empty, mrv_size), state_id_counter, board_tuple, 0))
    state_id_counter += 1
    
    explored_count = 0
    visited_boards = set() # Avoid expanding same states
    
    while heap:
        priority_tuple, _, current_board_tuple, g_cost = heapq.heappop(heap)
        
        # Convert to list representation
        current_board = [list(row) for row in current_board_tuple]
        
        if current_board_tuple in visited_boards:
            continue
        visited_boards.add(current_board_tuple)
        
        explored_count += 1
        
        # Check if solved
        h_cost = count_empty_cells(current_board)
        if h_cost == 0:
            if is_valid_board(current_board):
                yield current_board, None, explored_count, 'solved'
                return
            continue
            
        # Get MRV cell
        r, c, candidates = get_mrv_cell(current_board)
        
        # Yield the current board and the cell we are targeting for expansion
        yield current_board, (r, c), explored_count, 'running'
        
        if r is None:
            # No empty cells but not solved? Should not happen since h_cost > 0
            continue
            
        if len(candidates) == 0:
            # Dead end in search, prune
            continue
            
        # Branch on candidates for this MRV cell
        for val in candidates:
            # Create next state
            next_board = copy.deepcopy(current_board)
            next_board[r][c] = val
            
            # Check validity before putting into queue (early pruning)
            # Actually, because we only put valid candidates, it's valid locally.
            next_board_tuple = tuple(tuple(row) for row in next_board)
            
            if next_board_tuple not in visited_boards:
                next_g = g_cost + 1
                next_h = h_cost - 1
                next_f = next_g + next_h # which is initial_empty
                
                # Compute MRV of the new board state
                r_next, c_next, candidates_next = get_mrv_cell(next_board)
                
                # If it immediately creates a cell with 0 options, prune it
                if r_next is not None and len(candidates_next) == 0:
                    continue
                    
                next_mrv_size = len(candidates_next) if r_next is not None else 0
                
                # Push state
                # Note: We sort by f_cost (constant), h_cost ascending, then next_mrv_size.
                # Since h_cost is empty cells remaining, lower h_cost (more filled cells) is popped first.
                # This makes A* act as depth-first search along the most promising branches!
                heapq.heappush(
                    heap,
                    ((next_f, next_h, next_mrv_size), state_id_counter, next_board_tuple, next_g)
                )
                state_id_counter += 1
                
        if explored_count >= max_explored:
            yield current_board, None, explored_count, 'limit_reached'
            return
            
    yield None, None, explored_count, 'unsolvable'

def solve_sudoku_backtracking_generator(board, explored_ref=None, max_explored=15000):
    """
    Recursive backtracking solver implemented as a generator for UI visualization.
    Integrates the Minimum Remaining Values (MRV) heuristic for tight branching.
    Yields: (current_board, active_cell, explored_count, status)
    """
    if explored_ref is None:
        explored_ref = [0]
        
    # Check initial grid validity on first call
    if explored_ref[0] == 0:
        if not is_valid_board(board):
            yield board, None, 0, 'invalid'
            return False
            
    r, c, candidates = get_mrv_cell(board)
    if r is None:
        # Solved successfully!
        yield board, None, explored_ref[0], 'solved'
        return True
        
    if len(candidates) == 0:
        return False # Dead end, trigger backtracking
        
    for val in candidates:
        explored_ref[0] += 1
        if explored_ref[0] >= max_explored:
            yield board, None, explored_ref[0], 'limit_reached'
            return False
            
        board[r][c] = val
        yield board, (r, c), explored_ref[0], 'running'
        
        # Delegate generator steps recursively
        solved = yield from solve_sudoku_backtracking_generator(board, explored_ref, max_explored)
        if solved:
            return True
            
        # Revert change (backtrack)
        board[r][c] = 0
        yield board, (r, c), explored_ref[0], 'running'
        
    return False

def solve_sudoku_backtracking_fast(board, explored_ref=None):
    """
    Pure backtracking DFS with MRV for instant solve without generator or deepcopy overhead.
    Modifies board in-place. Returns True if solved, False otherwise.
    """
    if explored_ref is None:
        explored_ref = [0]
        
    r, c, candidates = get_mrv_cell(board)
    if r is None:
        return True
        
    if len(candidates) == 0:
        return False
        
    for val in candidates:
        explored_ref[0] += 1
        board[r][c] = val
        if solve_sudoku_backtracking_fast(board, explored_ref):
            return True
        board[r][c] = 0
        
    return False

# Preset puzzles representing easy, medium, hard, impossible, and empty puzzles.
# 0 represents an empty cell.
PRESETS = {
    "Easy": parse_board_string(
        "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    ),
    "Medium": parse_board_string(
        "..32....6....4..9.1.2...5..7...29....4.3.7.5....81...2..1...8.3.2..8....9....46.."
    ),
    "Hard (AI Escargot)": parse_board_string(
        "1...........712...3..5....9.2..9..3.8..6...1.45.........6.3.7.8...9..5.2..8......"
    ),
    "World's Hardest Sudoku (Inkala 2012)": parse_board_string(
        "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
    ),
    "Impossible (No Solution)": parse_board_string(
        "531.7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79" # Valid initially but mathematically unsolvable
    ),
    "Invalid (Duplicate in Row)": parse_board_string(
        "55..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79" # Double 5 in first row
    ),
    "Empty Grid": [[0]*9 for _ in range(9)]
}

def generate_random_puzzle_board(difficulty="Medium"):
    """
    Returns a preset or slightly randomized version of a preset board to act as 'Generate'.
    To keep it lightweight without needing a heavy generation engine, we return one of the preloaded seeds.
    """
    # Simple dictionary of multiple seeds for variance
    seeds = {
        "Easy": [
            "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79",
            "000079065000003002005060093340050106000000000608020045950080700200900000480310000"
        ],
        "Medium": [
            "..32....6....4..9.1.2...5..7...29....4.3.7.5....81...2..1...8.3.2..8....9....46..",
            "000600081070000039000008006000501904000070000302409000500100000980000040120003000"
        ],
        "Hard": [
            "3...8.......7....51..............36...2..4....7...........6.13..452...........8..",
            "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
        ]
    }
    
    import random
    options = seeds.get(difficulty, seeds["Medium"])
    chosen_str = random.choice(options)
    return parse_board_string(chosen_str)
