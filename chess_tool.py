import pygame
import copy
import math
import random
import os

#Constants
WIDTH, HEIGHT = 512, 512
ROWS, COLS = 8, 8
SQ_SIZE = WIDTH // COLS
FPS = 30

#Colors
WHITE = (240, 217, 181)
BLACK = (181, 136, 99)
HIGHLIGHT = (130, 151, 105)
TEXT_COLOR = (30, 30, 30)
UI_BG = (50, 50, 50)

#Piece mappings
PIECES = {
    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟'
}


IMAGES = {}

def load_images():
    pieces = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']
    for piece in pieces:
        img_path = os.path.join("images", f"{piece}.png")
        try:
            image = pygame.image.load(img_path)
            IMAGES[piece] = pygame.transform.scale(image, (SQ_SIZE, SQ_SIZE))
        except FileNotFoundError:
            print(f"Error: Could not find {img_path}. Make sure the 'images' folder exists and has the correct files.")
            pygame.quit()
            exit()

#Game logic
class Board:
    def __init__(self):
        self.board = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
        ]
        self.white_to_move = True

        self.castle_rights = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}

    def _get_pseudo_legal_moves(self, r, c):
        piece = self.board[r][c]
        if piece == '--': return []

        moves = []
        color = piece[0]
        ptype = piece[1]

        directions = {
            'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
            'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
            'Q': [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)],
            'K': [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        }

        #Sliding pieces
        if ptype in ['R', 'B', 'Q']:
            for d in directions[ptype]:
                for i in range(1, 8):
                    end_r, end_c = r + d[0] * i, c + d[1] * i
                    if 0 <= end_r < 8 and 0 <= end_c < 8:
                        target = self.board[end_r][end_c]
                        if target == '--':
                            moves.append((end_r, end_c))
                        elif target[0] != color:
                            moves.append((end_r, end_c))
                            break
                        else:
                            break
                    else:
                        break

        #King
        elif ptype == 'K':
            for d in directions['K']:
                end_r, end_c = r + d[0], c + d[1]
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    target = self.board[end_r][end_c]
                    if target[0] != color:
                        moves.append((end_r, end_c))

        # Knight
        elif ptype == 'N':
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
            for m in knight_moves:
                end_r, end_c = r + m[0], c + m[1]
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    target = self.board[end_r][end_c]
                    if target[0] != color:
                        moves.append((end_r, end_c))

        # Pawn
        elif ptype == 'P':
            dir = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1

            # Forward 1
            if 0 <= r + dir < 8 and self.board[r + dir][c] == '--':
                moves.append((r + dir, c))
                # Forward 2
                if r == start_row and self.board[r + 2 * dir][c] == '--':
                    moves.append((r + 2 * dir, c))

            # Captures
            for dc in [-1, 1]:
                if 0 <= r + dir < 8 and 0 <= c + dc < 8:
                    target = self.board[r + dir][c + dc]
                    if target != '--' and target[0] != color:
                        moves.append((r + dir, c + dc))

        return moves

    def find_king(self, is_white):
        target = 'wK' if is_white else 'bK'
        for r in range(ROWS):
            for c in range(COLS):
                if self.board[r][c] == target:
                    return r, c
        return None, None

    def square_under_attack(self, r, c, enemy_color):
        for er in range(ROWS):
            for ec in range(COLS):
                piece = self.board[er][ec]
                if piece != '--' and piece[0] == enemy_color:
                    moves = self._get_pseudo_legal_moves(er, ec)
                    if (r, c) in moves:
                        return True
        return False

    def in_check(self, is_white):
        kr, kc = self.find_king(is_white)
        if kr is None: return False
        enemy_color = 'b' if is_white else 'w'
        return self.square_under_attack(kr, kc, enemy_color)

    def is_valid_setup(self):
        """Validates if the custom board state follows basic chess rules."""
        wk_count = 0
        bk_count = 0

        for r in range(ROWS):
            for c in range(COLS):
                piece = self.board[r][c]
                if piece == 'wK':
                    wk_count += 1
                elif piece == 'bK':
                    bk_count += 1
                elif piece[1] == 'P' and (r == 0 or r == 7):
                    return False, "Pawns cannot be on the 1st or 8th rank."

        if wk_count != 1 or bk_count != 1:
            return False, "Must have exactly one White King and one Black King."

        if self.white_to_move and self.in_check(False):
            return False, "Black King is in check, but it is White's turn."
        if not self.white_to_move and self.in_check(True):
            return False, "White King is in check, but it is Black's turn."

        if self.board[7][4] != 'wK':
            self.castle_rights['wK'] = self.castle_rights['wQ'] = False
        if self.board[7][7] != 'wR': self.castle_rights['wK'] = False
        if self.board[7][0] != 'wR': self.castle_rights['wQ'] = False

        if self.board[0][4] != 'bK':
            self.castle_rights['bK'] = self.castle_rights['bQ'] = False
        if self.board[0][7] != 'bR': self.castle_rights['bK'] = False
        if self.board[0][0] != 'bR': self.castle_rights['bQ'] = False

        return True, ""

    def get_valid_moves(self, r, c):
        pseudo_moves = self._get_pseudo_legal_moves(r, c)
        legal_moves = []
        piece = self.board[r][c]
        is_white = self.board[r][c][0] == 'w'

        for move in pseudo_moves:
            end_r, end_c = move[0], move[1]
            temp_piece = self.board[end_r][end_c]

            self.board[end_r][end_c] = self.board[r][c]
            self.board[r][c] = '--'

            if not self.in_check(is_white):
                legal_moves.append(move)

            self.board[r][c] = self.board[end_r][end_c]
            self.board[end_r][end_c] = temp_piece

            enemy_color = 'b' if is_white else 'w'
            if piece[1] == 'K' and not self.in_check(is_white):
                if is_white and r == 7 and c == 4:
                    if self.castle_rights['wK'] and self.board[7][5] == '--' and self.board[7][6] == '--':
                        if not self.square_under_attack(7, 5, enemy_color) and not self.square_under_attack(7, 6,
                                                                                                            enemy_color):
                            legal_moves.append((7, 6))
                    if self.castle_rights['wQ'] and self.board[7][1] == '--' and self.board[7][2] == '--' and \
                            self.board[7][3] == '--':
                        if not self.square_under_attack(7, 2, enemy_color) and not self.square_under_attack(7, 3,
                                                                                                            enemy_color):
                            legal_moves.append((7, 2))
                elif not is_white and r == 0 and c == 4:
                    if self.castle_rights['bK'] and self.board[0][5] == '--' and self.board[0][6] == '--':
                        if not self.square_under_attack(0, 5, enemy_color) and not self.square_under_attack(0, 6,
                                                                                                            enemy_color):
                            legal_moves.append((0, 6))
                    if self.castle_rights['bQ'] and self.board[0][1] == '--' and self.board[0][2] == '--' and \
                            self.board[0][3] == '--':
                        if not self.square_under_attack(0, 2, enemy_color) and not self.square_under_attack(0, 3,
                                                                                                            enemy_color):
                            legal_moves.append((0, 2))
        return legal_moves

    def get_all_possible_moves(self, is_white):
        moves = []
        color = 'w' if is_white else 'b'
        for r in range(ROWS):
            for c in range(COLS):
                if self.board[r][c].startswith(color):
                    valid_ends = self.get_valid_moves(r, c)
                    for end in valid_ends:
                        moves.append(((r, c), end))
        return moves

    def make_move(self, start, end):
        moved_piece = self.board[start[0]][start[1]]
        target_piece = self.board[end[0]][end[1]]

        self.board[start[0]][start[1]] = '--'
        self.board[end[0]][end[1]] = moved_piece
        self.white_to_move = not self.white_to_move

        # Pawn Promotion Logic
        if moved_piece[1] == 'P':
            if (moved_piece[0] == 'w' and end[0] == 0) or (moved_piece[0] == 'b' and end[0] == 7):
                self.board[end[0]][end[1]] = moved_piece[0] + 'Q'

        # Castling
        if moved_piece[1] == 'K' and abs(start[1] - end[1]) == 2:
            if end[1] == 6:  # Kingside
                self.board[start[0]][5] = self.board[start[0]][7]
                self.board[start[0]][7] = '--'
            elif end[1] == 2:  # Queenside
                self.board[start[0]][3] = self.board[start[0]][0]
                self.board[start[0]][0] = '--'

        if moved_piece == 'wK':
            self.castle_rights['wK'] = self.castle_rights['wQ'] = False
        elif moved_piece == 'bK':
            self.castle_rights['bK'] = self.castle_rights['bQ'] = False

        elif moved_piece == 'wR':
            if start == (7, 7):
                self.castle_rights['wK'] = False
            elif start == (7, 0):
                self.castle_rights['wQ'] = False
        elif moved_piece == 'bR':
            if start == (0, 7):
                self.castle_rights['bK'] = False
            elif start == (0, 0):
                self.castle_rights['bQ'] = False

        if target_piece == 'wR':
            if end == (7, 7):
                self.castle_rights['wK'] = False
            elif end == (7, 0):
                self.castle_rights['wQ'] = False
        elif target_piece == 'bR':
            if end == (0, 7):
                self.castle_rights['bK'] = False
            elif end == (0, 0):
                self.castle_rights['bQ'] = False


# AI Integration
class ChessAI:
    def __init__(self, depth=2):
        self.depth = depth

        # --- Base Values ---
        self.PIECE_VALUES = {'K': 10000, 'Q': 900, 'R': 500, 'B': 330, 'N': 320, 'P': 100}

        # --- Positional Scoring Grids ---
        self.PAWN_SCORES = [
            [900, 900, 900, 900, 900, 900, 900, 900],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5, 5, 10, 25, 25, 10, 5, 5],
            [0, 0, 0, 20, 20, 0, 0, 0],
            [5, -5, -10, 0, 0, -10, -5, 5],
            [5, 10, 10, -20, -20, 10, 10, 5],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]

        self.KNIGHT_SCORES = [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20, 0, 0, 0, 0, -20, -40],
            [-30, 0, 10, 15, 15, 10, 0, -30],
            [-30, 5, 15, 20, 20, 15, 5, -30],
            [-30, 0, 15, 20, 20, 15, 0, -30],
            [-30, 5, 10, 15, 15, 10, 5, -30],
            [-40, -20, 0, 5, 5, 0, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50]
        ]

        self.BISHOP_SCORES = [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 10, 10, 5, 0, -10],
            [-10, 5, 5, 10, 10, 5, 5, -10],
            [-10, 0, 10, 10, 10, 10, 0, -10],
            [-10, 10, 10, 10, 10, 10, 10, -10],
            [-10, 5, 0, 0, 0, 0, 5, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20]
        ]

        self.ROOK_SCORES = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [5, 10, 10, 10, 10, 10, 10, 5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [0, 0, 0, 5, 5, 0, 0, 0]
        ]

        self.KING_SCORES = [
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [20, 20, 0, 0, 0, 0, 20, 20],
            [20, 30, 10, 0, 0, 10, 30, 20]
        ]

    def evaluate_board(self, board):
        score = 0
        for r in range(8):
            for c in range(8):
                piece = board.board[r][c]
                if piece != '--':
                    val = self.PIECE_VALUES[piece[1]]

                    if piece[1] == 'P':
                        bonus = self.PAWN_SCORES[r][c] if piece[0] == 'w' else self.PAWN_SCORES[7 - r][c]
                        val += bonus
                    elif piece[1] == 'N':
                        bonus = self.KNIGHT_SCORES[r][c] if piece[0] == 'w' else self.KNIGHT_SCORES[7 - r][c]
                        val += bonus
                    elif piece[1] == 'B':
                        bonus = self.BISHOP_SCORES[r][c] if piece[0] == 'w' else self.BISHOP_SCORES[7 - r][c]
                        val += bonus
                    elif piece[1] == 'R':
                        bonus = self.ROOK_SCORES[r][c] if piece[0] == 'w' else self.ROOK_SCORES[7 - r][c]
                        val += bonus
                    elif piece[1] == 'K':
                        bonus = self.KING_SCORES[r][c] if piece[0] == 'w' else self.KING_SCORES[7 - r][c]
                        val += bonus

                    score += val if piece[0] == 'w' else -val
        return score

    def quiescence_search(self, board, alpha, beta, maximizing_player):
        stand_pat = self.evaluate_board(board)

        if maximizing_player:
            if stand_pat >= beta: return beta
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha: return alpha
            beta = min(beta, stand_pat)

        all_moves = board.get_all_possible_moves(maximizing_player)
        capture_moves = [m for m in all_moves if board.board[m[1][0]][m[1][1]] != '--']

        if maximizing_player:
            max_eval = stand_pat
            for move in capture_moves:
                temp_board = copy.deepcopy(board)
                temp_board.make_move(move[0], move[1])
                eval = self.quiescence_search(temp_board, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = stand_pat
            for move in capture_moves:
                temp_board = copy.deepcopy(board)
                temp_board.make_move(move[0], move[1])
                eval = self.quiescence_search(temp_board, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return self.quiescence_search(board, alpha, beta, maximizing_player), None

        moves = board.get_all_possible_moves(maximizing_player)
        random.shuffle(moves)

        if len(moves) == 0:
            if board.in_check(maximizing_player):
                return -100000 if maximizing_player else 100000, None
            else:
                return 0, None

        best_move = None
        if maximizing_player:
            max_eval = -math.inf
            for move in moves:
                temp_board = copy.deepcopy(board)
                temp_board.make_move(move[0], move[1])
                eval, _ = self.minimax(temp_board, depth - 1, alpha, beta, False)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval, best_move
        else:
            min_eval = math.inf
            for move in moves:
                temp_board = copy.deepcopy(board)
                temp_board.make_move(move[0], move[1])
                eval, _ = self.minimax(temp_board, depth - 1, alpha, beta, True)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval, best_move

    def get_move(self, board):
        """Public method to call from the main loop."""
        _, best_move = self.minimax(board, self.depth, -math.inf, math.inf, board.white_to_move)
        return best_move


# --- Rendering & Main Loop ---
def draw_board(screen):
    for r in range(ROWS):
        for c in range(COLS):
            color = WHITE if (r + c) % 2 == 0 else BLACK
            pygame.draw.rect(screen, color, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def draw_pieces(screen, board):
    for r in range(ROWS):
        for c in range(COLS):
            piece = board.board[r][c]
            if piece != '--':
                screen.blit(IMAGES[piece], pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


class Button:
    def __init__(self, text, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = (70, 70, 70)
        self.hover_color = (100, 100, 100)
        self.text_color = (255, 255, 255)

    def draw(self, screen, font):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.base_color

        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2, border_radius=8)

        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

def draw_overlays(screen, board, moves, selected_square):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # (Optional) You can keep a background highlight for the selected piece here
    # if you want to know which piece you currently clicked.
    # --- RESTORED: Highlight the selected square (Yellow border) ---
    if selected_square:
        r, c = selected_square
        # (200, 200, 50) is the yellow color, 5 is the thickness of the border
        pygame.draw.rect(screen, (200, 200, 50), pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE), 5)
    # Draw the Move Targets and Capture Rings
    for move in moves:
        r, c = move
        center_x = c * SQ_SIZE + SQ_SIZE // 2
        center_y = r * SQ_SIZE + SQ_SIZE // 2

        if board.board[r][c] == '--':
            # 1. Normal move (empty square): Draw a small solid dot
            pygame.draw.circle(overlay, (0, 0, 0, 80), (center_x, center_y), SQ_SIZE // 6)
        else:
            # 2. Capture move (enemy piece): Draw a hollow ring OVER the piece
            # The last argument '7' is the thickness of the ring's line
            pygame.draw.circle(overlay, (0, 0, 0, 80), (center_x, center_y), SQ_SIZE // 2 - 2, 5)

    # Blit this transparent layer over the main screen
    screen.blit(overlay, (0, 0))


def main():
    pygame.init()
    # 512x512 board + 100px UI panel at the bottom
    screen = pygame.display.set_mode((WIDTH, HEIGHT + 100))
    pygame.display.set_caption("PyGame Chess Training Tool")
    clock = pygame.time.Clock()

    ui_font = pygame.font.SysFont("arial", 16)
    title_font = pygame.font.SysFont("arial", 32, bold=True)
    rules_font = pygame.font.SysFont("arial", 18)  # Slightly bigger font for rules reading

    load_images()

    game_board = Board()
    game_board = Board()
    chess_ai = ChessAI(depth=2)  # <--- NEW: Create the AI Engine
    selected_square = None
    valid_moves = []

    current_mode = 'MENU'
    setup_color = 'w'
    setup_piece = 'P'
    setup_error_text = ""

    game_over = False
    game_over_text = ""

    # Menu Buttons (Shifted up and tightened to fit 5 buttons)
    btn_w, btn_h = 250, 45
    start_y = HEIGHT // 2 - 140
    spacing = 55
    btn_pve = Button("Play with computer", WIDTH // 2 - btn_w // 2, start_y, btn_w, btn_h)
    btn_pvp = Button("Play 1 vs 1", WIDTH // 2 - btn_w // 2, start_y + spacing, btn_w, btn_h)
    btn_setup = Button("Set up position", WIDTH // 2 - btn_w // 2, start_y + spacing * 2, btn_w, btn_h)
    btn_rules = Button("Rules", WIDTH // 2 - btn_w // 2, start_y + spacing * 3, btn_w, btn_h)  # NEW BUTTON
    btn_quit = Button("Quit", WIDTH // 2 - btn_w // 2, start_y + spacing * 4, btn_w, btn_h)

    buttons = [btn_pve, btn_pvp, btn_setup, btn_rules, btn_quit]

    # Setup Choice Buttons
    btn_setup_pve = Button("Play with computer", WIDTH // 2 - btn_w // 2, HEIGHT // 2 - 40, btn_w, btn_h)
    btn_setup_pvp = Button("Play 1 vs 1", WIDTH // 2 - btn_w // 2, HEIGHT // 2 + 30, btn_w, btn_h)

    # --- The Rules Text ---
    rules_text = [
        "BASIC CHESS RULES:",
        "",
        "1. White always moves first.",
        "2. Pawns move forward 1 square or 2 on their first move.",
        "   Pawns capture diagonally.",
        "3. Knights move in an 'L' shape and jump over pieces.",
        "4. Bishops move diagonally any number of squares.",
        "5. Rooks move in straight lines (up/down/left/right).",
        "6. Queens combine the power of Rooks and Bishops.",
        "7. Kings move exactly 1 square in any direction.",
        "8. You cannot leave your King in check.",
        "9. Checkmate occurs when the King is attacked and has",
        "   no legal moves to escape. The game ends.",
        "",
        "Press ESC to return to the Main Menu."
    ]

    running = True
    while running:

        # AI Auto-Move
        if current_mode == 'PVE' and not game_board.white_to_move and not game_over:
            pygame.display.flip()
            best_move = chess_ai.get_move(game_board)
            if best_move:
                game_board.make_move(best_move[0], best_move[1])
                all_moves = game_board.get_all_possible_moves(game_board.white_to_move)
                if len(all_moves) == 0:
                    game_over = True
                    if game_board.in_check(game_board.white_to_move):
                        game_over_text = "Checkmate! Black wins."
                    else:
                        game_over_text = "Stalemate! It's a draw."

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- MENU STATE ---
            if current_mode == 'MENU':
                if btn_pve.is_clicked(event):
                    current_mode = 'PVE'
                    game_board = Board()
                    game_over = False
                elif btn_pvp.is_clicked(event):
                    current_mode = 'PVP'
                    game_board = Board()
                    game_over = False
                elif btn_setup.is_clicked(event):
                    current_mode = 'SETUP'
                    game_board = Board()
                    game_board.board = [['--'] * 8 for _ in range(8)]
                    game_over = False
                    setup_error_text = ""
                elif btn_rules.is_clicked(event):  # NEW LOGIC
                    current_mode = 'RULES'
                elif btn_quit.is_clicked(event):
                    running = False

            # --- ALL OTHER STATES ---
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        current_mode = 'MENU'
                        selected_square = None
                        valid_moves = []

                    if current_mode == 'SETUP':
                        if event.key == pygame.K_RETURN:
                            is_valid, msg = game_board.is_valid_setup()
                            if is_valid:
                                current_mode = 'SETUP_CHOICE'
                                setup_error_text = ""
                            else:
                                setup_error_text = msg

                        if event.key == pygame.K_t:
                            game_board.white_to_move = not game_board.white_to_move
                            setup_error_text = ""

                        if event.key == pygame.K_w: setup_color = 'w'
                        if event.key == pygame.K_b: setup_color = 'b'
                        if event.key == pygame.K_p: setup_piece = 'P'
                        if event.key == pygame.K_r: setup_piece = 'R'
                        if event.key == pygame.K_n: setup_piece = 'N'
                        if event.key == pygame.K_v: setup_piece = 'B'
                        if event.key == pygame.K_q: setup_piece = 'Q'
                        if event.key == pygame.K_k: setup_piece = 'K'
                        if event.key == pygame.K_c:
                            game_board.board = [['--'] * 8 for _ in range(8)]
                            setup_error_text = ""

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    location = pygame.mouse.get_pos()
                    col, row = location[0] // SQ_SIZE, location[1] // SQ_SIZE

                    if row >= 8: continue

                    if current_mode in ['PVP', 'PVE'] and not game_over:
                        if current_mode == 'PVE' and not game_board.white_to_move:
                            continue

                        if selected_square == (row, col):
                            selected_square = None
                            valid_moves = []
                        else:
                            piece = game_board.board[row][col]
                            if selected_square and (row, col) in valid_moves:
                                game_board.make_move(selected_square, (row, col))
                                selected_square = None
                                valid_moves = []

                                all_moves = game_board.get_all_possible_moves(game_board.white_to_move)
                                if len(all_moves) == 0:
                                    game_over = True
                                    if game_board.in_check(game_board.white_to_move):
                                        winner = "Black" if game_board.white_to_move else "White"
                                        game_over_text = f"Checkmate! {winner} wins."
                                    else:
                                        game_over_text = "Stalemate! It's a draw."

                            elif piece != '--' and ((piece[0] == 'w' and game_board.white_to_move) or (
                                    piece[0] == 'b' and not game_board.white_to_move)):
                                selected_square = (row, col)
                                valid_moves = game_board.get_valid_moves(row, col)

                    elif current_mode == 'SETUP':
                        if event.button == 1:
                            game_board.board[row][col] = setup_color + setup_piece
                            setup_error_text = ""
                        elif event.button == 3:
                            game_board.board[row][col] = '--'
                            setup_error_text = ""

                    elif current_mode == 'SETUP_CHOICE':
                        if btn_setup_pve.is_clicked(event):
                            current_mode = 'PVE'
                        elif btn_setup_pvp.is_clicked(event):
                            current_mode = 'PVP'

        # --- DRAWING ROUTINE ---
        if current_mode == 'MENU':
            screen.fill(UI_BG)
            title_surf = title_font.render("CHESS TRAINING TOOL", True, (255, 255, 255))
            screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 200))
            for btn in buttons:
                btn.draw(screen, ui_font)

        elif current_mode == 'RULES':
            screen.fill(UI_BG)  # Fill the whole screen with dark grey
            # Render the text line by line
            y_offset = 30
            for line in rules_text:
                text_surface = rules_font.render(line, True, (220, 220, 220))
                screen.blit(text_surface, (40, y_offset))
                y_offset += 30  # Space between lines

        else:
            screen.fill(UI_BG)
            draw_board(screen)
            draw_pieces(screen, game_board)
            draw_overlays(screen, game_board, valid_moves, selected_square)

            if current_mode == 'SETUP_CHOICE':
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                btn_setup_pve.draw(screen, ui_font)
                btn_setup_pvp.draw(screen, ui_font)

            # Draw UI footer
            turn_text = "White to Move" if game_board.white_to_move else "Black to Move"

            if current_mode == 'SETUP':
                turn_text = f"Turn: {'White' if game_board.white_to_move else 'Black'} | Paint: {setup_color}{setup_piece}"
                if setup_error_text:
                    info_str = f"ERROR: {setup_error_text}"
                else:
                    info_str = "W/B:Color | P/R/N/V/Q/K:Piece | C:Clear | T:Turn | ENTER:Done"
            elif current_mode == 'SETUP_CHOICE':
                turn_text = "Valid Position!"
                info_str = "Choose game mode to play from this position."
            elif game_over:
                turn_text = "Game Over"
                info_str = f"{game_over_text} (Press ESC to return to menu)"
            else:
                if game_board.in_check(game_board.white_to_move):
                    turn_text += " [CHECK!]"
                info_str = "Press ESC to return to Main Menu"

            ui_surf1 = ui_font.render(turn_text, True, (255, 255, 255))
            info_color = (255, 255, 100) if setup_error_text else (200, 200, 200)
            ui_surf2 = ui_font.render(info_str, True, info_color)

            screen.blit(ui_surf1, (10, HEIGHT + 20))
            screen.blit(ui_surf2, (10, HEIGHT + 55))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()