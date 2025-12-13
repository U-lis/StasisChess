import copy
from uuid import uuid4

from enums import Color, PieceType
from piece import Pawn, Rook, Knight, Bishop, Queen, King


class Game:
    def __init__(self):
        self.id = str(uuid4())[:8]
        self.turn = Color.WHITE
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.pieces = {}
        self.hands = {Color.WHITE: [], Color.BLACK: []}
        self.history = []
        self.first_turn_done = {Color.WHITE: False, Color.BLACK: False}
        self.action_done = {}

        self._init_pieces()

    def __add_piece(self, ptype, cnt, color):
        for i in range(cnt):
            pid = f"{color}_{ptype.abbr}{i}"
            piece = None

            if ptype == PieceType.PAWN:
                piece = Pawn(pid, color)
            elif ptype == PieceType.ROOK:
                piece = Rook(pid, color)
            elif ptype == PieceType.KNIGHT:
                piece = Knight(pid, color)
            elif ptype == PieceType.BISHOP:
                piece = Bishop(pid, color)
            elif ptype == PieceType.QUEEN:
                piece = Queen(pid, color)
            elif ptype == PieceType.KING:
                piece = King(pid, color)

            self.pieces[pid] = piece
            self.hands[color].append(pid)

    def _init_pieces(self):
        for color in Color:
            # pawns 8
            self.__add_piece(PieceType.PAWN, 8, color)
            # rooks, bishops, knights x2
            self.__add_piece(PieceType.ROOK, 2, color)
            self.__add_piece(PieceType.BISHOP, 2, color)
            # queen 1, king 1
            self.__add_piece(PieceType.KNIGHT, 2, color)
            self.__add_piece(PieceType.QUEEN, 1, color)

    def to_json(self):
        return {
            "id": self.id,
            "turn": self.turn,
            "pieces": {pid: self.pieces[pid].to_json() for pid in self.pieces},
            "hands": self.hands,
            "history": self.history
        }

    def pos_empty(self, x, y):
        return self.board[y][x] is None

    def get_piece_at(self, x, y):
        _id = self.board[y][x]
        return self.pieces[_id] if _id else None

    def get_piece(self, pid):
        return self.pieces.get(pid)

    def drop_piece(self, player_color, pid, x, y):
        if pid not in self.hands[player_color]:
            return False, "you don't own that piece"

        p = self.pieces[pid]
        if not self.first_turn_done[player_color] and p.type != PieceType.KING:
            return False, "drop king first"

        if not (0 <= x < 8 and 0 <= y < 8):
            return False, "invalid coords"

        if self.board[y][x]:
            return False, "target occupied"

        if p.type == PieceType.PAWN:
            # 폰은 각 플레이어 기준 맨 끝 랭크에 착수할 수 없다.
            if player_color == Color.WHITE and y == 7: return False, "white cannot drop pawn on last rank"
            if player_color == Color.BLACK and y == 0: return False, "black cannot drop pawn on first rank"
            # 폰은 착수 랭크에 따라 스턴 스택이 다르게 쌓이며, 다음과 같다.백 기준으로 랭크 1: 0스턴 스텍 ~ 랭크 7: 6스턴 스텍. 흑은 반대로 랭크 8: 0스턴 스텍 ~ 랭크 2: 6스턴 스텍이다.
            if player_color == Color.WHITE:
                p.stun = y if y <= 6 else 1
            else:
                p.stun = (7 - y) if y >= 1 else 1
        else:
            p.stun = max(1, p.stun)

        p.drop((x, y))
        self.board[y][x] = pid
        self.hands[player_color].remove(pid)
        self.history.append({"action": "drop", "player": player_color, "piece": pid, "pos": [x, y]})
        self.first_turn_done[player_color] = True
        return True, "dropped"

    def move_piece(self, player_color, pid, frm, to):
        x1, y1 = frm
        x2, y2 = to

        if not (0 <= x1 < 8 and 0 <= y1 < 8 and 0 <= x2 < 8 and 0 <= y2 < 8):
            return False, "invalid coords"

        if self.board[y1][x1] != pid:
            return False, "source mismatch"

        piece = self.pieces[pid]
        if piece.color != player_color:
            return False, "not your piece"

        if piece.stun > 0:
            return False, f"piece stunned. remain stun stack : {piece.stun}"

        if not piece.can_move(frm, to, self.board_pieces()):
            return False, "illegal move for piece"

        target_id = self.board[y2][x2]
        is_win = False

        if target_id is not None:
            target = self.pieces[target_id]
            if target.color == piece.color:
                return False, "cannot capture own piece"

            # Check for win condition (king capture)
            if target.type == PieceType.KING:
                is_win = True

            piece.capture(target)
            target.pos = None
            target.captured = True
            target.stun = 0
            target.move_stack = 0
            self.hands[player_color].append(target_id)
            self.board[y2][x2] = None

        # move
        self.board[y1][x1] = None
        self.board[y2][x2] = pid
        piece.pos = (x2, y2)
        piece.move_stack -= 1

        self.history.append({"action": "move", "player": player_color, "piece": pid, "from": [x1, y1], "to": [x2, y2]})

        if is_win:
            return True, "win"

        return True, "moved"

    def board_pieces(self):
        b = [[None for _ in range(8)] for _ in range(8)]
        for y in range(8):
            for x in range(8):
                pid = self.board[y][x]
                if pid:
                    b[y][x] = self.pieces[pid]
        return b

    def safe_after_move(self, pid, frm, to, color):
        gcopy = copy.deepcopy(self)
        ok, msg = gcopy.move_piece(gcopy.pieces[pid].color, pid, frm, to)
        if not ok:
            return False
        king_exists = False
        for p in gcopy.pieces.values():
            if p.type == PieceType.KING and p.color == color and p.pos is not None:
                king_exists = True
        return king_exists

    def end_turn(self):
        for pid, p in self.pieces.items():
            p.end_turn()
        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE
        self.action_done = {}
