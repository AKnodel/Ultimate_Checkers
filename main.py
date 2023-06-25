import pygame
from copy import deepcopy
import math
import time
import customtkinter
import tkinter
from PIL import Image
import pyglet
import os
import sys


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# .......................................... Constants .......................................................
# Set the width and height of the game window
WIDTH, HEIGHT = 950, 950

# Set the number of rows and columns for the checkers board
ROWS, COLS = 8, 8

# Calculate the size of each square on the board based on the window width and number of columns
SQUARE_SIZE = WIDTH // COLS

# Load the image for the crown that appears on a piece when it reaches the opposite end of the board
CROWN = pygame.transform.scale(
    pygame.image.load(resource_path("assets\\crown.png")), (50, 50)
)

# Set the target frame rate for the game
FPS = 60

# Loading custom fonts
pyglet.font.add_file(resource_path("fonts\\NatureBeautyPersonalUse-9Y2DK.ttf"))
pyglet.font.add_file(resource_path("fonts\\bahnschrift.ttf"))

# ............................................................................................................


# ............................................ Piece..................................................................................
class Piece:
    # Define constants for the piece's appearance
    PADDING = 15  # Padding around the piece inside the square
    OUTLINE = 2  # Width of the outline around the piece

    def __init__(self, row, col, color):
        # Initialize the piece's position, color, and status as not being a king
        self.row = row
        self.col = col
        self.color = color
        self.king = False

        # Initialize the piece's position on the game board
        self.x = 0
        self.y = 0
        self.calc_pos()

    def calc_pos(self):
        # Calculate the piece's position on the game board based on its row and column
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2

    def make_king(self):
        # Promote the piece to a king
        self.king = True

    def draw(self, win):
        # Draw the piece on the game board
        radius = SQUARE_SIZE // 2 - self.PADDING
        pygame.draw.circle(win, GREY, (self.x, self.y), radius + self.OUTLINE)
        pygame.draw.circle(win, self.color, (self.x, self.y), radius)

        # If the piece is a king, draw a crown on top of it
        if self.king:
            win.blit(
                CROWN,
                (self.x - CROWN.get_width() // 2, self.y - CROWN.get_height() // 2),
            )

    def move(self, row, col):
        # Update the piece's position on the game board
        self.row = row
        self.col = col
        self.calc_pos()

    def __repr__(self):
        # Return the color of the piece as a string
        return str(self.color)


# ............................................................................................................


# ................................................ Game ......................................................
class Game:
    def __init__(self, win):
        self._init()  # Initialize the game state
        self.win = win  # Set the game window

    def update(self):
        self.board.draw(self.win)  # Draw the game board on the window
        self.draw_valid_moves(
            self.valid_moves
        )  # Draw valid moves as circles on the board
        pygame.display.update()  # Update the display to show the changes

    def _init(self):
        self.selected = None  # The currently selected piece
        self.board = Board()  # Create a new game board
        self.turn = HUMAN_KEY  # Set the starting player to human
        self.valid_moves = {}  # Valid moves for the current piece

    def ai_board_winner(self, game):
        # Determine if the AI player has won the game
        return self.board.ai_board_winner(game)

    def human_board_winner(self, game):
        # Determine if the human player has won the game
        return self.board.human_board_winner(game)

    def reset(self):
        self._init()  # Reset the game state

    def select(self, row, col):
        if self.selected:
            result = self._move(row, col)  # Try to move the selected piece
            if not result:
                self.selected = None  # Unselect the piece if the move is invalid
                self.select(
                    row, col
                )  # Call select recursively with the new coordinates

        piece = self.board.get_piece(
            row, col
        )  # Get the piece at the selected coordinates
        if (
            piece != 0 and piece.color == self.turn
        ):  # Check if the piece is a valid selection
            self.selected = piece  # Set the selected piece
            self.valid_moves = self.board.get_valid_moves(
                piece
            )  # Get the valid moves for the selected piece
            return True

        return False

    def _move(self, row, col):
        piece = self.board.get_piece(
            row, col
        )  # Get the piece at the target coordinates
        if (
            self.selected and piece == 0 and (row, col) in self.valid_moves
        ):  # Check if the move is valid
            self.board.move(
                self.selected, row, col
            )  # Move the selected piece to the target coordinates
            skipped = self.valid_moves[
                (row, col)
            ]  # Get any skipped piece from the move
            if skipped:
                self.board.remove(skipped)  # Remove the skipped piece from the board
            self.change_turn()  # Change the turn to the next player
        else:
            return False

        return True

    def draw_valid_moves(self, moves):
        # Draw valid moves as circles on the board
        for move in moves:
            row, col = move
            pygame.draw.circle(
                self.win,
                VALID_DOT,
                (
                    col * SQUARE_SIZE + SQUARE_SIZE // 2,
                    row * SQUARE_SIZE + SQUARE_SIZE // 2,
                ),
                15,
            )

    def change_turn(self):
        # Change the turn to the next player
        self.valid_moves = {}
        if self.turn == HUMAN_KEY:
            self.turn = AI_KEY
        else:
            self.turn = HUMAN_KEY

    def get_board(self):
        # Return the game board
        return self.board

    def ai_move(self, board):
        self.board = board  # Set the game board to the given state
        self.change_turn()  # Change the turn to the next player


# ..................................................................................................................


# ...................................................... Board .......................................................
class Board:
    def __init__(self):
        self.board = []
        self.HUMAN_left = self.AI_left = 12
        self.HUMAN_kings = self.AI_kings = 0
        self.create_board()
        # initializes the attributes of the Board object, including the board
        # matrix and the initial number of pieces for the human and AI players.

    def draw_squares(self, win):  # draws the board squares on the game window.
        win.fill(BACK_COLOR_2)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(
                    win,
                    BACK_COLOR_1,
                    (row * SQUARE_SIZE, col * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                )

    def evaluate(self):  # returns the score of the AI player.
        return (self.AI_left - self.HUMAN_left) + (
            self.AI_kings * 0.5 - self.HUMAN_kings * 0.5
        )

    def get_all_pieces(self, color):  # returns all the pieces of a given color.
        pieces = []
        for row in self.board:
            for piece in row:
                if piece != 0 and piece.color == color:
                    pieces.append(piece)
        return pieces

    def move(self, piece, row, col):
        # moves a given piece to a specified location on
        # the board and updates the corresponding attributes.
        self.board[piece.row][piece.col], self.board[row][col] = (
            self.board[row][col],
            self.board[piece.row][piece.col],
        )
        piece.move(row, col)

        if row == ROWS - 1 or row == 0:
            piece.make_king()
            if piece.color == AI_KEY:
                self.AI_kings += 1
            else:
                self.HUMAN_kings += 1

    def get_piece(self, row, col):
        # returns the piece at a given position on the board.
        return self.board[row][col]

    def create_board(self):
        #  creates the game board.
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if col % 2 == ((row + 1) % 2):
                    if row < 3:
                        self.board[row].append(Piece(row, col, AI_KEY))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, HUMAN_KEY))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)

    def draw(self, win):
        #  draws the pieces on the game window.
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def remove(self, pieces):
        # removes a given piece from the board.
        for piece in pieces:
            self.board[piece.row][piece.col] = 0
            if piece != 0:
                if piece.color == HUMAN_KEY:
                    self.HUMAN_left -= 1
                else:
                    self.AI_left -= 1

    def ai_board_winner(self, game):
        #  returns the winner of the game if it is over, and None otherwise.
        if self.AI_left <= 0:
            return HUMAN_KEY
        elif self.HUMAN_left <= 0:
            return AI_KEY
        human_valid_moves = get_all_moves(self, HUMAN_KEY, game)
        ai_left_moves = get_all_moves(self, AI_KEY, game)
        if len(human_valid_moves) == 0 or len(ai_left_moves) == 0:
            return GREY
        return None

    def human_board_winner(self):
        # returns the winner of the game if it is over, and None otherwise.
        if self.HUMAN_left <= 0:
            return HUMAN_KEY
        elif self.AI_left <= 0:
            return AI_KEY

        return None

    def get_valid_moves(self, piece):
        #  returns all the valid moves for a given piece.
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row

        if piece.color == HUMAN_KEY or piece.king:
            moves.update(
                self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left)
            )
            moves.update(
                self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right)
            )
        if piece.color == AI_KEY or piece.king:
            moves.update(
                self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left)
            )
            moves.update(
                self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right)
            )

        return moves

    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        # is a helper method for get_valid_moves() that recursively traverses
        #  the board to the left and returns all possible moves.
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break

            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = last + skipped
                else:
                    moves[(r, left)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(
                        self._traverse_left(
                            r + step, row, step, color, left - 1, skipped=last
                        )
                    )
                    moves.update(
                        self._traverse_right(
                            r + step, row, step, color, left + 1, skipped=last
                        )
                    )
                break
            elif current.color == color:
                break
            else:
                last = [current]

            left -= 1

        return moves

    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        #  is a helper method for get_valid_moves() that recursively traverses
        # the board to the right and returns all possible moves.
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break

            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(
                        self._traverse_left(
                            r + step, row, step, color, right - 1, skipped=last
                        )
                    )
                    moves.update(
                        self._traverse_right(
                            r + step, row, step, color, right + 1, skipped=last
                        )
                    )
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1

        return moves


# .........................................................................................................


# ................................................. main ..................................................
def HUMAN_main():
    run = True
    clock = pygame.time.Clock()
    game = Game(WIN)

    # The game loop
    while run:
        clock.tick(FPS)

        # Check if the game has been won by the human player
        if game.human_board_winner() != None:
            # Print the winner and wait for 2 seconds before quitting the game
            print(game.human_board_winner())
            run = False
            time.sleep(2)
            run = False

        # Check for events, such as mouse clicks
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            # If a mouse button is clicked, get the row and column of the selected cell
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)
                game.select(row, col)

        # Update the game board after each iteration of the game loop
        game.update()

    # Quit pygame after the game loop has ended
    pygame.quit()


def AI_main():
    # initialize variables and objects
    run = True
    clock = pygame.time.Clock()
    game = Game(WIN)

    while run:
        # set FPS limit
        clock.tick(FPS)

        # if it's the AI's turn, use minimax algorithm to find the best move
        if game.turn == AI_KEY:
            value, new_board = minimax(
                game.get_board(), diff_depth, AI_KEY, game, -math.inf, math.inf
            )
            game.ai_move(new_board)

        # check if the AI has won, and display appropriate message
        if game.ai_board_winner(game) != None:
            print(game.ai_board_winner(game))
            if game.ai_board_winner(game) == HUMAN_KEY:
                print("**********************************************************")
                print("\nYOU WON\n")
                print("**********************************************************")
            elif game.ai_board_winner(game) == AI_KEY:
                print("**********************************************************")
                print("\nAI WON\n")
                print("**********************************************************")
            elif game.ai_board_winner(game) == GREY:
                print("**********************************************************")
                print("\nIt's a TIE!\n")
                print("**********************************************************")
            # wait for 2 seconds and exit the loop
            time.sleep(2)
            run = False

        # check for user input events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            # if the user clicks on the board, select the corresponding square
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)
                game.select(row, col)

        # update the display
        game.update()

    # exit pygame
    pygame.quit()


def get_row_col_from_mouse(pos):
    # convert the mouse position to row and column indices
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col


# ......................................................................................................................


# .................................................. algorithm ............................................................
def minimax(position, depth, max_player, game, alpha, beta):
    """
    This function implements the minimax algorithm with alpha-beta pruning to find the best move
    for a given player at a given depth.

    Args:
        position (Board): the current board state
        depth (int): the current depth of the search
        max_player (bool): True if the current player is the maximizing player, False if the current player is the minimizing player
        game (Game): the current game object
        alpha (int): the current alpha value for alpha-beta pruning
        beta (int): the current beta value for alpha-beta pruning

    Returns:
        (int, Board): a tuple containing the score of the best move and the corresponding board state
    """
    if depth == 0 or position.ai_board_winner(game) != None:
        # Base case: if we've reached the maximum depth or there's a winner, return the evaluation of the board state
        return position.evaluate(), position

    if max_player:
        # If it's the maximizing player's turn
        maxEval = -math.inf
        best_move = None
        for move in get_all_moves(position, AI_KEY, game):
            # For each possible move, calculate the minimax score recursively
            evaluation = minimax(move, depth - 1, False, game, alpha, beta)[0]

            # If the evaluation is better than the current best evaluation, update the best evaluation and best move
            if evaluation > maxEval:
                maxEval = evaluation
                best_move = move

            # Update alpha value for alpha-beta pruning
            alpha = max(alpha, maxEval)
            if alpha >= beta:
                # If alpha is greater than or equal to beta, pruning occurs and we break out of the loop
                break

        return maxEval, best_move
    else:
        # If it's the minimizing player's turn
        minEval = math.inf
        best_move = None
        for move in get_all_moves(position, HUMAN_KEY, game):
            # For each possible move, calculate the minimax score recursively
            evaluation = minimax(move, depth - 1, True, game, alpha, beta)[0]

            # If the evaluation is better than the current best evaluation, update the best evaluation and best move
            if evaluation < minEval:
                minEval = evaluation
                best_move = move

            # Update beta value for alpha-beta pruning
            beta = min(beta, minEval)
            if alpha >= beta:
                # If alpha is greater than or equal to beta, pruning occurs and we break out of the loop
                break

        return minEval, best_move


def simulate_move(piece, move, board, game, skip):
    """
    This function simulates a move on a copy of the board, given a piece and a move.

    Args:
        piece (Piece): the piece to move
        move (tuple): the coordinates of the move
        board (Board): the current board state
        game (Game): the current game object
        skip (Piece): the piece to remove (if any)

    Returns:
        Board: the board state after the move has been made
    """
    board.move(piece, move[0], move[1])  # move the piece on the copy of the board
    if skip:
        board.remove(skip)  # if there's a piece to remove, remove it

    return board


def get_all_moves(board, color, game):
    moves = []

    # Loop through all pieces of the given color
    for piece in board.get_all_pieces(color):
        # Get all valid moves for the current piece
        valid_moves = board.get_valid_moves(piece)
        # Loop through all valid moves for the current piece
        for move, skip in valid_moves.items():
            # Create a copy of the board and the piece
            temp_board = deepcopy(board)
            temp_piece = temp_board.get_piece(piece.row, piece.col)
            # Simulate the move on the copy of the board and append it to the list of moves
            new_board = simulate_move(temp_piece, move, temp_board, game, skip)
            moves.append(new_board)

    return moves


def draw_moves(game, board, piece):
    valid_moves = board.get_valid_moves(piece)
    board.draw(game.win)
    pygame.draw.circle(game.win, (0, 255, 0), (piece.x, piece.y), 50, 5)
    game.draw_valid_moves(valid_moves.keys())
    pygame.display.update()


#  ........................................................................................................................

# ............................................ start menu .............................................................


# Set appearance mode and default color theme
customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme(
    "dark-blue"
)  # Themes: blue (default), dark-blue, green


# Create main window class
class main_window(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1080x775+275+5")  # Set window size and position
        self.title("Start Menu - Ultimate Checkers")  # Set window title

        # Create label for "Play with" text
        self.label_1 = customtkinter.CTkLabel(
            self,
            height=50,
            width=100,
            text="  Play with :  ",
            text_color="#FCAE1E",
            anchor="center",
            font=("Nature Beauty Personal Use", 75),
        )

        # Add "Play with" label to grid
        self.label_1.grid(row=0, column=0, padx=20, pady=20)

        # Create radio buttons for selecting human or AI player
        self.radio_var = tkinter.IntVar(self, value=2)

        radiobutton_1 = customtkinter.CTkRadioButton(
            self,
            text="",
            variable=self.radio_var,
            value=1,
            corner_radius=0,
            radiobutton_width=225,
            radiobutton_height=175,
            hover_color="#39FF14",
            border_color="",
            hover=True,
            border_width_unchecked=10,
            border_width_checked=10,
            command=self.radiobutton_event,
        )

        radiobutton_2 = customtkinter.CTkRadioButton(
            self,
            text="",
            variable=self.radio_var,
            value=2,
            corner_radius=0,
            radiobutton_width=225,
            radiobutton_height=175,
            hover_color="#39FF14",
            border_color="",
            hover=True,
            border_width_unchecked=10,
            border_width_checked=10,
            command=self.radiobutton_event,
        )

        # Add radio buttons to grid
        radiobutton_1.grid(row=0, column=10, padx=20, pady=10)
        radiobutton_2.grid(row=0, column=13, padx=20, pady=10)

        # Create labels for human and AI player options
        self.label_2 = customtkinter.CTkLabel(
            self,
            height=50,
            width=100,
            text=" Human  ",
            text_color="#00BFFF",
            anchor="center",
            font=("Nature Beauty Personal Use", 70),
        )
        self.label_3 = customtkinter.CTkLabel(
            self,
            height=50,
            width=100,
            text=" A.I.  ",
            text_color="#00BFFF",
            anchor="center",
            font=("Nature Beauty Personal Use", 70),
        )

        # Add labels for human and AI player options to grid
        self.label_2.grid(row=0, column=10, padx=20, pady=20)
        self.label_3.grid(row=0, column=13, padx=20, pady=20)

        # Create label for difficulty level
        self.label_4 = customtkinter.CTkLabel(
            self,
            height=20,
            width=20,
            text=" Difficulty level :  ",
            anchor="center",
            font=("Bahnschrift SemiBold SemiConden", 35),
        )
        # Add labels for difficulty options to grid
        self.label_4.grid(
            row=2,
            column=13,
        )

        self.label_5 = customtkinter.CTkLabel(
            self,
            height=20,
            width=20,
            text="(Only valid if you choose AI mode)",
            anchor="center",
            font=("Bahnschrift SemiBold SemiConden", 13),
        )
        self.label_5.grid(
            row=3,
            column=13,
        )
        self.combobox_var_1 = customtkinter.StringVar(self, value="Easy")
        # Create label for difficulty level
        combobox_1 = customtkinter.CTkComboBox(
            self,
            values=["Easy", "Medium", "Impossible"],
            variable=self.combobox_var_1,
            justify="center",
            corner_radius=10,
            button_hover_color="#00BFFF",
            font=("Bahnschrift SemiBold SemiConden", 20),
            command=self.combobox1_callback,
        )
        #  Add labels for difficulty options to grid
        combobox_1.grid(
            row=5,
            column=13,
        )
        self.label_6 = customtkinter.CTkLabel(
            self,
            height=0,
            width=0,
            text=" Choose Theme :",
            anchor="center",
            font=("Bahnschrift SemiBold SemiConden", 35),
        )
        self.label_6.grid(
            row=11,
            column=0,
        )
        self.combobox_var_2 = customtkinter.StringVar(self, value="Default")

        combobox_2 = customtkinter.CTkComboBox(
            self,
            values=["Default", "Mint", "Dracula"],
            variable=self.combobox_var_2,
            justify="center",
            corner_radius=10,
            button_hover_color="#00BFFF",
            font=("Bahnschrift SemiBold SemiConden", 20),
            command=self.combobox2_callback,
        )
        combobox_2.grid(
            row=12,
            column=0,
        )
        image_default = customtkinter.CTkImage(
            dark_image=Image.open(resource_path("assets\\default.png")), size=(125, 125)
        )
        button1 = customtkinter.CTkButton(
            self,
            text="",
            image=image_default,
            corner_radius=5,
            fg_color="transparent",
            hover_color="#3CB043",
            anchor="left",
            compound="left",
            command=lambda: self.set_combobox(combobox_2, "Default"),
        )

        button1.grid(row=13, column=0)
        image_mint = customtkinter.CTkImage(
            dark_image=Image.open(resource_path("assets\\mint.png")), size=(125, 125)
        )
        button2 = customtkinter.CTkButton(
            self,
            text="",
            image=image_mint,
            corner_radius=5,
            fg_color="transparent",
            hover_color="#3CB043",
            anchor="left",
            compound="left",
            command=lambda: self.set_combobox(combobox_2, "Mint"),
        )
        button2.grid(row=14, column=0)
        image_dracula = customtkinter.CTkImage(
            dark_image=Image.open(resource_path("assets\\dracula.png")), size=(125, 125)
        )
        button3 = customtkinter.CTkButton(
            self,
            text="",
            image=image_dracula,
            corner_radius=5,
            fg_color="transparent",
            anchor="left",
            hover_color="#3CB043",
            compound="left",
            command=lambda: self.set_combobox(combobox_2, "Dracula"),
        )
        button3.grid(row=15, column=0)

        play_button = customtkinter.CTkButton(
            master=self,
            text=" Play ",
            width=150,
            height=100,
            font=("Nature Beauty Personal Use", 55),
            fg_color="#FF3131",
            anchor="center",
            corner_radius=10,
            hover_color="#3CB043",
            command=self.play,
        )
        play_button.grid(row=15, column=13, padx=20, pady=10)

    def set_combobox(self, combobox_2, value):
        self.combobox_var_2.set(value)

    def radiobutton_event(self):
        return self.radio_var.get()

    def combobox1_callback(self, event):
        return self.combobox_var_1.get()

    def combobox2_callback(self, event):
        return self.combobox_var_2.get()

    def play(self):
        print("play pressed")
        print("Playing against(1: human   2: ai) : ", self.radio_var.get())
        print("Difficulty(default: medium) : ", self.combobox_var_1.get())
        print("Theme(default: wooden) : ", self.combobox_var_2.get())

        main_window.destroy(self)


# .................................................. driver program.......................................

# Create a main window instance and run the Tkinter main loop
app = main_window()
app.mainloop()

# Get user's selections for game settings
chance = app.radiobutton_event()
difficulty = app.combobox_var_1.get()
theme = app.combobox_var_2.get()

# Setting difficulty based on user's selection
if difficulty == "Easy":
    diff_depth = 2
elif difficulty == "Medium":
    diff_depth = 3
elif difficulty == "Impossible":
    diff_depth = 4

# Setting theme based on user's selection
if theme == "Default":
    from checkers.constants_default import (
        AI_KEY,
        HUMAN_KEY,
        GREY,
        VALID_DOT,
        BACK_COLOR_1,
        BACK_COLOR_2,
    )
elif theme == "Mint":
    from checkers.constants_mint import (
        AI_KEY,
        HUMAN_KEY,
        GREY,
        VALID_DOT,
        BACK_COLOR_1,
        BACK_COLOR_2,
    )
elif theme == "Dracula":
    from checkers.constants_dracula import (
        AI_KEY,
        HUMAN_KEY,
        GREY,
        VALID_DOT,
        BACK_COLOR_1,
        BACK_COLOR_2,
    )

# Create a Pygame window and set caption
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultimate Checkers")

# Start the game with the appropriate mode based on user's selection
if chance == 1:
    HUMAN_main()
elif chance == 2:
    AI_main()

# .........................................................................................................................
