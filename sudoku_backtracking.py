import customtkinter as ctk
from tkinter import messagebox
from TkToolTip import ToolTip
import copy
import heapq
from sudoku_analysis import open_analysis_window


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

from sudoku_analysis import open_analysis_window



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
