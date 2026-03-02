import customtkinter as ctk
from tkinter import messagebox
from TkToolTip import ToolTip
import copy
import heapq
from sudoku_analysis import open_analysis_window
import random


class BitmaskSolver:

    def __init__(self):
        self.rows=[0]*9
        self.cols=[0]*9
        self.boxes=[0]*9

    def _get_box_index(self,r,c):
        return (r//3)*3+(c//3)

    def _initialize_masks(self,board):
        self.rows=[0]*9
        self.cols=[0]*9
        self.boxes=[0]*9
        empty_cells=[]
        for r in range(9):
            for c in range(9):
                if board[r][c]!=0:
                    val=board[r][c]-1
                    mask=(1 << val)
                    self.rows[r]|=mask
                    self.cols[c]|=mask
                    self.boxes[self._get_box_index(r, c)]|=mask
                else:
                    empty_cells.append((r, c))
        return empty_cells

    def solve(self,board):
        empty_cells=self._initialize_masks(board)
        empty_cells.sort(key=lambda cell:self._count_options(cell[0],cell[1]))
        if self._backtrack(board,empty_cells,0):
            return board
        return None

    def count_solutions(self,board,limit=2):
        self._initialize_masks(board)
        empty_cells = [(r, c) for r in range(9) for c in range(9) if board[r][c]==0]
        return self._backtrack_count(board,empty_cells,0,limit)

    def _count_options(self,r,c):
        box_idx =self._get_box_index(r,c)
        taken =self.rows[r] | self.cols[c] | self.boxes[box_idx]
        options =0
        for k in range(9):
            if not (taken & (1 << k)):
                options +=1
        return options

    def _backtrack(self, board, empty_cells, idx):
        if idx ==len(empty_cells):
            return True

        r,c =empty_cells[idx]
        box_idx =self._get_box_index(r,c)
        taken = self.rows[r] | self.cols[c] | self.boxes[box_idx]

        for k in range(9):
            mask = 1 << k
            if not (taken & mask):
                board[r][c] =k + 1
                self.rows[r] |=mask
                self.cols[c] |=mask
                self.boxes[box_idx] |=mask

                if self._backtrack(board,empty_cells,idx + 1):
                    return True

                self.rows[r] &=~mask
                self.cols[c] &=~mask
                self.boxes[box_idx] &=~mask
                board[r][c] =0
        return False

    def _backtrack_count(self,board,empty_cells,idx,limit):
        if idx ==len(empty_cells):
            return 1
        r, c = empty_cells[idx]
        box_idx =self._get_box_index(r, c)
        taken =self.rows[r] | self.cols[c] | self.boxes[box_idx]
        count =0
        for k in range(9):
            mask =1 << k
            if not (taken & mask):
                board[r][c] =k + 1
                self.rows[r] |=mask
                self.cols[c] |=mask
                self.boxes[box_idx] |=mask
                count += self._backtrack_count(board,empty_cells,idx+1,limit)
                self.rows[r] &=~mask
                self.cols[c] &=~mask
                self.boxes[box_idx] &=~mask
                board[r][c] =0
                if count >=limit:
                    return count
        return count


def _standalone_is_valid(board,row,col,num):
    for i in range(9):
        if board[row][i] ==num and i !=col:
            return False
        if board[i][col] ==num and i !=row:
            return False
    br, bc = 3 * (row //3), 3*(col//3)
    for i in range(br,br + 3):
        for j in range(bc,bc + 3):
            if board[i][j] ==num and (i, j) !=(row,col):
                return False
    return True


def _standalone_get_candidates(board,row,col):
    if board[row][col]!= 0:
        return set()
    candidates =set(range(1, 10))
    candidates -=set(board[row])
    candidates -={board[i][col] for i in range(9)}
    br, bc = 3*(row // 3), 3*(col // 3)
    for i in range(br,br + 3):
        for j in range(bc,bc + 3):
            candidates.discard(board[i][j])
    return candidates


def solve_greedy_standalone(board):
    board = copy.deepcopy(board)
    while True:
        pq = []
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    cands = _standalone_get_candidates(board, r, c)
                    if not cands:
                        return None
                    heapq.heappush(pq, (len(cands), r, c, cands))
        if not pq:
            return board
        _, r, c, cands = heapq.heappop(pq)
        cands = _standalone_get_candidates(board, r, c)
        if not cands:
            return None
        board[r][c] = min(cands)
    return board


def solve_dnc_standalone(board):
    board = copy.deepcopy(board)
    return _dnc_helper(board)

def _dnc_helper(board):
    best_cell = None
    best_candidates = None
    min_count = 10
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                cands = _standalone_get_candidates(board, r, c)
                cnt = len(cands)
                if cnt == 0:
                    return None
                if cnt < min_count:
                    min_count = cnt
                    best_cell = (r, c)
                    best_candidates = cands
                    if cnt == 1:
                        break
        if min_count == 1:
            break
    if best_cell is None:
        return board
    row, col = best_cell
    for val in best_candidates:
        board[row][col] = val
        result = _dnc_helper(board)
        if result is not None:
            return result
        board[row][col] = 0
    return None


def solve_dp_standalone(board):
    board = copy.deepcopy(board)
    rows = [0] * 9; cols = [0] * 9; boxes = [0] * 9
    empty = []
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                mask = 1 << (board[r][c] - 1)
                rows[r] |= mask; cols[c] |= mask
                boxes[(r // 3) * 3 + c // 3] |= mask
            else:
                empty.append((r, c))

    def count_opts(r, c):
        taken = rows[r] | cols[c] | boxes[(r//3)*3 + c//3]
        return bin(~taken & 0x1ff).count('1')

    empty.sort(key=lambda cell: count_opts(cell[0],cell[1]))

    def bt(idx):
        if idx == len(empty):
            return True
        r, c = empty[idx]
        bi = (r // 3)*3 + c//3
        taken = rows[r] | cols[c] | boxes[bi]
        for k in range(9):
            m = 1 << k
            if not (taken & m):
                board[r][c] = k + 1
                rows[r] |= m; cols[c] |= m; boxes[bi] |= m
                if bt(idx + 1):
                    return True
                rows[r] &= ~m; cols[c] &= ~m; boxes[bi] &= ~m
                board[r][c] = 0
        return False

    return board if bt(0) else None


def solve_backtracking_standalone(board):
    board = copy.deepcopy(board)
    rows = [0] *9; cols = [0] *9; boxes = [0]* 9
    empty = []
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                mask = 1 << (board[r][c] - 1)
                rows[r] |= mask; cols[c] |= mask
                boxes[(r // 3)* 3 + c //3] |= mask
            else:
                empty.append((r, c))

    def count_opts(r, c):
        taken = rows[r] | cols[c] | boxes[(r // 3)*3 + c //3]
        return bin(~taken & 0x1ff).count('1')

    empty.sort(key=lambda cell: count_opts(cell[0], cell[1]))

    def bt(idx):
        if idx == len(empty):
            return True
        r, c = empty[idx]
        bi = (r// 3) *3 + c //3
        taken = rows[r] | cols[c] | boxes[bi]
        for k in range(9):
            m = 1 << k
            if not (taken & m):
                board[r][c] = k + 1
                rows[r] |= m; cols[c] |= m; boxes[bi] |= m
                if bt(idx + 1):
                    return True
                rows[r] &= ~m; cols[c] &= ~m; boxes[bi] &= ~m
                board[r][c] = 0
        return False

    return board if bt(0) else None


def solve_hybrid_standalone(board):
    board = copy.deepcopy(board)
    for br in range(0,9,3):
        for bc in range(0,9,3):
            for r in range(br,br +3):
                for c in range(bc,bc +3):
                    if board[r][c] == 0:
                        cands = _standalone_get_candidates(board,r,c)
                        if len(cands) ==1:
                            board[r][c] =cands.pop()
    return solve_dp_standalone(board)


BENCHMARK_SOLVERS = {
    "Greedy":           solve_greedy_standalone,
    "Divide & Conquer": solve_dnc_standalone,
    "DP (Bitmask)":     solve_dp_standalone,
    "Backtracking":     solve_backtracking_standalone,
    "Hybrid (D&C+DP)":  solve_hybrid_standalone,
}

####
# ---------- Shared helper functions ----------

def get_base_pattern():
    """Create a valid completed Sudoku board using a mathematical pattern."""
    def pattern(r, c):
        return (3 * (r % 3) + r // 3 + c) % 9
    nums = list(range(1, 10))
    random.shuffle(nums)
    return [[nums[pattern(r, c)] for c in range(9)] for r in range(9)]


def shuffle_board(board):
    """Randomise a valid board by shuffling rows/columns within bands."""
    for i in range(0, 9, 3):
        block = board[i:i + 3]
        random.shuffle(block)
        board[i:i + 3] = block
    board = list(map(list, zip(*board)))
    for i in range(0, 9, 3):
        block = board[i:i + 3]
        random.shuffle(block)
        board[i:i + 3] = block
    board = list(map(list, zip(*board)))
    return board

def generate_puzzle(difficulty="Medium"):
    """Generate a valid Sudoku puzzle with a unique solution."""
    full_board = shuffle_board(get_base_pattern())
    solution = copy.deepcopy(full_board)
    board = copy.deepcopy(full_board)

    if difficulty == "Easy":
        target_holes = 30
    elif difficulty == "Medium":
        target_holes = 45
    else:
        target_holes = 55

    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)

    solver = BitmaskSolver()
    holes = 0

    for r, c in cells:
        if holes >= target_holes:
            break
        backup = board[r][c]
        board[r][c] = 0
        solutions = solver.count_solutions(copy.deepcopy(board), limit=2)
        if solutions != 1:
            board[r][c] = backup
        else:
            holes += 1

    return board, solution

def generate_benchmark_puzzle(holes=45):
    """Generate a puzzle with a given number of holes for benchmarking."""
    full = shuffle_board(get_base_pattern())
    board = copy.deepcopy(full)
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    for i in range(min(holes, len(cells))):
        r, c = cells[i]
        board[r][c] = 0
    return board



BENCHMARK_BG   = "#1a1a2e"
BENCHMARK_CARD = "#16213e"
BENCHMARK_ACCENT = "#e94560"

COMPLEXITY_TABLE = [
    ["Greedy (PQ)",      "O(n\u00b2 log n)", "Fast but incomplete",  "O(n\u00b2)",   "No backtracking; may fail"],
    ["Divide & Conquer", "O(9^n)",      "Fast with MRV",        "O(n)",    "Recursive subproblem split"],
    ["DP (Bitmask)",     "O(9^n)",      "Near-instant",         "O(n+27)", "O(1) constraint via bits"],
    ["Backtracking",     "O(9^n)",      "Near-instant w/ MRV",  "O(n+27)", "Classic + bitmask + MRV"],
    ["Hybrid (D&C+DP)",  "O(9^n)",      "Fastest practical",    "O(n+27)", "Two-phase: D&C then DP"],
]


def open_benchmark_window(parent_root):
    """
    Open a Toplevel window that benchmarks all 5 solvers and
    displays results as a matplotlib bar chart + complexity table.
    """
    win = tk.Toplevel()
    win.title("Algorithm Comparison \u2014 Sudoku Solver Benchmark")
    win.geometry("960x800")
    win.configure(bg=BENCHMARK_BG)
    win.resizable(False, False)

    tk.Label(
        win, text="\U0001f4ca  Algorithm Comparison",
        font=("Segoe UI", 22, "bold"), bg=BENCHMARK_BG, fg="#ffffff",
    ).pack(pady=(15, 5))

    status_lbl = tk.Label(
        win, text="Click 'Run Benchmark' to start...",
        font=("Segoe UI", 12), bg=BENCHMARK_BG, fg="#a8b2d1",
    )
    status_lbl.pack(pady=(0, 10))

    results_frame = tk.Frame(win, bg=BENCHMARK_BG)
    results_frame.pack(fill="both", expand=True, padx=20, pady=5)

    # --- Control buttons ---
    btn_frame = tk.Frame(win, bg=BENCHMARK_BG)
    btn_frame.pack(pady=10)

    tk.Button(
        btn_frame, text="\U0001f680  Run Benchmark",
        font=("Segoe UI", 11, "bold"),
        bg=BENCHMARK_ACCENT, fg="#ffffff",
        activebackground="#ff6b81", relief="flat",
        padx=15, pady=6, cursor="hand2",
        command=lambda: _run_benchmark_thread(parent_root, status_lbl, results_frame),
    ).pack(side="left", padx=5)

    tk.Button(
        btn_frame, text="Close",
        font=("Segoe UI", 11, "bold"),
        bg="#8892b0", fg=BENCHMARK_BG,
        relief="flat", padx=15, pady=6, cursor="hand2",
        command=win.destroy,
    ).pack(side="left", padx=5)

    # --- Complexity table ---
    _build_complexity_table(win)

def _build_complexity_table(parent):
    """Render the algorithm complexity analysis table in the given parent."""
    table_frame = tk.Frame(parent, bg=BENCHMARK_CARD, bd=1, relief="solid")
    table_frame.pack(fill="x", padx=20, pady=(5, 10))

    tk.Label(
        table_frame, text="Algorithm Complexity Analysis",
        font=("Segoe UI", 13, "bold"), bg=BENCHMARK_CARD, fg="#ffffff",
    ).pack(anchor="w", padx=10, pady=(8, 5))

    headers = ["Algorithm", "Time (Worst)", "Time (Practical)", "Space", "Key Characteristic"]
    grid_f = tk.Frame(table_frame, bg=BENCHMARK_CARD)
    grid_f.pack(fill="x", padx=10, pady=(0, 8))

    for ci, h in enumerate(headers):
        tk.Label(
            grid_f, text=h, font=("Segoe UI", 9, "bold"),
            bg="#0f3460", fg="#ffffff", padx=8, pady=4, anchor="w",
        ).grid(row=0, column=ci, sticky="nsew", padx=1, pady=1)

    for ri, row_data in enumerate(COMPLEXITY_TABLE):
        bg = BENCHMARK_CARD if ri % 2 == 0 else "#1f2b47"
        for ci, val in enumerate(row_data):
            tk.Label(
                grid_f, text=val, font=("Consolas", 9),
                bg=bg, fg="#a8b2d1", padx=8, pady=3, anchor="w",
            ).grid(row=ri + 1, column=ci, sticky="nsew", padx=1, pady=1)

    for ci in range(len(headers)):
        grid_f.columnconfigure(ci, weight=1)

    analysis = (
        "Analysis Summary:\n"
        "\u2022 n = number of empty cells.  All exact solvers share O(9^n) worst-case time.\n"
        "\u2022 Greedy is the only incomplete solver \u2014 it cannot guarantee a solution.\n"
        "\u2022 Bitmask state compression provides O(1) constraint checks vs O(n) for set-based.\n"
        "\u2022 MRV heuristic reduces practical branching factor from 9 to ~2-3.\n"
        "\u2022 Hybrid combines D&C subgrid decomposition with DP speed."
    )
    tk.Label(
        table_frame, text=analysis, font=("Segoe UI", 9),
        bg=BENCHMARK_CARD, fg="#8892b0", justify="left", anchor="w",
    ).pack(anchor="w", padx=10, pady=(0, 10))
#####

from sudoku_analysis import open_analysis_window

def get_candidates(board, row, col):
    """Return the set of valid digits for the given cell."""
    if board[row][col] != 0:
        return set()
    candidates = set(range(1, 10))
    candidates -= set(board[row])
    candidates -= {board[i][col] for i in range(9)}
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            candidates.discard(board[i][j])
    return candidates


def is_valid(board, row, col, num):
    """Check whether placing ⁠ num ⁠ at (row, col) violates Sudoku rules."""
    for i in range(9):
        if board[row][i] == num and i != col:
            return False
        if board[i][col] == num and i != row:
            return False
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if board[i][j] == num and (i, j) != (row, col):
                return False
    return True


def solve_with_backtracking(board_snapshot):
    """Wrapper that invokes BitmaskSolver on a deep-copied board."""
    solver = BitmaskSolver()
    board_copy = copy.deepcopy(board_snapshot)
    return solver.solve(board_copy)


# ---------- Benchmarking engine ----------

ALGO_METADATA = [
    {
        "key": "greedy", "name": "Greedy (Priority Queue)",
        "desc": "Selects the most constrained cell using a\nmin-heap (MRV heuristic). Makes greedy\nchoices without lookahead or backtracking.",
        "time": "Time:  O(n² log n)  per move", "space": "Space: O(n²)",
        "tag": "No Backtracking",
    },
    {
        "key": "dnc", "name": "Divide & Conquer",
        "desc": "Recursively divides the problem by choosing\nthe most constrained cell (MRV), tries each\ncandidate, and conquers sub-problems.",
        "time": "Time:  O(9^n)  worst case", "space": "Space: O(n)   recursion stack",
        "tag": "Recursive Split",
    },
    {
        "key": "dp", "name": "Dynamic Programming (Bitmask)",
        "desc": "Uses bitmask state compression to represent\nconstraints as integers. O(1) validity checks\nvia bitwise operations with MRV ordering.",
        "time": "Time:  O(9^n)  worst, near-instant practical",
        "space": "Space: O(n + 27) bitmask arrays", "tag": "State Compression",
    },
    {
        "key": "backtracking", "name": "Backtracking (Bitmask + MRV)",
        "desc": "Classic recursive backtracking enhanced with\nbitmask optimisation and MRV heuristic for\nefficient constraint checking & pruning.",
        "time": "Time:  O(9^n)  worst case",
        "space": "Space: O(n + 27) bitmask arrays", "tag": "Recursive Search",
    },
    {
        "key": "hybrid", "name": "Hybrid (D&C + DP)",
        "desc": "Two-phase solver: first applies Divide &\nConquer per 3×3 subgrid, then uses DP with\nbitmask to solve remaining cells.",
        "time": "Time:  O(9^n)  worst, very fast practical",
        "space": "Space: O(n + 27)", "tag": "Combined Strategy",
    },
]


def benchmark_all_solvers():
    """Benchmark all solvers across Easy / Medium / Hard difficulties."""
    difficulties = {"Easy": 30, "Medium": 45, "Hard": 55}
    num_trials = 5
    results = {}
    for diff_name, holes in difficulties.items():
        results[diff_name] = {}
        for solver_name in BENCHMARK_SOLVERS:
            times = []
            for _ in range(num_trials):
                puzzle = generate_benchmark_puzzle(holes)
                board_copy = copy.deepcopy(puzzle)
                start = time.perf_counter()
                BENCHMARK_SOLVERS[solver_name](board_copy)
                end = time.perf_counter()
                times.append((end - start) * 1000)
            results[diff_name][solver_name] = {
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "times": times,
            }
    return results



COLORS = {
    "bg_dark":"#0f0f1a","bg_card":"#1a1a2e","bg_cell":"#1b2838","bg_cell_hover":"#243448","bg_cell_fixed":"#141e2a","accent_blue":"#4fc3f7",
    "accent_green":"#66bb6a","accent_red":"#ef5350","accent_orange":"#ffa726","accent_purple":"#ab47bc","accent_yellow":"#ffee58","text_primary":"#e0e0e0","text_secondary":"#90a4ae",
    "text_fixed":"#b0bec5","text_user":"#4fc3f7","text_ai":"#ef5350","border_light":"#2a3a5e","border_block":"#0d47a1","grid_line":"#1e2d4d",
}

FONT_TITLE =("Segoe UI", 22, "bold")
FONT_STATUS=("Segoe UI", 14, "bold")
FONT_CELL=("Segoe UI", 22, "bold")
FONT_BUTTON=("Segoe UI", 12, "bold")
FONT_LABEL =("Segoe UI", 12)
FONT_SMALL =("Segoe UI", 10)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SudokuDuel:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver")
        self.root.geometry("680x880")
        self.root.configure(fg_color=COLORS["bg_dark"])
        self.root.resizable(False, False)

        self.board = [[0] * 9 for _ in range(9)]
        self.initial_board = [[0] * 9 for _ in range(9)]
        self.solution_board = [[0] * 9 for _ in range(9)]
        self.cells = [[None] * 9 for _ in range(9)]

        self.current_turn = "user"
        self.game_over = False
        self.difficulty = "Medium"
        self.difficulty_var = ctk.StringVar(value=self.difficulty)
        self.algorithm = "Backtracking"
        self.algorithm_var = ctk.StringVar(value=self.algorithm)

        self.create_widgets()
        self.render_board()
        self._update_status()

    def create_widgets(self):
        title_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        title_frame.pack(pady=(18, 0))

        title = ctk.CTkLabel(
            title_frame,
            text=" Sudoku Duel",
            font=FONT_TITLE,
            text_color=COLORS["accent_blue"],
        )
        title.pack()
        self.subtitle = ctk.CTkLabel(
            title_frame,
            text="Backtracking",
            font=FONT_SMALL,
            text_color=COLORS["text_secondary"],
        )
        self.subtitle.pack(pady=(2, 0))
        self.status_label = ctk.CTkLabel(
            self.root,
            text="Your Turn",
            font=FONT_STATUS,
            text_color=COLORS["accent_green"],
        )
        self.status_label.pack(pady=(12, 6))
        diff_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        diff_frame.pack(pady=(2, 10))

        ctk.CTkLabel(
            diff_frame, text="Difficulty",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 10))

        self.diff_menu = ctk.CTkSegmentedButton(
            diff_frame,
            values=["Easy", "Medium", "Hard"],
            variable=self.difficulty_var,
            command=self._on_difficulty_change,
            font=FONT_SMALL,
            selected_color=COLORS["accent_blue"],
            selected_hover_color="#3aa8d8",
            unselected_color=COLORS["bg_card"],
            unselected_hover_color=COLORS["bg_cell_hover"],
            text_color=COLORS["text_primary"],
        )
        self.diff_menu.pack(side="left")
        algo_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        algo_frame.pack(pady=(2, 10))

        ctk.CTkLabel(
            algo_frame, text="Algorithm",
            font=FONT_LABEL,
            text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 10))

        self.algo_menu = ctk.CTkSegmentedButton(
            algo_frame,
            values=["Greedy", "D&C + DP", "Backtracking"],
            variable=self.algorithm_var,
            command=self._on_algorithm_change,
            font=FONT_SMALL,
            selected_color=COLORS["accent_purple"],
            selected_hover_color="#8e24aa",
            unselected_color=COLORS["bg_card"],
            unselected_hover_color=COLORS["bg_cell_hover"],
            text_color=COLORS["text_primary"],
        )
        self.algo_menu.pack(side="left")

        board_outer = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["border_block"],
            corner_radius=12,
        )
        board_outer.pack(pady=8, padx=20)

        board_inner = ctk.CTkFrame(
            board_outer,
            fg_color=COLORS["bg_dark"],
            corner_radius=10,
        )
        board_inner.pack(padx=3, pady=3)

        CELL_SIZE = 55

        for i in range(9):
            for j in range(9):
                pad_t = 4 if i % 3 == 0 and i != 0 else 1
                pad_l = 4 if j % 3 == 0 and j != 0 else 1

                cell = ctk.CTkEntry(
                    board_inner,
                    width=CELL_SIZE, height=CELL_SIZE,
                    font=FONT_CELL,
                    justify="center",
                    corner_radius=6,
                    fg_color=COLORS["bg_cell"],
                    border_color=COLORS["border_light"],
                    border_width=1,
                    text_color=COLORS["text_primary"],
                )
                cell.grid(
                    row=i, column=j,
                    padx=(pad_l, 1),
                    pady=(pad_t, 1),
                )
                cell.bind(
                    "<KeyRelease>",
                    lambda e, r=i, c=j: self.on_cell_edit(r, c),
                )
                self.cells[i][j] = cell
        btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_frame.pack(pady=(14, 6))
        buttons = [
            ("  NEW GAME",  self.new_game,       COLORS["accent_green"],  "Start a fresh puzzle"),("  HINT",      self.show_hint,      COLORS["accent_blue"],   "Get a hint for the next move"),("  AI PLAY",   self.ai_play_button, COLORS["accent_red"],    "Let the AI make a move"),("  RESET",     self.reset_board,    COLORS["accent_orange"], "Reset to the starting state"),("📊 ANALYSIS", lambda: open_analysis_window(self.root), COLORS["accent_purple"], "Benchmark & compare all algorithms"),
        ]
        for idx, (text, cmd, color, tip) in enumerate(buttons):
            btn = ctk.CTkButton(
                btn_frame,
                text=text,
                command=cmd,
                font=FONT_BUTTON,
                fg_color=color,
                hover_color=self._darken(color),
                corner_radius=8,
                width=130,
                height=38,
                text_color="#0f0f1a",
            )
            btn.grid(row=0, column=idx, padx=6)
            ToolTip(btn, msg=tip, delay=0.3)

        self.strict_var = ctk.BooleanVar(value=False)
        strict_check = ctk.CTkCheckBox(
            self.root,
            text="Strict Mode  (correct values only)",
            variable=self.strict_var,
            font=FONT_SMALL,
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["accent_purple"],
            hover_color="#8e24aa",
            corner_radius=4,
        )
        strict_check.pack(pady=(8, 4))
        ToolTip(strict_check, msg="Only allow correct solution values", delay=0.4)

    @staticmethod
    def _darken(hex_color, factor=0.75):
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _update_status(self):
        self.status_label.configure(
            text=f"Your Turn  •  {self.difficulty}  •  {self.algorithm}"
        )
        self.subtitle.configure(text=self.algorithm)

    def _on_difficulty_change(self, value):
        self.difficulty = value
        self.new_game()

    def _on_algorithm_change(self, value):
        self.algorithm = value
        self._update_status()

    def on_cell_edit(self, row, col):
        pass

    def new_game(self):
        self.game_over = False
        self.board = [[0] * 9 for _ in range(9)]
        self.initial_board = copy.deepcopy(self.board)
        self.current_turn = "user"
        self.render_board()
        self._update_status()

    def render_board(self):
        for i in range(9):
            for j in range(9):
                cell = self.cells[i][j]
                cell.configure(state="normal")
                cell.delete(0, "end")
                if self.board[i][j] != 0:
                    cell.insert(0, str(self.board[i][j]))
                    if self.initial_board[i][j] != 0:
                        cell.configure(
                            text_color=COLORS["text_fixed"],
                            state="disabled",
                        )
                    else:
                        cell.configure(text_color=COLORS["text_user"])
                else:
                    cell.configure(fg_color=COLORS["bg_cell"])

    def show_hint(self):
        pass

    def ai_play_button(self):
        pass

    def reset_board(self):
        self.game_over = False
        self.board = copy.deepcopy(self.initial_board)
        self.current_turn = "user"
        self.render_board()
        self._update_status()


if __name__ == "__main__":
    app = ctk.CTk()
    SudokuDuel(app)
    app.mainloop()
