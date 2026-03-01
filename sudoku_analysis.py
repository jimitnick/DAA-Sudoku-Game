"""
Sudoku Algorithm Time Complexity Analysis
==========================================
Benchmarks all 5 solving algorithms on real puzzles and displays results
in a separate window with matplotlib graphs and complexity tables.
"""

import copy
import random
import time
import threading
import heapq
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np


# ─────────────────────────────────────────────────────────
# PUZZLE GENERATION  (headless — no UI dependency)
# ─────────────────────────────────────────────────────────

def _get_base_pattern():
    def pattern(r, c):
        return (3 * (r % 3) + r // 3 + c) % 9
    nums = list(range(1, 10))
    random.shuffle(nums)
    return [[nums[pattern(r, c)] for c in range(9)] for r in range(9)]


def _shuffle_board(board):
    board = [row[:] for row in board]
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
    bands = [board[i:i + 3] for i in range(0, 9, 3)]
    random.shuffle(bands)
    board = [row for band in bands for row in band]
    board = list(map(list, zip(*board)))
    stacks = [board[i:i + 3] for i in range(0, 9, 3)]
    random.shuffle(stacks)
    board = [row for stack in stacks for row in stack]
    board = list(map(list, zip(*board)))
    return board


def generate_puzzle(difficulty="Medium"):
    """Return (puzzle, solution) as two 9×9 lists."""
    full = _shuffle_board(_get_base_pattern())
    solution = copy.deepcopy(full)
    puzzle = copy.deepcopy(full)
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    remove = {"Easy": 30, "Medium": 45, "Hard": 55}.get(difficulty, 45)
    for i in range(remove):
        r, c = cells[i]
        puzzle[r][c] = 0
    return puzzle, solution


# ─────────────────────────────────────────────────────────
# HELPER UTILITIES
# ─────────────────────────────────────────────────────────

def _is_valid(board, row, col, num):
    if num in board[row]:
        return False
    if num in [board[i][col] for i in range(9)]:
        return False
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if board[i][j] == num:
                return False
    return True


def _get_candidates(board, row, col):
    if board[row][col] != 0:
        return set()
    cands = set(range(1, 10))
    cands -= set(board[row])
    cands -= {board[i][col] for i in range(9)}
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            cands.discard(board[i][j])
    return cands


# ─────────────────────────────────────────────────────────
# SOLVER 1:  GREEDY  (priority-queue / MRV heuristic)
# ─────────────────────────────────────────────────────────

def solve_greedy(board_in):
    board = copy.deepcopy(board_in)
    pq = []
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                cands = _get_candidates(board, r, c)
                heapq.heappush(pq, (len(cands), r, c, cands))

    while pq:
        _, row, col, _ = heapq.heappop(pq)
        if board[row][col] != 0:
            continue
        cands = _get_candidates(board, row, col)
        if not cands:
            return None  # dead-end — greedy has no backtrack
        board[row][col] = random.choice(list(cands))
        # Re-enqueue affected neighbours
        for r2 in range(9):
            if board[r2][col] == 0:
                c2 = _get_candidates(board, r2, col)
                heapq.heappush(pq, (len(c2), r2, col, c2))
        for c2 in range(9):
            if board[row][c2] == 0:
                cn = _get_candidates(board, row, c2)
                heapq.heappush(pq, (len(cn), row, c2, cn))
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                if board[i][j] == 0:
                    cn = _get_candidates(board, i, j)
                    heapq.heappush(pq, (len(cn), i, j, cn))
    return board


# ─────────────────────────────────────────────────────────
# SOLVER 2:  DIVIDE & CONQUER  (recursive MRV)
# ─────────────────────────────────────────────────────────

def solve_dnc(board_in):
    board = copy.deepcopy(board_in)
    return _solve_dnc_helper(board)


def _solve_dnc_helper(board):
    best_cell = None
    best_cands = None
    min_count = 10
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                cands = _get_candidates(board, r, c)
                cnt = len(cands)
                if cnt == 0:
                    return None
                if cnt < min_count:
                    min_count = cnt
                    best_cell = (r, c)
                    best_cands = cands
                    if cnt == 1:
                        break
        if min_count == 1:
            break
    if best_cell is None:
        return board
    row, col = best_cell
    for val in best_cands:
        board[row][col] = val
        result = _solve_dnc_helper(board)
        if result is not None:
            return result
        board[row][col] = 0
    return None


# ─────────────────────────────────────────────────────────
# SOLVER 3:  DP  (bitmask state compression)
# ─────────────────────────────────────────────────────────

class _BitmaskSolver:
    def __init__(self):
        self.rows = [0] * 9
        self.cols = [0] * 9
        self.boxes = [0] * 9

    def _box(self, r, c):
        return (r // 3) * 3 + c // 3

    def _init_masks(self, board):
        self.rows = [0] * 9
        self.cols = [0] * 9
        self.boxes = [0] * 9
        empties = []
        for r in range(9):
            for c in range(9):
                if board[r][c] != 0:
                    mask = 1 << (board[r][c] - 1)
                    self.rows[r] |= mask
                    self.cols[c] |= mask
                    self.boxes[self._box(r, c)] |= mask
                else:
                    empties.append((r, c))
        return empties

    def _count_opts(self, r, c):
        taken = self.rows[r] | self.cols[c] | self.boxes[self._box(r, c)]
        return bin(~taken & 0x1FF).count("1")

    def solve(self, board):
        empties = self._init_masks(board)
        empties.sort(key=lambda cell: self._count_opts(cell[0], cell[1]))
        if self._bt(board, empties, 0):
            return board
        return None

    def _bt(self, board, empties, idx):
        if idx == len(empties):
            return True
        r, c = empties[idx]
        bi = self._box(r, c)
        taken = self.rows[r] | self.cols[c] | self.boxes[bi]
        for k in range(9):
            m = 1 << k
            if not (taken & m):
                board[r][c] = k + 1
                self.rows[r] |= m
                self.cols[c] |= m
                self.boxes[bi] |= m
                if self._bt(board, empties, idx + 1):
                    return True
                self.rows[r] &= ~m
                self.cols[c] &= ~m
                self.boxes[bi] &= ~m
                board[r][c] = 0
        return False


def solve_dp(board_in):
    board = copy.deepcopy(board_in)
    return _BitmaskSolver().solve(board)


# ─────────────────────────────────────────────────────────
# SOLVER 4:  BACKTRACKING  (classic)
# ─────────────────────────────────────────────────────────

def solve_backtracking(board_in):
    board = copy.deepcopy(board_in)
    if _backtrack(board):
        return board
    return None


def _backtrack(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                for num in range(1, 10):
                    if _is_valid(board, r, c, num):
                        board[r][c] = num
                        if _backtrack(board):
                            return True
                        board[r][c] = 0
                return False
    return True


# ─────────────────────────────────────────────────────────
# SOLVER 5:  HYBRID  (D&C subgrid phase → DP bitmask)
# ─────────────────────────────────────────────────────────

def solve_hybrid(board_in):
    board = copy.deepcopy(board_in)
    # Phase 1: D&C subgrid constraint propagation
    changed = True
    while changed:
        changed = False
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                for r in range(br, br + 3):
                    for c in range(bc, bc + 3):
                        if board[r][c] == 0:
                            cands = _get_candidates(board, r, c)
                            if len(cands) == 1:
                                board[r][c] = cands.pop()
                                changed = True
    # Phase 2: DP bitmask solver finishes
    return _BitmaskSolver().solve(board)


# ─────────────────────────────────────────────────────────
# BENCHMARK ENGINE
# ─────────────────────────────────────────────────────────

SOLVERS = {
    "Greedy":         solve_greedy,
    "D&C":            solve_dnc,
    "DP (Bitmask)":   solve_dp,
    "Backtracking":   solve_backtracking,
    "Hybrid":         solve_hybrid,
}

DIFFICULTIES = ["Easy", "Medium", "Hard"]
PUZZLES_PER_DIFFICULTY = 5          # averaged for stable results
TIMEOUT_PER_SOLVE = 10.0            # seconds


def _time_solver(solver_fn, puzzle, timeout=TIMEOUT_PER_SOLVE):
    """Return solve time in ms, or None on timeout / failure."""
    result = [None]
    exc = [None]

    def worker():
        try:
            result[0] = solver_fn(puzzle)
        except Exception as e:
            exc[0] = e

    t = threading.Thread(target=worker, daemon=True)
    start = time.perf_counter()
    t.start()
    t.join(timeout)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if t.is_alive():
        return None  # timeout
    if exc[0] is not None:
        return None  # error
    return elapsed_ms


def run_benchmarks(progress_cb=None):
    """
    Return {difficulty: {solver_name: avg_ms}} and a list of per-puzzle records.
    progress_cb(current, total) is called if provided.
    """
    results = {d: {name: [] for name in SOLVERS} for d in DIFFICULTIES}
    records = []
    total = len(DIFFICULTIES) * PUZZLES_PER_DIFFICULTY * len(SOLVERS)
    done = 0

    for diff in DIFFICULTIES:
        for pidx in range(PUZZLES_PER_DIFFICULTY):
            puzzle, _sol = generate_puzzle(diff)
            for name, fn in SOLVERS.items():
                ms = _time_solver(fn, puzzle)
                if ms is not None:
                    results[diff][name].append(ms)
                records.append({
                    "difficulty": diff,
                    "puzzle": pidx + 1,
                    "algorithm": name,
                    "time_ms": ms,
                })
                done += 1
                if progress_cb:
                    progress_cb(done, total)

    # Compute averages
    avg = {}
    for diff in DIFFICULTIES:
        avg[diff] = {}
        for name in SOLVERS:
            times = results[diff][name]
            avg[diff][name] = sum(times) / len(times) if times else None

    return avg, records


# ─────────────────────────────────────────────────────────
# COMPLEXITY INFORMATION
# ─────────────────────────────────────────────────────────

COMPLEXITY_TABLE = [
    ("Greedy (MRV)",      "O(n²)",  "O(n² log n)",  "O(n² log n)",  "O(n²)",      "No backtrack; may fail on hard puzzles"),
    ("Divide & Conquer",  "O(n²)",  "O(9^m)",        "O(9^m)",        "O(m)",       "Recursive MRV; m = empty cells"),
    ("DP (Bitmask)",      "O(n²)",  "O(9^m)",        "O(9^m)",        "O(n)",       "Bitmask constraints give O(1) checks"),
    ("Backtracking",      "O(n²)",  "O(9^m)",        "O(9^(n²))",     "O(n²)",      "Classic brute-force with pruning"),
    ("Hybrid (D&C + DP)", "O(n²)",  "O(9^m)",        "O(9^m)",        "O(n² + m)",  "Constraint-prop Phase 1 reduces m"),
]

COMPLEXITY_HEADERS = ["Algorithm", "Best", "Average", "Worst", "Space", "Notes"]


# ─────────────────────────────────────────────────────────
# VISUALISATION WINDOW  (customtkinter Toplevel)
# ─────────────────────────────────────────────────────────

COLORS_ANALYSIS = {
    "bg_dark":      "#0f0f1a",
    "bg_card":      "#1a1a2e",
    "accent_blue":  "#4fc3f7",
    "accent_green": "#66bb6a",
    "accent_red":   "#ef5350",
    "accent_orange":"#ffa726",
    "accent_purple":"#ab47bc",
    "text_primary": "#e0e0e0",
    "text_secondary":"#90a4ae",
    "border_light": "#2a3a5e",
}

ALGO_COLORS = ["#4fc3f7", "#66bb6a", "#ef5350", "#ffa726", "#ab47bc"]


def open_analysis_window(parent):
    """Launch the analysis window as a Toplevel of *parent*."""
    win = ctk.CTkToplevel(parent)
    win.title("📊  Algorithm Time Complexity Analysis")
    win.geometry("1100x850")
    win.configure(fg_color=COLORS_ANALYSIS["bg_dark"])
    win.resizable(True, True)
    win.transient(parent)
    win.grab_set()

    # ── Header ──
    header = ctk.CTkLabel(
        win,
        text="📊  Sudoku Algorithm Analysis",
        font=("Segoe UI", 24, "bold"),
        text_color=COLORS_ANALYSIS["accent_blue"],
    )
    header.pack(pady=(18, 4))
    sub = ctk.CTkLabel(
        win,
        text="Benchmarking all algorithms on real puzzles …",
        font=("Segoe UI", 13),
        text_color=COLORS_ANALYSIS["text_secondary"],
    )
    sub.pack(pady=(0, 10))

    # ── Progress bar ──
    progress_frame = ctk.CTkFrame(win, fg_color="transparent")
    progress_frame.pack(fill="x", padx=40, pady=(0, 10))
    progress_bar = ctk.CTkProgressBar(
        progress_frame,
        width=500,
        height=14,
        progress_color=COLORS_ANALYSIS["accent_blue"],
        fg_color=COLORS_ANALYSIS["bg_card"],
    )
    progress_bar.pack(fill="x")
    progress_bar.set(0)
    progress_label = ctk.CTkLabel(
        progress_frame,
        text="0 %",
        font=("Segoe UI", 11),
        text_color=COLORS_ANALYSIS["text_secondary"],
    )
    progress_label.pack(pady=(2, 0))

    # ── Scrollable content frame (populated after benchmarks) ──
    content_frame = ctk.CTkScrollableFrame(
        win,
        fg_color=COLORS_ANALYSIS["bg_dark"],
        scrollbar_button_color=COLORS_ANALYSIS["border_light"],
    )
    content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ── Run benchmarks in a background thread ──
    def on_progress(done, total):
        pct = done / total
        win.after(0, lambda: progress_bar.set(pct))
        win.after(0, lambda: progress_label.configure(text=f"{int(pct * 100)} %"))

    def run():
        avg, records = run_benchmarks(progress_cb=on_progress)
        win.after(0, lambda: _build_results_ui(content_frame, avg, records, sub,
                                                progress_frame, win))

    threading.Thread(target=run, daemon=True).start()


def _build_results_ui(parent, avg, records, subtitle_label, progress_frame, win):
    """Populate the content frame with the chart and table once benchmarks finish."""
    subtitle_label.configure(text="Benchmark complete ✓")
    progress_frame.pack_forget()

    # ── 1. MATPLOTLIB BAR CHART ──
    fig = Figure(figsize=(10.2, 4.8), dpi=100, facecolor="#0f0f1a")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#1a1a2e")

    algo_names = list(SOLVERS.keys())
    n_algo = len(algo_names)
    x = np.arange(len(DIFFICULTIES))
    width = 0.15

    for idx, name in enumerate(algo_names):
        vals = [avg[d].get(name) or 0 for d in DIFFICULTIES]
        bars = ax.bar(x + idx * width, vals, width, label=name,
                      color=ALGO_COLORS[idx], edgecolor="none", alpha=0.92)
        # value labels
        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f"{v:.1f}", ha="center", va="bottom",
                        fontsize=7, color="#e0e0e0", fontweight="bold")

    ax.set_xlabel("Difficulty", fontsize=12, color="#90a4ae", labelpad=8)
    ax.set_ylabel("Avg Solve Time (ms)", fontsize=12, color="#90a4ae", labelpad=8)
    ax.set_title("Algorithm Performance Comparison", fontsize=15,
                 color="#4fc3f7", pad=12, fontweight="bold")
    ax.set_xticks(x + width * (n_algo - 1) / 2)
    ax.set_xticklabels(DIFFICULTIES, fontsize=11, color="#e0e0e0")
    ax.tick_params(axis="y", colors="#90a4ae")
    ax.legend(fontsize=9, loc="upper left", facecolor="#1a1a2e",
              edgecolor="#2a3a5e", labelcolor="#e0e0e0")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#2a3a5e")
    ax.spines["left"].set_color("#2a3a5e")
    ax.grid(axis="y", color="#2a3a5e", linewidth=0.5, alpha=0.5)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="x", padx=10, pady=(10, 4))

    # ── 2. PER-TEST-CASE TABLE ──
    _add_section_header(parent, "📋  Individual Test-Case Results")

    # Build a header row
    tc_header_frame = ctk.CTkFrame(parent, fg_color="#1a1a2e", corner_radius=6)
    tc_header_frame.pack(fill="x", padx=14, pady=(6, 0))
    for j, hdr in enumerate(["Difficulty", "Puzzle #", "Algorithm", "Time (ms)"]):
        lbl = ctk.CTkLabel(tc_header_frame, text=hdr,
                           font=("Segoe UI", 11, "bold"),
                           text_color=COLORS_ANALYSIS["accent_blue"],
                           width=150 if j < 3 else 120)
        lbl.grid(row=0, column=j, padx=8, pady=6, sticky="w")

    tc_body = ctk.CTkFrame(parent, fg_color=COLORS_ANALYSIS["bg_dark"])
    tc_body.pack(fill="x", padx=14, pady=(0, 8))

    for i, rec in enumerate(records):
        bg = "#1a1a2e" if i % 2 == 0 else "#151528"
        row_frame = ctk.CTkFrame(tc_body, fg_color=bg, corner_radius=0, height=28)
        row_frame.pack(fill="x")
        vals = [
            rec["difficulty"],
            str(rec["puzzle"]),
            rec["algorithm"],
            f"{rec['time_ms']:.2f}" if rec["time_ms"] is not None else "TIMEOUT",
        ]
        for j, v in enumerate(vals):
            color = COLORS_ANALYSIS["text_primary"]
            if v == "TIMEOUT":
                color = COLORS_ANALYSIS["accent_red"]
            lbl = ctk.CTkLabel(row_frame, text=v,
                               font=("Segoe UI", 10),
                               text_color=color,
                               width=150 if j < 3 else 120)
            lbl.grid(row=0, column=j, padx=8, pady=3, sticky="w")

    # ── 3. COMPLEXITY TABLE ──
    _add_section_header(parent, "⏱  Time & Space Complexity")

    tbl_frame = ctk.CTkFrame(parent, fg_color="#1a1a2e", corner_radius=8)
    tbl_frame.pack(fill="x", padx=14, pady=(6, 14))

    # Header
    for j, hdr in enumerate(COMPLEXITY_HEADERS):
        w = 155 if j == 0 else (100 if j < 5 else 250)
        lbl = ctk.CTkLabel(tbl_frame, text=hdr,
                           font=("Segoe UI", 11, "bold"),
                           text_color=COLORS_ANALYSIS["accent_blue"],
                           width=w)
        lbl.grid(row=0, column=j, padx=6, pady=(8, 4), sticky="w")

    # Data rows
    for i, row_data in enumerate(COMPLEXITY_TABLE):
        bg = "#1a1a2e" if i % 2 == 0 else "#151528"
        for j, val in enumerate(row_data):
            w = 155 if j == 0 else (100 if j < 5 else 250)
            color = COLORS_ANALYSIS["accent_green"] if j == 0 else COLORS_ANALYSIS["text_primary"]
            lbl = ctk.CTkLabel(tbl_frame, text=val,
                               font=("Segoe UI", 10),
                               text_color=color,
                               width=w,
                               fg_color=bg)
            lbl.grid(row=i + 1, column=j, padx=6, pady=2, sticky="w")

    # ── Legend ──
    legend = ctk.CTkLabel(
        parent,
        text="n = 9 (board size)  •  m = number of empty cells  •  Times averaged over "
             f"{PUZZLES_PER_DIFFICULTY} puzzles per difficulty",
        font=("Segoe UI", 10),
        text_color=COLORS_ANALYSIS["text_secondary"],
    )
    legend.pack(pady=(0, 14))


def _add_section_header(parent, text):
    lbl = ctk.CTkLabel(
        parent,
        text=text,
        font=("Segoe UI", 16, "bold"),
        text_color=COLORS_ANALYSIS["accent_blue"],
        anchor="w",
    )
    lbl.pack(fill="x", padx=14, pady=(16, 2))


# ─────────────────────────────────────────────────────────
# Stand-alone test
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.withdraw()
    open_analysis_window(root)
    root.mainloop()
