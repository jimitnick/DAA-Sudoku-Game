# A priority-queue-based greedy approach to Sudoku works by always selecting the next cell to fill based on how constrained it is,
# which is determined dynamically as the puzzle evolves.
# At the start, every empty cell is analyzed to compute the number of possible candidate digits it can take,
# and each cell is inserted into a min-heap (priority queue) keyed by its candidate count,
# so the most constrained cell (the one with the fewest legal values) is always extracted first.
# The algorithm repeatedly pops the top cell from the priority queue, assigns one of its valid digits (often chosen with an additional heuristic such as least-constraining value),
# updates the Sudoku board, and then recalculates candidate sets for all affected neighboring cells in the same row, column, and subgrid.
# Those neighbors have their priority values updated in the queue, ensuring the queue always reflects the current state of constraints.
# This greedy process continues, filling the most restricted cell at every step.
# While this does not guarantee a complete solution without fallback search,
# the priority queue efficiently enforces the heuristic that making the tightest forced decisions first reduces branching and dramatically improves solver performance.


import tkinter as tk
from tkinter import messagebox
import heapq
import random
import copy

class SudokuDuel:
    STRICT_MODE = False  # If True, user can only enter correct solution values

    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Duel — User vs Greedy AI")
        self.root.geometry("600x700")
        self.root.configure(bg="#ffffff")
        
        # Game state
        self.board = [[0]*9 for _ in range(9)]
        self.initial_board = [[0]*9 for _ in range(9)]
        self.current_turn = "user"
        self.cells = [[None]*9 for _ in range(9)]
        self.cell_colors = [[None]*9 for _ in range(9)]
        
        # Create GUI
        self.create_widgets()
        self.new_game()

        # initialise priority queue
        self.pq = []
    
    def create_widgets(self):
        self.status_label = tk.Label(self.root, text="User's Turn", 
                                     font=("Helvetica", 14, "bold"),
                                     bg="#ffffff", fg="black")
        self.status_label.pack(pady=10)
        
        board_frame = tk.Frame(self.root, bg="#d0d0d0", bd=4, relief=tk.SUNKEN)
        board_frame.pack(pady=10)
        
        for i in range(9):
            for j in range(9):
                pady_top = 2 if i % 3 == 0 and i != 0 else 0
                padx_left = 2 if j % 3 == 0 and j != 0 else 0
                
                cell = tk.Entry(board_frame, width=3, font=("Helvetica", 20, "bold"),
                                justify="center", bd=1, relief=tk.SOLID,
                                bg="white", disabledbackground="white",
                                disabledforeground="black")
                cell.grid(row=i, column=j, padx=(padx_left, 0), pady=(pady_top, 0))
                cell.bind("<KeyRelease>", lambda e, r=i, c=j: self.on_cell_edit(r, c))
                self.cells[i][j] = cell
        
        button_frame = tk.Frame(self.root, bg="#ffffff")
        
        # Strict mode toggle
        self.strict_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.root, text="Strict Mode (Correct Only)",
                       variable=self.strict_var,
                       command=lambda: setattr(self, 'STRICT_MODE', self.strict_var.get()),
                       bg="#ffffff").pack(pady=5)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="New Game", command=self.new_game,
                  font=("Helvetica", 12), bg="#4CAF50", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Hint", command=self.show_hint,
                  font=("Helvetica", 12), bg="#2196F3", fg="white").grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="AI Play", command=self.ai_play,
                  font=("Helvetica", 12), bg="#f44336", fg="white").grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Reset", command=self.reset_board,
                  font=("Helvetica", 12), bg="#FF9800", fg="white").grid(row=0, column=3, padx=5)

    def generate_puzzle(self):
        full_board = self.shuffle_board(self.get_base_pattern())
        self.solution_board = copy.deepcopy(full_board)
        self.board = copy.deepcopy(full_board)
        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)
        for i in range(random.randint(40, 45)):
            r, c = cells[i]
            self.board[r][c] = 0
        return self.board
    
    def get_base_pattern(self):
        def pattern(r, c): return (3 * (r % 3) + r // 3 + c) % 9
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
        bands = [board[i:i+3] for i in range(0, 9, 3)]
        random.shuffle(bands)
        board = [row for band in bands for row in band]
        board = list(map(list, zip(*board)))
        stacks = [board[i:i+3] for i in range(0, 9, 3)]
        random.shuffle(stacks)
        board = [row for stack in stacks for row in stack]
        board = list(map(list, zip(*board)))
        return board

    def is_valid(self, board, row, col, num):
        if num in board[row]: return False
        if num in [board[i][col] for i in range(9)]: return False
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                if board[i][j] == num: return False
        return True

    def get_candidates(self, board, row, col):
        if board[row][col] != 0: return set()
        candidates = set(range(1, 10))
        candidates -= set(board[row])
        candidates -= {board[i][col] for i in range(9)}
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                candidates.discard(board[i][j])
        return candidates

    def initialize_priority_queue(self):
        self.pq = []
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    c = self.get_candidates(self.board, i, j)
                    if c:
                        heapq.heappush(self.pq, (len(c), i, j, c))

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
                cand = self.get_candidates(self.board, r, c)
                if cand:
                    heapq.heappush(self.pq, (len(cand), r, c, cand))

    def ai_make_move(self):
        while self.pq:
            _, row, col, _ = heapq.heappop(self.pq)
            if self.board[row][col] != 0:
                continue
            candidates = self.get_candidates(self.board, row, col)
            if not candidates:
                return False
            value = random.choice(list(candidates))
            self.board[row][col] = value
            self.cells[row][col].config(state="normal")
            self.cells[row][col].delete(0, tk.END)
            self.cells[row][col].insert(0, str(value))
            self.cells[row][col].config(fg="red", state="disabled")
            self.update_neighbors(row, col)
            return True
        return False

    def on_cell_edit(self, row, col):
        if self.current_turn != "user" or self.initial_board[row][col] != 0:
            return
        cell = self.cells[row][col]
        v = cell.get().strip()
        if v == "":
            self.board[row][col] = 0
            return
        try:
            num = int(v)
            if not (1 <= num <= 9): raise ValueError
            self.board[row][col] = 0
            # Strict mode: must match solution
            if self.STRICT_MODE and num != self.solution_board[row][col]:
                messagebox.showerror("Incorrect", "That is not the correct value for this cell.")
                cell.delete(0, tk.END)
                return

            if self.is_valid(self.board, row, col, num):
                self.board[row][col] = num
                self.update_neighbors(row, col)
                cell.config(fg="blue")
                self.current_turn = "ai"
                self.status_label.config(text="AI is Thinking...")
                self.root.after(300, self.ai_turn)
            else:
                cell.delete(0, tk.END)
        except ValueError:
            cell.delete(0, tk.END)

    def ai_turn(self):
        if not self.ai_make_move():
            messagebox.showinfo("Game Over", "AI cannot make a move!")
            return
        if self.is_complete():
            messagebox.showinfo("Game Over", "Puzzle Complete!")
            return
        self.current_turn = "user"
        self.status_label.config(text="User's Turn")

    def is_complete(self):
        return all(self.board[i][j] != 0 for i in range(9) for j in range(9))

    def new_game(self):
        self.board = self.generate_puzzle()
        self.initial_board = copy.deepcopy(self.board)
        self.current_turn = "user"
        self.initialize_priority_queue()
        self.render_board()
        self.status_label.config(text="User's Turn")

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
        self.initialize_priority_queue()
        if not self.pq:
            messagebox.showinfo("Hint", "No empty cells remaining!")
            return
        _, row, col, _ = self.pq[0]
        for i in range(9):
            for j in range(9):
                self.cells[i][j].config(bg="white")
        self.cells[row][col].config(bg="#ffeb3b")
        cand = sorted(self.get_candidates(self.board, row, col))
        messagebox.showinfo("Hint", f"Most constrained cell: Row {row+1}, Col {col+1}\nCandidates: {cand}")

    def ai_play(self):
        self.ai_make_move()

    def reset_board(self):
        self.board = copy.deepcopy(self.initial_board)
        self.current_turn = "user"
        self.initialize_priority_queue()
        self.render_board()
        self.status_label.config(text="User's Turn")

if __name__ == "__main__":
    root = tk.Tk()
    SudokuDuel(root)
    root.mainloop()
