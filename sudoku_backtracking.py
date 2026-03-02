import threading
import time
import copy
import subprocess
import sys
import os
import heapq
import random

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from TkToolTip import ToolTip
from tkinter import ttk


class BitmaskSolver:

    def __init__(self):
        self.rows = [0] * 9
        self.cols = [0] * 9
        self.boxes = [0] * 9

    def _get_box_index(self, r, c):
        return (r // 3) * 3 + (c // 3)

    def _initialize_masks(self, board):
        self.rows = [0] * 9
        self.cols = [0] * 9
        self.boxes = [0] * 9
        empty_cells = []
        for r in range(9):
            for c in range(9):
                if board[r][c] != 0:
                    val = board[r][c] - 1
                    mask = (1 << val)
                    self.rows[r] |= mask
                    self.cols[c] |= mask
                    self.boxes[self._get_box_index(r, c)] |= mask
                else:
                    empty_cells.append((r, c))
        return empty_cells

    def solve(self, board):
        empty_cells = self._initialize_masks(board)
        empty_cells.sort(key=lambda cell: self._count_options(cell[0], cell[1]))
        if self._backtrack(board, empty_cells, 0):
            return board
        return None

    def count_solutions(self, board, limit=2):
        self._initialize_masks(board)
        empty_cells = [(r, c) for r in range(9) for c in range(9) if board[r][c] == 0]
        return self._backtrack_count(board, empty_cells, 0, limit)

    def _count_options(self, r, c):
        box_idx = self._get_box_index(r, c)
        taken = self.rows[r] | self.cols[c] | self.boxes[box_idx]
        options = 0
        for k in range(9):
            if not (taken & (1 << k)):
                options += 1
        return options

    def _backtrack(self, board, empty_cells, idx):
        if idx == len(empty_cells):
            return True

        r, c = empty_cells[idx]
        box_idx = self._get_box_index(r, c)
        taken = self.rows[r] | self.cols[c] | self.boxes[box_idx]

        for k in range(9):
            mask = 1 << k
            if not (taken & mask):
                board[r][c] = k + 1
                self.rows[r] |= mask
                self.cols[c] |= mask
                self.boxes[box_idx] |= mask

                if self._backtrack(board, empty_cells, idx + 1):
                    return True

                self.rows[r] &= ~mask
                self.cols[c] &= ~mask
                self.boxes[box_idx] &= ~mask
                board[r][c] = 0
        return False

    def _backtrack_count(self, board, empty_cells, idx, limit):
        if idx == len(empty_cells):
            return 1
        r, c = empty_cells[idx]
        box_idx = self._get_box_index(r, c)
        taken = self.rows[r] | self.cols[c] | self.boxes[box_idx]
        count = 0
        for k in range(9):
            mask = 1 << k
            if not (taken & mask):
                board[r][c] = k + 1
                self.rows[r] |= mask
                self.cols[c] |= mask
                self.boxes[box_idx] |= mask
                count += self._backtrack_count(board, empty_cells, idx + 1, limit)
                self.rows[r] &= ~mask
                self.cols[c] &= ~mask
                self.boxes[box_idx] &= ~mask
                board[r][c] = 0
                if count >= limit:
                    return count
        return count


def _standalone_is_valid(board, row, col, num):
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


def _standalone_get_candidates(board, row, col):
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
        taken = rows[r] | cols[c] | boxes[(r // 3) * 3 + c // 3]
        return bin(~taken & 0x1ff).count('1')

    empty.sort(key=lambda cell: count_opts(cell[0], cell[1]))

    def bt(idx):
        if idx == len(empty):
            return True
        r, c = empty[idx]
        bi = (r // 3) * 3 + c // 3
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
        taken = rows[r] | cols[c] | boxes[(r // 3) * 3 + c // 3]
        return bin(~taken & 0x1ff).count('1')

    empty.sort(key=lambda cell: count_opts(cell[0], cell[1]))

    def bt(idx):
        if idx == len(empty):
            return True
        r, c = empty[idx]
        bi = (r // 3) * 3 + c // 3
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
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            for r in range(br, br + 3):
                for c in range(bc, bc + 3):
                    if board[r][c] == 0:
                        cands = _standalone_get_candidates(board, r, c)
                        if len(cands) == 1:
                            board[r][c] = cands.pop()
    return solve_dp_standalone(board)


BENCHMARK_SOLVERS = {
    "Greedy":           solve_greedy_standalone,
    "Divide & Conquer": solve_dnc_standalone,
    "DP (Bitmask)":     solve_dp_standalone,
    "Backtracking":     solve_backtracking_standalone,
    "Hybrid (D&C+DP)":  solve_hybrid_standalone,
}

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


def _run_benchmark_thread(parent_root, status_lbl, results_frame):
    """Run the benchmark in a background thread to keep the UI responsive."""
    status_lbl.config(text="\u23f3 Running benchmark... please wait")

    def worker():
        results = benchmark_all_solvers()
        parent_root.after(0, lambda: _display_benchmark_results(results, status_lbl, results_frame))

    threading.Thread(target=worker, daemon=True).start()


def _display_benchmark_results(results, status_lbl, results_frame):
    """Show benchmark results as matplotlib bar charts (with text fallback)."""
    status_lbl.config(text="\u2705 Benchmark complete!")

    for child in results_frame.winfo_children():
        child.destroy()

    try:
        import matplotlib
        matplotlib.use("TkAgg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import numpy as np

        fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.2), dpi=100)
        fig.patch.set_facecolor(BENCHMARK_BG)
        fig.subplots_adjust(wspace=0.35, bottom=0.28, top=0.85)

        solver_names = list(BENCHMARK_SOLVERS.keys())
        bar_colors = ["#3498db", "#9b59b6", "#2ecc71", "#e74c3c", "#f39c12"]

        for ax_idx, (diff_name, diff_data) in enumerate(results.items()):
            ax = axes[ax_idx]
            ax.set_facecolor("#16213e")
            avg_times = [diff_data[s]["avg"] for s in solver_names]
            x = np.arange(len(solver_names))
            bars = ax.bar(x, avg_times, color=bar_colors, width=0.6,
                          edgecolor="#ffffff", linewidth=0.5)
            
            # Label the bars and indicate failures with opacity & text
            for bar, solver_name in zip(bars, solver_names):
                val = diff_data[solver_name]["avg"]
                sr = diff_data[solver_name]["success_rate"]
                
                if sr < 100:
                    bar.set_alpha(0.4)
                    label_text = f"{val:.2f}\n({sr:.0f}%)"
                    text_color = "#ff6b81"
                else:
                    label_text = f"{val:.2f}"
                    text_color = "#ffffff"

                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(avg_times) * 0.02,
                    label_text, ha="center", va="bottom",
                    fontsize=7, color=text_color, fontweight="bold",
                )
            ax.set_title(diff_name, color="#ffffff", fontsize=11, fontweight="bold")
            ax.set_ylabel("Time (ms)", color="#a8b2d1", fontsize=8)
            ax.set_xticks(x)
            ax.set_xticklabels(["Greedy", "D&C", "DP", "BT", "Hybrid"],
                               rotation=30, ha="right", fontsize=7, color="#a8b2d1")
            ax.tick_params(axis="y", colors="#a8b2d1", labelsize=7)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#a8b2d1")
            ax.spines["bottom"].set_color("#a8b2d1")

        fig.suptitle("Solve Time Comparison (avg of 5 runs, in ms)",
                     color="#ffffff", fontsize=12, fontweight="bold")
        canvas = FigureCanvasTkAgg(fig, master=results_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, pady=5)

    except ImportError:
        tk.Label(
            results_frame,
            text="\u26a0 matplotlib not installed \u2014 showing text results.\n"
                 "Install with: pip install matplotlib",
            font=("Segoe UI", 12), bg=BENCHMARK_BG, fg=BENCHMARK_ACCENT,
        ).pack(pady=10)
        for diff_name, diff_data in results.items():
            tk.Label(
                results_frame, text=f"\n--- {diff_name} ---",
                font=("Consolas", 11, "bold"), bg=BENCHMARK_BG, fg="#ffffff",
            ).pack(anchor="w")
            for solver_name, stats in diff_data.items():
                sr = stats["success_rate"]
                text = f"  {solver_name:20s}  avg={stats['avg']:.3f}ms  min={stats['min']:.3f}ms  Success: {sr:.0f}%"
                if sr < 100:
                    text += " [FAILED]"
                tk.Label(
                    results_frame, text=text, font=("Consolas", 9),
                    bg=BENCHMARK_BG, fg="#a8b2d1" if sr == 100 else "#ff6b81",
                ).pack(anchor="w")


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
    """Benchmark all solvers across Easy / Medium / Hard difficulties with success tracking."""
    difficulties = {"Easy": 30, "Medium": 45, "Hard": 55}
    num_trials = 5
    results = {}
    for diff_name, holes in difficulties.items():
        results[diff_name] = {}
        for solver_name in BENCHMARK_SOLVERS:
            times = []
            successes = 0
            for _ in range(num_trials):
                puzzle = generate_benchmark_puzzle(holes)
                board_copy = copy.deepcopy(puzzle)
                
                start = time.perf_counter()
                result = BENCHMARK_SOLVERS[solver_name](board_copy)
                end = time.perf_counter()
                
                times.append((end - start) * 1000)
                
                if result is not None:
                    successes += 1
                    
            results[diff_name][solver_name] = {
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "times": times,
                "success_rate": (successes / num_trials) * 100
            }
    return results


# ---------- GUI Theme Constants ----------

COLORS = {
    "bg_dark": "#0f0f1a", "bg_card": "#1a1a2e", "bg_cell": "#1b2838",
    "bg_cell_hover": "#243448", "bg_cell_fixed": "#141e2a",
    "bg_cell_match": "#2b3d5a",
    "accent_blue": "#4fc3f7", "accent_green": "#66bb6a",
    "accent_red": "#ef5350", "accent_orange": "#ffa726",
    "accent_purple": "#ab47bc", "accent_yellow": "#ffee58",
    "text_primary": "#e0e0e0", "text_secondary": "#90a4ae",
    "text_fixed": "#b0bec5", "text_user": "#4fc3f7", "text_ai": "#ef5350",
    "border_light": "#2a3a5e", "border_block": "#0d47a1",
    "grid_line": "#1e2d4d",
}

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_STATUS = ("Segoe UI", 14, "bold")
FONT_CELL = ("Segoe UI", 22, "bold")
FONT_BUTTON = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)

# Launcher colour palette
BG_DARK_L      = "#1a1a2e"
BG_CARD_L      = "#16213e"
BG_CARD_HOVER  = "#1f3460"
ACCENT_1       = "#0f3460"
ACCENT_2       = "#e94560"
ACCENT_3       = "#533483"
TEXT_PRIMARY_L  = "#ffffff"
TEXT_SECONDARY_L = "#a8b2d1"
TEXT_MUTED      = "#8892b0"

CARD_COLORS = [
    ("#0f3460", "#1a5276"),
    ("#6c3483", "#7d3c98"),
    ("#1e8449", "#27ae60"),
    ("#c0392b", "#e74c3c"),
    ("#d68910", "#f39c12"),
]

FONT_TITLE_L     = ("Segoe UI", 28, "bold")
FONT_SUBTITLE_L  = ("Segoe UI", 12)
FONT_CARD_NAME   = ("Segoe UI", 15, "bold")
FONT_CARD_DESC   = ("Segoe UI", 9)
FONT_CARD_COMP   = ("Consolas", 8)
FONT_BUTTON_L    = ("Segoe UI", 11, "bold")
FONT_SMALL_L     = ("Segoe UI", 9)

# Path setup for launching other solver files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALGO_FILES = {
    "greedy":       os.path.join(SCRIPT_DIR, "sudoku_duel.py"),
    "dnc":          os.path.join(SCRIPT_DIR, "sudoku divid and conquer.py"),
    "dp":           os.path.join(SCRIPT_DIR, "sudoku_dp.py"),
    "backtracking": os.path.join(SCRIPT_DIR, "sudoku_backtracking.py"),
    "hybrid":       os.path.join(SCRIPT_DIR, "sudoku_hybrid.py"),
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ---------- Sudoku Duel Game (CustomTkinter) ----------

class SudokuDuel:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver")
        self.root.geometry("680x780")
        self.root.configure(fg_color=COLORS["bg_dark"])
        self.root.resizable(False, False)

        self.board = [[0] * 9 for _ in range(9)]
        self.initial_board = [[0] * 9 for _ in range(9)]
        self.solution_board = [[0] * 9 for _ in range(9)]
        self.cells = [[None] * 9 for _ in range(9)]
        self.highlight_num = None

        self.current_turn = "user"
        self.game_over = False
        self.difficulty = "Medium"
        self.difficulty_var = ctk.StringVar(value=self.difficulty)
        self.algorithm = "Backtracking"
        self.algorithm_var = ctk.StringVar(value=self.algorithm)
        
        self.log_filename = None

        self.pq = []
        self.pq_entries = set()

        self.create_widgets()
        self.new_game()

    def _init_log_file(self):
        """Initialise a new log file with the algorithm name and timestamp."""
        safe_algo_name = self.algorithm.replace(" ", "_").replace("&", "and").replace("+", "plus")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"AI_Log_{safe_algo_name}_{timestamp}.txt"
        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(f"--- Started new logging session for {self.algorithm} at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    def _log_ai(self, msg):
        """Write an AI thinking message to the log file."""
        if not getattr(self, 'log_filename', None):
            self._init_log_file()
        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

    def _play_sound(self, kind="click"):
        """Play a sound effect in a background thread (cross-platform)."""
        def _do_play():
            try:
                import platform
                system = platform.system()
                if system == "Darwin":  # macOS
                    sound_map = {
                        "click":    "/System/Library/Sounds/Tink.aiff",
                        "complete": "/System/Library/Sounds/Glass.aiff",
                    }
                    path = sound_map.get(kind, sound_map["click"])
                    import subprocess
                    subprocess.Popen(
                        ["afplay", path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                elif system == "Windows":
                    import winsound
                    if kind == "complete":
                        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
                    else:
                        winsound.MessageBeep(winsound.MB_OK)
                else:
                    # Linux / other — silent fallback
                    self.root.after(0, self.root.bell)
            except Exception:
                try:
                    self.root.after(0, self.root.bell)
                except Exception:
                    pass
        threading.Thread(target=_do_play, daemon=True).start()

    # ---- GUI ----

    def create_widgets(self):
        title_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        title_frame.pack(pady=(10, 0))

        ctk.CTkLabel(
            title_frame, text=" Sudoku Duel",
            font=FONT_TITLE, text_color=COLORS["accent_blue"],
        ).pack()
        self.subtitle = ctk.CTkLabel(
            title_frame, text="Backtracking",
            font=FONT_SMALL, text_color=COLORS["text_secondary"],
        )
        self.subtitle.pack(pady=(2, 0))
        self.status_label = ctk.CTkLabel(
            self.root, text="Your Turn",
            font=FONT_STATUS, text_color=COLORS["accent_green"],
        )
        self.status_label.pack(pady=(6, 4))

        diff_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        diff_frame.pack(pady=(2, 4))
        ctk.CTkLabel(
            diff_frame, text="Difficulty",
            font=FONT_LABEL, text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 10))
        self.diff_menu = ctk.CTkSegmentedButton(
            diff_frame, values=["Easy", "Medium", "Hard"],
            variable=self.difficulty_var,
            command=self._on_difficulty_change, font=FONT_SMALL,
            selected_color=COLORS["accent_blue"], selected_hover_color="#3aa8d8",
            unselected_color=COLORS["bg_card"],
            unselected_hover_color=COLORS["bg_cell_hover"],
            text_color=COLORS["text_primary"],
        )
        self.diff_menu.pack(side="left")

        algo_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        algo_frame.pack(pady=(2, 4))
        ctk.CTkLabel(
            algo_frame, text="Algorithm",
            font=FONT_LABEL, text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 10))
        self.algo_menu = ctk.CTkSegmentedButton(
            algo_frame, values=["Greedy", "D&C + DP", "Backtracking"],
            variable=self.algorithm_var,
            command=self._on_algorithm_change, font=FONT_SMALL,
            selected_color=COLORS["accent_purple"], selected_hover_color="#8e24aa",
            unselected_color=COLORS["bg_card"],
            unselected_hover_color=COLORS["bg_cell_hover"],
            text_color=COLORS["text_primary"],
        )
        self.algo_menu.pack(side="left")

        board_outer = ctk.CTkFrame(
            self.root, fg_color=COLORS["border_block"], corner_radius=12,
        )
        board_outer.pack(pady=4, padx=20)
        board_inner = ctk.CTkFrame(
            board_outer, fg_color=COLORS["bg_dark"], corner_radius=10,
        )
        board_inner.pack(padx=3, pady=3)

        CELL_SIZE = 45
        for i in range(9):
            for j in range(9):
                pad_t = 4 if i % 3 == 0 and i != 0 else 1
                pad_l = 4 if j % 3 == 0 and j != 0 else 1
                cell = ctk.CTkEntry(
                    board_inner, width=CELL_SIZE, height=CELL_SIZE,
                    font=FONT_CELL, justify="center", corner_radius=6,
                    fg_color=COLORS["bg_cell"],
                    border_color=COLORS["border_light"], border_width=1,
                    text_color=COLORS["text_primary"],
                )
                cell.grid(row=i, column=j, padx=(pad_l, 1), pady=(pad_t, 1))
                cell.bind("<KeyRelease>", lambda e, r=i, c=j: self.on_cell_edit(r, c))
                self.cells[i][j] = cell

        btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_frame.pack(pady=(8, 4))
        buttons = [
            ("  NEW GAME", self.new_game,       COLORS["accent_green"],  "Start a fresh puzzle"),
            ("  HINT",     self.show_hint,      COLORS["accent_blue"],   "Get a hint for the next move"),
            ("  AI PLAY",  self.ai_play_button, COLORS["accent_red"],    "Let the AI make a move"),
            ("  RESET",    self.reset_board,    COLORS["accent_orange"], "Reset to the starting state"),
        ]
        for idx, (text, cmd, color, tip) in enumerate(buttons):
            btn = ctk.CTkButton(
                btn_frame, text=text, command=cmd, font=FONT_BUTTON,
                fg_color=color, hover_color=self._darken(color),
                corner_radius=8, width=130, height=38, text_color="#0f0f1a",
            )
            btn.grid(row=0, column=idx, padx=6)
            ToolTip(btn, msg=tip, delay=0.3)

        bench_btn = ctk.CTkButton(
            btn_frame, text="  BENCHMARK", command=self.open_benchmark,
            font=FONT_BUTTON,
            fg_color=COLORS["accent_purple"],
            hover_color=self._darken(COLORS["accent_purple"]),
            corner_radius=8, width=130, height=38, text_color="#0f0f1a",
        )
        bench_btn.grid(row=1, column=0, columnspan=4, padx=6, pady=(8, 0))
        ToolTip(bench_btn, msg="Benchmark all 5 algorithms and compare performance", delay=0.3)

        self.strict_var = ctk.BooleanVar(value=False)
        strict_check = ctk.CTkCheckBox(
            self.root, text="Strict Mode  (correct values only)",
            variable=self.strict_var, font=FONT_SMALL,
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["accent_purple"], hover_color="#8e24aa",
            corner_radius=4,
        )
        strict_check.pack(pady=(4, 2))
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
        self._init_log_file()

    def _generate_puzzle(self):
        board, solution = generate_puzzle(self.difficulty)
        self.solution_board = solution
        self.board = board
        return board

    def open_benchmark(self):
        open_benchmark_window(self.root)

    def initialize_priority_queue(self):
        self.pq = []
        self.pq_entries = set()
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    c = get_candidates(self.board, i, j)
                    if c:
                        heapq.heappush(self.pq, (len(c), i, j))
                        self.pq_entries.add((i, j))

    def update_neighbors(self, row, col):
        neighbours = set()
        for i in range(9):
            neighbours.add((row, i))
            neighbours.add((i, col))
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                neighbours.add((i, j))
        for r, c in neighbours:
            if self.board[r][c] == 0:
                cand = get_candidates(self.board, r, c)
                if cand:
                    if (r, c) not in self.pq_entries:
                        heapq.heappush(self.pq, (len(cand), r, c))
                        self.pq_entries.add((r, c))

    def ai_make_move(self):
        self._log_ai("AI analyzing current board state...")
        while self.pq and self.board[self.pq[0][1]][self.pq[0][2]] != 0:
            _, r, c = heapq.heappop(self.pq)
            self.pq_entries.discard((r, c))

        if not self.pq:
            if not self.is_complete():
                self._log_ai("Re-evaluating priority queue for empty cells...")
                self.initialize_priority_queue()
                if not self.pq:
                    self._log_ai("Board is not complete, but no valid moves left. State is unsolvable.")
                    return False
            else:
                self._log_ai("Board is complete.")
                return False

        cands_len, row, col = heapq.heappop(self.pq)
        self.pq_entries.discard((row, col))
        self._log_ai(f"AI selected cell ({row}, {col}) with {cands_len} candidate(s) using MRV heuristic.")

        self._log_ai(f"Simulating full board completion to verify correct move...")
        solved_board = solve_with_backtracking(self.board)

        if solved_board:
            correct_val = solved_board[row][col]
            self._log_ai(f"Simulation successful. Target value for ({row}, {col}) is {correct_val}.")
            self.board[row][col] = correct_val
            self.cells[row][col].configure(state="normal")
            self.cells[row][col].delete(0, "end")
            self.cells[row][col].insert(0, str(correct_val))
            self.cells[row][col].configure(text_color=COLORS["text_ai"], state="disabled")
            self._log_ai(f"Updating neighbor constraints for row {row}, col {col}, and its 3x3 subgrid.")
            self.update_neighbors(row, col)
            if self.highlight_num is not None:
                self._highlight_number(self.highlight_num)
            return True
        else:
            self._log_ai("Simulation failed. No valid solution exists from this board state.")
            return False

    def ai_play_button(self):
        if self.game_over:
            return
        self.status_label.configure(text="AI is Thinking...", text_color=COLORS["accent_red"])
        self.root.update_idletasks()
        self.ai_turn()

    def ai_turn(self):
        if self.game_over:
            return
        if not self.ai_make_move():
            if self.is_complete():
                self.game_over = True
                self._play_sound("complete")
                messagebox.showinfo("Game Over", "Puzzle Complete!")
            else:
                # Don't end the game — let the user make a corrective move
                self.current_turn = "user"
                self._update_status()
                messagebox.showinfo(
                    "AI Stuck",
                    "AI cannot find a solution from this state.\n"
                    "Please make a move to help the AI continue.",
                )
            return

        if self.is_complete():
            self.game_over = True
            self._play_sound("complete")
            messagebox.showinfo("Game Over", "Puzzle Complete! AI Finished it.")
            return

        self.current_turn = "user"
        self._update_status()

    # ---- User interaction ----

    def _clear_number_highlights(self):
        self.highlight_num = None
        for i in range(9):
            for j in range(9):
                self.cells[i][j].configure(fg_color=COLORS["bg_cell"])

    def _highlight_number(self, num):
        self.highlight_num = num
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == num:
                    self.cells[i][j].configure(fg_color=COLORS["bg_cell_match"])
                else:
                    self.cells[i][j].configure(fg_color=COLORS["bg_cell"])

    def on_cell_edit(self, row, col):
        if self.game_over or self.current_turn != "user" or self.initial_board[row][col] != 0:
            return
        cell = self.cells[row][col]
        v = cell.get().strip()
        if v == "":
            self.board[row][col] = 0
            self._clear_number_highlights()
            return
        try:
            num = int(v)
            if not (1 <= num <= 9):
                raise ValueError

            if self.strict_var.get():
                if num != self.solution_board[row][col]:
                    messagebox.showerror("Incorrect", "Strict Mode: That is not the correct value.")
                    cell.delete(0, "end")
                    self.board[row][col] = 0
                    self._clear_number_highlights()
                    return

            if is_valid(self.board, row, col, num):
                self.board[row][col] = num
                self.pq_entries.discard((row, col))
                self.update_neighbors(row, col)
                cell.configure(text_color=COLORS["text_user"])
                self._play_sound("click")

                if self.is_complete():
                    self.game_over = True
                    self._play_sound("complete")
                    messagebox.showinfo("Game Over", "Puzzle Complete! You Win!")
                    return

                self.current_turn = "ai"
                self.status_label.configure(text="AI is Thinking...", text_color=COLORS["accent_red"])
                self.root.after(300, self.ai_turn)
            else:
                cell.delete(0, "end")
                self.board[row][col] = 0
                self._clear_number_highlights()
        except ValueError:
            cell.delete(0, "end")
            self._clear_number_highlights()

    def is_complete(self):
        return all(self.board[i][j] != 0 for i in range(9) for j in range(9))

    def new_game(self):
        self.game_over = False
        self._generate_puzzle()
        self.initial_board = copy.deepcopy(self.board)
        self.current_turn = "user"
        self.initialize_priority_queue()
        self._init_log_file()
        self.render_board()
        self._update_status()

    def render_board(self):
        for i in range(9):
            for j in range(9):
                cell = self.cells[i][j]
                cell.configure(fg_color=COLORS["bg_cell"])
                cell.configure(state="normal")
                cell.delete(0, "end")
                if self.board[i][j] != 0:
                    cell.insert(0, str(self.board[i][j]))
                    if self.initial_board[i][j] != 0:
                        cell.configure(text_color=COLORS["text_fixed"], state="disabled")
                    else:
                        cell.configure(text_color=COLORS["text_user"])
        self.highlight_num = None

    def show_hint(self):
        if self.game_over:
            return
        solved = solve_with_backtracking(self.board)
        if not solved:
            messagebox.showinfo("Hint", "No solution exists from this state.")
            return
        for r in range(9):
            for c in range(9):
                if self.board[r][c] == 0:
                    for i in range(9):
                        for j in range(9):
                            self.cells[i][j].configure(fg_color=COLORS["bg_cell"])
                    self.cells[r][c].configure(fg_color="#3a3a00")
                    cand = sorted(get_candidates(self.board, r, c))
                    messagebox.showinfo(
                        "Hint",
                        f"Backtracking Target:\n"
                        f"Row {r + 1}, Col {c + 1}\n"
                        f"Solution Value: {solved[r][c]}\n"
                        f"Valid Options: {cand}",
                    )
                    return
        messagebox.showinfo("Hint", "No empty cells remaining!")

    def reset_board(self):
        self.game_over = False
        self.board = copy.deepcopy(self.initial_board)
        self.current_turn = "user"
        self.initialize_priority_queue()
        self.render_board()
        self._update_status()


# ---------- Sudoku Launcher (Tkinter) ----------

class SudokuLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Algorithm Lab")
        self.root.geometry("820x740")
        self.root.configure(bg=BG_DARK_L)
        self.root.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        title_frame = tk.Frame(self.root, bg=BG_DARK_L)
        title_frame.pack(fill="x", pady=(25, 5))
        tk.Label(
            title_frame, text="Sudoku Algorithm Lab",
            font=FONT_TITLE_L, bg=BG_DARK_L, fg=TEXT_PRIMARY_L,
        ).pack()
        tk.Label(
            title_frame,
            text="Design & Analysis of Algorithms — Choose a solving strategy",
            font=FONT_SUBTITLE_L, bg=BG_DARK_L, fg=TEXT_SECONDARY_L,
        ).pack(pady=(4, 0))

        tk.Frame(self.root, bg=ACCENT_2, height=2).pack(fill="x", padx=40, pady=(15, 15))

        cards_frame = tk.Frame(self.root, bg=BG_DARK_L)
        cards_frame.pack(fill="both", padx=30, pady=(0, 10))

        row1 = tk.Frame(cards_frame, bg=BG_DARK_L)
        row1.pack(fill="x", pady=(0, 10))
        for idx in range(3):
            self._create_card(row1, ALGO_METADATA[idx], CARD_COLORS[idx], idx)

        row2 = tk.Frame(cards_frame, bg=BG_DARK_L)
        row2.pack(fill="x", pady=(0, 10))
        tk.Frame(row2, bg=BG_DARK_L, width=125).pack(side="left")
        for idx in range(3, 5):
            self._create_card(row2, ALGO_METADATA[idx], CARD_COLORS[idx], idx)

        compare_frame = tk.Frame(self.root, bg=BG_DARK_L)
        compare_frame.pack(fill="x", padx=30, pady=(10, 5))
        tk.Button(
            compare_frame, text="Compare All Algorithms",
            font=("Segoe UI", 14, "bold"),
            bg=ACCENT_2, fg=TEXT_PRIMARY_L,
            activebackground="#ff6b81", activeforeground=TEXT_PRIMARY_L,
            relief="flat", cursor="hand2", padx=20, pady=10,
            command=self._open_comparison,
        ).pack(pady=5)

        tk.Label(
            self.root,
            text="Each option opens a new window  •  Comparison benchmarks all solvers on the same puzzles",
            font=FONT_SMALL_L, bg=BG_DARK_L, fg=TEXT_MUTED,
        ).pack(side="bottom", pady=10)

    def _create_card(self, parent, algo, colors, idx):
        bg_color, hover_color = colors
        card = tk.Frame(parent, bg=bg_color, bd=0, relief="flat",
                        padx=15, pady=12, cursor="hand2")
        card.pack(side="left", padx=6, fill="both", expand=True)

        tag_frame = tk.Frame(card, bg=bg_color)
        tag_frame.pack(anchor="w")
        tk.Label(tag_frame, text=f"  {algo['tag']}  ",
                 font=("Segoe UI", 7, "bold"), bg=TEXT_PRIMARY_L, fg=bg_color).pack(side="left")

        tk.Label(card, text=algo["name"], font=FONT_CARD_NAME,
                 bg=bg_color, fg=TEXT_PRIMARY_L, anchor="w").pack(anchor="w", pady=(8, 2))
        tk.Label(card, text=algo["desc"], font=FONT_CARD_DESC,
                 bg=bg_color, fg=TEXT_SECONDARY_L, anchor="w", justify="left").pack(anchor="w", pady=(0, 6))
        tk.Label(card, text=algo["time"], font=FONT_CARD_COMP,
                 bg=bg_color, fg=TEXT_MUTED, anchor="w").pack(anchor="w")
        tk.Label(card, text=algo["space"], font=FONT_CARD_COMP,
                 bg=bg_color, fg=TEXT_MUTED, anchor="w").pack(anchor="w")

        tk.Button(
            card, text="Play", font=FONT_BUTTON_L,
            bg=TEXT_PRIMARY_L, fg=bg_color, activebackground=hover_color,
            activeforeground=TEXT_PRIMARY_L, relief="flat", cursor="hand2",
            padx=12, pady=3,
            command=lambda k=algo["key"]: self._launch_game(k),
        ).pack(anchor="w", pady=(8, 0))

        def on_enter(e, c=card, hc=hover_color):
            c.config(bg=hc)
            for child in c.winfo_children():
                try: child.config(bg=hc)
                except tk.TclError: pass
                for gc in child.winfo_children():
                    try: gc.config(bg=hc)
                    except tk.TclError: pass

        def on_leave(e, c=card, bc=bg_color):
            c.config(bg=bc)
            for child in c.winfo_children():
                try: child.config(bg=bc)
                except tk.TclError: pass
                for gc in child.winfo_children():
                    try: gc.config(bg=bc)
                    except tk.TclError: pass

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", lambda e, k=algo["key"]: self._launch_game(k))

    def _launch_game(self, algo_key):
        filepath = ALGO_FILES.get(algo_key)
        if not filepath or not os.path.exists(filepath):
            messagebox.showerror("Error", f"Game file not found:\n{filepath}")
            return
        subprocess.Popen([sys.executable, filepath], cwd=SCRIPT_DIR)

    def _open_comparison(self):
        win = tk.Toplevel(self.root)
        win.title("Algorithm Comparison — Sudoku Solver Benchmark")
        win.geometry("950x780")
        win.configure(bg=BG_DARK_L)
        win.resizable(False, False)

        tk.Label(win, text="  Algorithm Comparison",
                 font=("Segoe UI", 22, "bold"), bg=BG_DARK_L, fg=TEXT_PRIMARY_L).pack(pady=(15, 5))

        self.cmp_status = tk.Label(win, text="Click 'Run Benchmark' to start...",
                                   font=FONT_SUBTITLE_L, bg=BG_DARK_L, fg=TEXT_SECONDARY_L)
        self.cmp_status.pack(pady=(0, 10))

        self.results_frame = tk.Frame(win, bg=BG_DARK_L)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=5)

        btn_frame = tk.Frame(win, bg=BG_DARK_L)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="  Run Benchmark", font=FONT_BUTTON_L,
                  bg=ACCENT_2, fg=TEXT_PRIMARY_L, activebackground="#ff6b81",
                  relief="flat", padx=15, pady=6, cursor="hand2",
                  command=lambda: self._run_benchmark(win)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Close", font=FONT_BUTTON_L,
                  bg=TEXT_MUTED, fg=BG_DARK_L, relief="flat", padx=15, pady=6,
                  cursor="hand2", command=win.destroy).pack(side="left", padx=5)

        self._show_complexity_table(win)

    def _show_complexity_table(self, parent):
        table_frame = tk.Frame(parent, bg=BG_CARD_L, bd=1, relief="solid")
        table_frame.pack(fill="x", padx=20, pady=(5, 10))

        tk.Label(table_frame, text="Algorithm Complexity Analysis",
                 font=("Segoe UI", 13, "bold"), bg=BG_CARD_L, fg=TEXT_PRIMARY_L).pack(anchor="w", padx=10, pady=(8, 5))

        headers = ["Algorithm", "Time (Worst)", "Time (Practical)", "Space", "Key Characteristic"]
        data = [
            ["Greedy (PQ)",      "O(n² log n)", "Fast but incomplete",  "O(n²)",   "No backtracking; may fail"],
            ["Divide & Conquer", "O(9^n)",      "Fast with MRV",        "O(n)",    "Recursive subproblem split"],
            ["DP (Bitmask)",     "O(9^n)",      "Near-instant",         "O(n+27)", "O(1) constraint via bits"],
            ["Backtracking",     "O(9^n)",      "Near-instant w/ MRV",  "O(n+27)", "Classic + bitmask + MRV"],
            ["Hybrid (D&C+DP)",  "O(9^n)",      "Fastest practical",    "O(n+27)", "Two-phase: D&C then DP"],
        ]

        grid_frame = tk.Frame(table_frame, bg=BG_CARD_L)
        grid_frame.pack(fill="x", padx=10, pady=(0, 8))

        for ci, h in enumerate(headers):
            tk.Label(grid_frame, text=h, font=("Segoe UI", 9, "bold"),
                     bg=ACCENT_1, fg=TEXT_PRIMARY_L, padx=8, pady=4,
                     relief="flat", anchor="w").grid(row=0, column=ci, sticky="nsew", padx=1, pady=1)

        for ri, row_data in enumerate(data):
            bg = BG_CARD_L if ri % 2 == 0 else "#1f2b47"
            for ci, val in enumerate(row_data):
                tk.Label(grid_frame, text=val, font=("Consolas", 9),
                         bg=bg, fg=TEXT_SECONDARY_L, padx=8, pady=3,
                         anchor="w").grid(row=ri + 1, column=ci, sticky="nsew", padx=1, pady=1)

        for ci in range(len(headers)):
            grid_frame.columnconfigure(ci, weight=1)

        analysis_text = (
            "Analysis Summary:\n"
            "• n = number of empty cells.  All exact solvers share O(9^n) worst-case time.\n"
            "• Greedy is the only incomplete solver — it cannot guarantee a solution.\n"
            "• Bitmask state compression provides O(1) constraint checks vs O(n) for set-based.\n"
            "• MRV heuristic reduces practical branching factor from 9 to ~2-3.\n"
            "• Hybrid combines D&C's subgrid decomposition with DP's speed."
        )
        tk.Label(table_frame, text=analysis_text, font=("Segoe UI", 9),
                 bg=BG_CARD_L, fg=TEXT_MUTED, justify="left", anchor="w").pack(anchor="w", padx=10, pady=(0, 10))

    def _run_benchmark(self, win):
        self.cmp_status.config(text="Running benchmark... please wait")
        win.update_idletasks()

        def worker():
            results = benchmark_all_solvers()
            self.root.after(0, lambda: self._display_results(results))

        threading.Thread(target=worker, daemon=True).start()

    def _display_results(self, results):
        self.cmp_status.config(text=" Benchmark complete!")

        for child in self.results_frame.winfo_children():
            child.destroy()

        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import numpy as np

            fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.2), dpi=100)
            fig.patch.set_facecolor(BG_DARK_L)
            fig.subplots_adjust(wspace=0.35, bottom=0.28, top=0.85)

            solver_names = list(BENCHMARK_SOLVERS.keys())
            bar_colors = ["#3498db", "#9b59b6", "#2ecc71", "#e74c3c", "#f39c12"]

            for ax_idx, (diff_name, diff_data) in enumerate(results.items()):
                ax = axes[ax_idx]
                ax.set_facecolor("#16213e")
                avg_times = [diff_data[s]["avg"] for s in solver_names]
                x = np.arange(len(solver_names))
                bars = ax.bar(x, avg_times, color=bar_colors, width=0.6,
                              edgecolor="#ffffff", linewidth=0.5)
                
                # Label the bars and indicate failures with opacity & text
                for bar, solver_name in zip(bars, solver_names):
                    val = diff_data[solver_name]["avg"]
                    sr = diff_data[solver_name]["success_rate"]
                    
                    if sr < 100:
                        bar.set_alpha(0.4)
                        label_text = f"{val:.2f}\n({sr:.0f}%)"
                        text_color = "#ff6b81"
                    else:
                        label_text = f"{val:.2f}"
                        text_color = "#ffffff"

                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(avg_times) * 0.02,
                        label_text, ha="center", va="bottom",
                        fontsize=7, color=text_color, fontweight="bold",
                    )
                ax.set_title(diff_name, color="#ffffff", fontsize=11, fontweight="bold")
                ax.set_ylabel("Time (ms)", color="#a8b2d1", fontsize=8)
                ax.set_xticks(x)
                ax.set_xticklabels(["Greedy", "D&C", "DP", "BT", "Hybrid"],
                                   rotation=30, ha="right", fontsize=7, color="#a8b2d1")
                ax.tick_params(axis="y", colors="#a8b2d1", labelsize=7)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["left"].set_color("#a8b2d1")
                ax.spines["bottom"].set_color("#a8b2d1")

            fig.suptitle("Solve Time Comparison (avg of 5 runs, in ms)",
                         color="#ffffff", fontsize=12, fontweight="bold")
            canvas = FigureCanvasTkAgg(fig, master=self.results_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, pady=5)

        except ImportError:
            tk.Label(self.results_frame,
                     text="⚠ matplotlib not installed — showing text results.\n"
                          "Install with: pip install matplotlib",
                     font=FONT_SUBTITLE_L, bg=BG_DARK_L, fg=ACCENT_2).pack(pady=10)
            for diff_name, diff_data in results.items():
                tk.Label(self.results_frame, text=f"\n--- {diff_name} ---",
                         font=("Consolas", 11, "bold"), bg=BG_DARK_L, fg=TEXT_PRIMARY_L).pack(anchor="w")
                for solver_name, stats in diff_data.items():
                    sr = stats["success_rate"]
                    text = f"  {solver_name:20s}  avg={stats['avg']:.3f}ms  Success: {sr:.0f}%"
                    if sr < 100:
                        text += " [FAILED]"
                    tk.Label(self.results_frame, text=text, font=("Consolas", 9),
                             bg=BG_DARK_L, fg=TEXT_SECONDARY_L if sr == 100 else "#ff6b81").pack(anchor="w")


if __name__ == "__main__":
    app = ctk.CTk()
    SudokuDuel(app)
    app.mainloop()
