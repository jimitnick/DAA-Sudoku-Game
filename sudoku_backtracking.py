import customtkinter as ctk
from tkinter import messagebox
from tktooltip import ToolTip
import copy


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

        # Game state
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
            ("  NEW GAME",  self.new_game,       COLORS["accent_green"],  "Start a fresh puzzle"),("  HINT",      self.show_hint,      COLORS["accent_blue"],   "Get a hint for the next move"),("  AI PLAY",   self.ai_play_button, COLORS["accent_red"],    "Let the AI make a move"),("  RESET",     self.reset_board,    COLORS["accent_orange"], "Reset to the starting state"),
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

        


    # Helpers

    @staticmethod
    def _darken(hex_color, factor=0.75):
        """Return a darker shade of the given hex colour."""
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    # --------------------------------------------------
    # Stub Methods (logic removed)
    # --------------------------------------------------

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
