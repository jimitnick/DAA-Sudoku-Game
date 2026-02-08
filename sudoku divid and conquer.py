import tkinter as tk
from tkinter import messagebox
import heapq
import random
import copy

class SudokuDuel:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Duel — User vs D&C AI")
        self.root.geometry("600x750")
        self.root.configure(bg="#ffffff")
        
        # Game state
        self.board = [[0]*9 for _ in range(9)]
        self.initial_board = [[0]*9 for _ in range(9)]
        self.solution_board = [[0]*9 for _ in range(9)]
        self.current_turn = "user"
        self.cells = [[None]*9 for _ in range(9)]
        self.pq = []
        
        # Create GUI
        self.create_widgets()
        self.new_game()
    
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
                       bg="#ffffff").pack(pady=5)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="New Game", command=self.new_game,
                  font=("Helvetica", 12), bg="#4CAF50", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Hint", command=self.show_hint,
                  font=("Helvetica", 12), bg="#2196F3", fg="white").grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="AI Play", command=self.ai_play_button,
                  font=("Helvetica", 12), bg="#f44336", fg="white").grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Reset", command=self.reset_board,
                  font=("Helvetica", 12), bg="#FF9800", fg="white").grid(row=0, column=3, padx=5)

    def generate_puzzle(self):
        full_board = self.shuffle_board(self.get_base_pattern())
        self.solution_board = copy.deepcopy(full_board)
        self.board = copy.deepcopy(full_board)
        
        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)
        
        # Remove numbers to create the puzzle (Easy-Medium difficulty)
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
        return board

    def is_valid(self, board, row, col, num):
        for i in range(9):
            if board[row][i] == num and i != col: return False
            if board[i][col] == num and i != row: return False
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                if board[i][j] == num and (i, j) != (row, col): return False
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

    # -------------------------------------------------------------------------
    #  DIVIDE AND CONQUER SOLVER
    # -------------------------------------------------------------------------
    
    def solve_dnc(self, board_snapshot):
        # 1. PIVOT (Find MRV)
        best_cell = None
        min_candidates_count = 10 
        
        for r in range(9):
            for c in range(9):
                if board_snapshot[r][c] == 0:
                    candidates = self.get_candidates(board_snapshot, r, c)
                    count = len(candidates)
                    if count == 0: return None # Dead end
                    
                    if count < min_candidates_count:
                        min_candidates_count = count
                        best_cell = (r, c)
                        if count == 1: break 
            if min_candidates_count == 1: break

        # 2. BASE CASE
        if best_cell is None:
            return board_snapshot

        # 3. DIVIDE & CONQUER
        row, col = best_cell
        possible_values = self.get_candidates(board_snapshot, row, col)
        
        for val in possible_values:
            board_snapshot[row][col] = val 
            result = self.solve_dnc(board_snapshot)
            if result is not None:
                return result
            board_snapshot[row][col] = 0 # Backtrack
            
        return None

    # -------------------------------------------------------------------------

    def initialize_priority_queue(self):
        self.pq = []
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    c = self.get_candidates(self.board, i, j)
                    if c:
                        heapq.heappush(self.pq, (len(c), i, j))

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
                    heapq.heappush(self.pq, (len(cand), r, c))

    def ai_make_move(self):
        # Sync PQ just in case
        while self.pq and self.board[self.pq[0][1]][self.pq[0][2]] != 0:
            heapq.heappop(self.pq)
            
        if not self.pq:
            # Try to rebuild if empty but board not full (safety net)
            if not self.is_complete():
                self.initialize_priority_queue()
                if not self.pq: return False
            else:
                return False

        # Get Target
        _, row, col = heapq.heappop(self.pq)
        
        # Run D&C Solver
        board_copy = copy.deepcopy(self.board)
        solved_board = self.solve_dnc(board_copy)
        
        if solved_board:
            correct_val = solved_board[row][col]
            self.board[row][col] = correct_val
            
            # UI Update
            self.cells[row][col].config(state="normal")
            self.cells[row][col].delete(0, tk.END)
            self.cells[row][col].insert(0, str(correct_val))
            self.cells[row][col].config(fg="red", state="disabled")
            
            self.update_neighbors(row, col)
            return True
        else:
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
            
            # STRICT MODE FIX: Use .get() directly
            if self.strict_var.get():
                if num != self.solution_board[row][col]:
                    messagebox.showerror("Incorrect", "Strict Mode: That is not the correct value.")
                    cell.delete(0, tk.END)
                    self.board[row][col] = 0
                    return

            if self.is_valid(self.board, row, col, num):
                self.board[row][col] = num
                self.update_neighbors(row, col)
                cell.config(fg="blue")
                
                # CHECK WIN IMMEDIATELY (Fix #1)
                if self.is_complete():
                    messagebox.showinfo("Game Over", "Puzzle Complete! You Win!")
                    return

                self.current_turn = "ai"
                self.status_label.config(text="AI is Thinking...")
                self.root.after(300, self.ai_turn)
            else:
                cell.delete(0, tk.END)
                self.board[row][col] = 0
        except ValueError:
            cell.delete(0, tk.END)

    def ai_play_button(self):
        # Routes the manual button click through the proper turn logic
        self.status_label.config(text="AI is Thinking...")
        self.root.update() # Force UI update so "Thinking" appears
        self.ai_turn()

    def ai_turn(self):
        # Try to make a move
        if not self.ai_make_move():
            # If move failed, check if it's because board is full or error
            if self.is_complete():
                messagebox.showinfo("Game Over", "Puzzle Complete!")
            else:
                messagebox.showinfo("Game Over", "AI cannot find a solution (Unsolvable state).")
            return
            
        # Check for win immediately after AI move
        if self.is_complete():
            messagebox.showinfo("Game Over", "Puzzle Complete! AI Finished it.")
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
                else:
                    cell.config(bg="white")

    def show_hint(self):
        self.initialize_priority_queue()
        # Clean PQ
        while self.pq and self.board[self.pq[0][1]][self.pq[0][2]] != 0:
            heapq.heappop(self.pq)
            
        if not self.pq:
            messagebox.showinfo("Hint", "No empty cells remaining!")
            return
            
        _, row, col = self.pq[0]
        
        for i in range(9):
            for j in range(9):
                self.cells[i][j].config(bg="white")
        self.cells[row][col].config(bg="#ffeb3b")
        
        cand = sorted(self.get_candidates(self.board, row, col))
        messagebox.showinfo("Hint", f"Divide & Conquer Target:\nRow {row+1}, Col {col+1}\nValid Options: {cand}")

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