import tkinter as tk
from tkinter import messagebox
import heapq
import random
import copy

class SudokuDuel:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Duel — User vs DP AI")
        self.root.geometry("600x750")
        self.root.configure(bg="#ffffff")
        self.root.resizable(False, False)

        # Game state
        self.board = [[0]*9 for _ in range(9)]
        self.initial_board = [[0]*9 for _ in range(9)]
        self.solution_board = [[0]*9 for _ in range(9)]
        self.cells = [[None]*9 for _ in range(9)]

        self.current_turn = "user"
        self.game_over = False
        self.difficulty = "Medium"
        self.difficulty_var = tk.StringVar(value=self.difficulty)

        self.pq = []
        self.pq_entries = set()

        self.create_widgets()
        self.new_game()

    # --------------------------------------------------
    # GUI
    # --------------------------------------------------

    def create_widgets(self):
        self.status_label = tk.Label(self.root, text="User's Turn",
                                     font=("Helvetica", 14, "bold"),
                                     bg="#ffffff")
        self.status_label.pack(pady=10)

        difficulty_frame = tk.Frame(self.root, bg="#ffffff")
        difficulty_frame.pack(pady=5)

        tk.Label(difficulty_frame, text="Difficulty:",
                 font=("Helvetica", 12),
                 bg="#ffffff").pack(side=tk.LEFT, padx=5)

        for level in ("Easy", "Medium", "Hard"):
            tk.Radiobutton(
                difficulty_frame,
                text=level,
                value=level,
                variable=self.difficulty_var,
                bg="#ffffff",
                command=self.on_difficulty_change
            ).pack(side=tk.LEFT, padx=5)

        board_frame = tk.Frame(self.root, bg="#d0d0d0", bd=4, relief=tk.SUNKEN)
        board_frame.pack(pady=10)

        for i in range(9):
            for j in range(9):
                pady_top = 2 if i % 3 == 0 and i != 0 else 0
                padx_left = 2 if j % 3 == 0 and j != 0 else 0

                cell = tk.Entry(board_frame, width=3,
                                font=("Helvetica", 20, "bold"),
                                justify="center",
                                bd=1, relief=tk.SOLID,
                                bg="white",
                                disabledbackground="white",
                                disabledforeground="black")

                cell.grid(row=i, column=j,
                          padx=(padx_left, 0),
                          pady=(pady_top, 0))

                cell.bind("<KeyRelease>",
                          lambda e, r=i, c=j: self.on_cell_edit(r, c))

                self.cells[i][j] = cell

        button_frame = tk.Frame(self.root, bg="#ffffff")
        button_frame.pack(pady=20)

        self.strict_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.root,
                       text="Strict Mode (Correct Only)",
                       variable=self.strict_var,
                       bg="#ffffff").pack(pady=5)

        tk.Button(button_frame, text="New Game",
                  command=self.new_game,
                  font=("Helvetica", 12),
                  bg="#4CAF50",
                  fg="white").grid(row=0, column=0, padx=5)

        tk.Button(button_frame, text="Hint",
                  command=self.show_hint,
                  font=("Helvetica", 12),
                  bg="#2196F3",
                  fg="white").grid(row=0, column=1, padx=5)

        tk.Button(button_frame, text="AI Play",
                  command=self.ai_turn,
                  font=("Helvetica", 12),
                  bg="#f44336",
                  fg="white").grid(row=0, column=2, padx=5)

        tk.Button(button_frame, text="Reset",
                  command=self.reset_board,
                  font=("Helvetica", 12),
                  bg="#FF9800",
                  fg="white").grid(row=0, column=3, padx=5)

    # --------------------------------------------------
    # Puzzle Generation
    # --------------------------------------------------

    def on_difficulty_change(self):
        self.difficulty = self.difficulty_var.get()
        self.new_game()

    def generate_puzzle(self):
        full_board = self.shuffle_board(self.get_base_pattern())
        self.solution_board = copy.deepcopy(full_board)
        self.board = copy.deepcopy(full_board)

        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)

        if self.difficulty == "Easy":
            remove_count = random.randint(35, 40)
        elif self.difficulty == "Medium":
            remove_count = random.randint(45, 50)
        else:
            remove_count = random.randint(55, 60)

        for i in range(remove_count):
            r, c = cells[i]
            self.board[r][c] = 0

        return self.board

    def get_base_pattern(self):
        def pattern(r, c):
            return (3 * (r % 3) + r // 3 + c) % 9
        nums = list(range(1, 10))
        random.shuffle(nums)
        return [[nums[pattern(r, c)] for c in range(9)] for r in range(9)]

    def shuffle_board(self, board):
        for i in range(0, 9, 3):
            block = board[i:i+3]
            random.shuffle(block)
            board[i:i+3] = block
        board = list(map(list, zip(*board)))
        for i in range(0, 9, 3):
            block = board[i:i+3]
            random.shuffle(block)
            board[i:i+3] = block
        board = list(map(list, zip(*board)))
        return board

    # --------------------------------------------------
    # Validation Helpers
    # --------------------------------------------------

    def get_candidates(self, board, row, col):
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

    # --------------------------------------------------
    # DP SOLVER (Memoized)
    # --------------------------------------------------

    def solve_dp(self, board_snapshot):
        self.dp_cache = {}
        board = copy.deepcopy(board_snapshot)
        return self._solve_dp_helper(board)

    def _solve_dp_helper(self, board):
        state = tuple(tuple(row) for row in board)

        if state in self.dp_cache:
            return self.dp_cache[state]

        # Find first empty cell
        empty = None
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    empty = (r, c)
                    break
            if empty:
                break

        if not empty:
            self.dp_cache[state] = board
            return board

        row, col = empty

        for num in self.get_candidates(board, row, col):
            board[row][col] = num

            result = self._solve_dp_helper(board)
            if result:
                self.dp_cache[state] = result
                return result

            board[row][col] = 0

        self.dp_cache[state] = None
        return None

    # --------------------------------------------------
    # AI Logic
    # --------------------------------------------------

    def ai_turn(self):
        if self.game_over:
            return

        solved = self.solve_dp(self.board)

        if not solved:
            messagebox.showinfo("Game Over", "No solution exists.")
            return

        # Fill one cell only
        for r in range(9):
            for c in range(9):
                if self.board[r][c] == 0:
                    self.board[r][c] = solved[r][c]
                    self.cells[r][c].delete(0, tk.END)
                    self.cells[r][c].insert(0, str(solved[r][c]))
                    self.cells[r][c].config(fg="red")
                    break
            else:
                continue
            break

        if self.is_complete():
            self.game_over = True
            messagebox.showinfo("Game Over", "Puzzle Complete!")

    # --------------------------------------------------
    # User Interaction
    # --------------------------------------------------

    def on_cell_edit(self, row, col):
        if self.game_over or self.initial_board[row][col] != 0:
            return

        cell = self.cells[row][col]
        v = cell.get().strip()

        if v == "":
            self.board[row][col] = 0
            return

        try:
            num = int(v)
            if not (1 <= num <= 9):
                raise ValueError

            if self.strict_var.get():
                if num != self.solution_board[row][col]:
                    messagebox.showerror("Incorrect",
                                         "Strict Mode: Wrong value.")
                    cell.delete(0, tk.END)
                    return

            self.board[row][col] = num
            cell.config(fg="blue")

            if self.is_complete():
                self.game_over = True
                messagebox.showinfo("Game Over", "You Win!")

        except ValueError:
            cell.delete(0, tk.END)

    def is_complete(self):
        return all(self.board[i][j] != 0
                   for i in range(9)
                   for j in range(9))

    # --------------------------------------------------

    def new_game(self):
        self.game_over = False
        self.board = self.generate_puzzle()
        self.initial_board = copy.deepcopy(self.board)
        self.render_board()
        self.status_label.config(
            text=f"User's Turn ({self.difficulty})"
        )

    def render_board(self):
        for i in range(9):
            for j in range(9):
                cell = self.cells[i][j]
                cell.config(state="normal")
                cell.delete(0, tk.END)

                if self.board[i][j] != 0:
                    cell.insert(0, str(self.board[i][j]))
                    if self.initial_board[i][j] != 0:
                        cell.config(fg="black", state="disabled")
                    else:
                        cell.config(fg="blue")

    def show_hint(self):
        solved = self.solve_dp(self.board)
        if not solved:
            return

        for r in range(9):
            for c in range(9):
                if self.board[r][c] == 0:
                    messagebox.showinfo(
                        "Hint",
                        f"Row {r+1}, Col {c+1} = {solved[r][c]}"
                    )
                    return

    def reset_board(self):
        self.board = copy.deepcopy(self.initial_board)
        self.game_over = False
        self.render_board()


if __name__ == "__main__":
    root = tk.Tk()
    SudokuDuel(root)
    root.mainloop()
