from typing import Tuple

from enums import Color, PieceType


class Piece:
    def __init__(self, pid: str, piece_type: PieceType, color: Color, pos: Tuple[int, int] | None = None):
        self.id: str = pid
        self.type: PieceType = piece_type
        self.color: Color = color
        self.pos: Tuple[int, int] | None = pos  # (x,y) or None
        self.stun: int = 0
        self.move_stack: int = 0
        self.captured: bool = False  # Piece is not captured at the beginning of the game

    def to_json(self):
        return {
            "id": self.id,
            "type": self.type.value,
            "color": self.color.value,
            "pos": list(self.pos) if self.pos else None,
            "stun": self.stun,
            "move_stack": self.move_stack,
            "captured": self.captured
        }

    # 각 기물 클래스에서 오버라이드
    def can_move(self, frm, to, board):
        raise NotImplementedError("Need to be implemented in subclass")

    def drop(self, pos):
        self.pos = pos
        self.captured = False
        self.stun = 1
        self.move_stack = 0

    def capture(self, target):
        # 만약 스택이 쌓여있는 기물을 잡았을 경우, 그 스택이 잡은 기물에게 이전된다.
        self.stun += target.stun
        self.move_stack += target.move_stack
        target.color = self.color

    def end_turn(self):
        # 이동 스텍은 스턴 스텍이 턴을 넘겨서 1씩 사라질 때마다 1씩 늘어난다.
        if self.captured:
            return
        if self.stun > 0:
            self.stun -= 1
            self.move_stack += 1


class Knight(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.KNIGHT, color, pos)

    def can_move(self, frm, to, board):
        dx = abs(frm[0] - to[0])
        dy = abs(frm[1] - to[1])
        return (dx == 1 and dy == 2) or (dx == 2 and dy == 1)


class Rook(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.ROOK, color, pos)

    def can_move(self, frm, to, board):
        if frm[0] != to[0] and frm[1] != to[1]: return False
        dx = 0 if frm[0] == to[0] else (1 if to[0] > frm[0] else -1)
        dy = 0 if frm[1] == to[1] else (1 if to[1] > frm[1] else -1)
        x, y = frm[0] + dx, frm[1] + dy
        while (x, y) != to:
            if board[y][x] is not None: return False
            x += dx
            y += dy
        return True


class Bishop(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.BISHOP, color, pos)

    def can_move(self, frm, to, board):
        dx = to[0] - frm[0]
        dy = to[1] - frm[1]
        if abs(dx) != abs(dy): return False
        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        x, y = frm[0] + sx, frm[1] + sy
        while (x, y) != to:
            if board[y][x] is not None: return False
            x += sx
            y += sy
        return True


class Queen(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.QUEEN, color, pos)

    def can_move(self, frm, to, board):
        r = Rook('temp', self.color)
        b = Bishop('temp', self.color)
        return r.can_move(frm, to, board) or b.can_move(frm, to, board)


class King(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.KING, color, pos)

    def can_move(self, frm, to, board):
        dx = abs(frm[0] - to[0])
        dy = abs(frm[1] - to[1])
        return max(dx, dy) == 1


class Pawn(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.PAWN, color, pos)

    def can_move(self, frm, to, board):
        dir = 1 if self.color == Color.BLACK else -1
        if to[0] == frm[0] and to[1] == frm[1] + dir:
            return board[to[1]][to[0]] is None

        if abs(to[0] - frm[0]) == 1 and to[1] == frm[1] + dir:
            target = board[to[1]][to[0]]
            return (target is not None) and (target.color != self.color)
        return False
