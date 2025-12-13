from __future__ import annotations

from enums import Color, PieceType, Position


class Piece:
    def __init__(self, pid: str, piece_type: PieceType, color: Color, pos: Position | None = None):
        self.id: str = pid
        self.type: PieceType = piece_type
        self.color: Color = color
        self.pos: Position | None = pos  # (x,y) or None
        self.stun: int = 0
        self.move_stack: int = 0
        self.captured: bool = False  # Piece is not captured at the beginning of the game

    @staticmethod
    def create(pid, piece_type: PieceType, color: Color):
        return {
            PieceType.PAWN: Pawn,
            PieceType.ROOK: Rook,
            PieceType.BISHOP: Bishop,
            PieceType.KNIGHT: Knight,
            PieceType.QUEEN: Queen,
            PieceType.KING: King,
        }[piece_type](pid, color)

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
    def can_move(self, frm: Position, to: Position, board):
        raise NotImplementedError("Need to be implemented in subclass")

    def drop(self, pos: Position):
        self.pos = pos
        self.captured = False
        self.stun = 1
        self.move_stack = 0

    def capture(self, target: Piece):
        # 만약 스택이 쌓여있는 기물을 잡았을 경우, 그 스택이 잡은 기물에게 이전된다.
        self.stun += target.stun
        self.move_stack += target.move_stack
        target.color = self.color

        # Clear the target piece's position and captured flag
        target.pos = None
        target.captured = True
        target.stun = 0
        target.move_stack = 0

    def end_turn(self):
        # 이동 스텍은 스턴 스텍이 턴을 넘겨서 1씩 사라질 때마다 1씩 늘어난다.
        if not self.captured and self.stun > 0:
            self.stun -= 1
            self.move_stack += 1


class Knight(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.KNIGHT, color, pos)

    def can_move(self, frm: Position, to: Position, board):
        dx = abs(frm.x - to.x)
        dy = abs(frm.y - to.y)
        return (dx == 1 and dy == 2) or (dx == 2 and dy == 1)


class Rook(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.ROOK, color, pos)

    def can_move(self, frm: Position, to: Position, board):
        if frm.x != to.x and frm.y != to.y: return False
        dx = 0 if frm.x == to.x else (1 if to.x > frm.x else -1)
        dy = 0 if frm.y == to.y else (1 if to.y > frm.y else -1)
        x, y = frm.x + dx, frm.y + dy
        while (x, y) != to:
            if board[y][x] is not None:
                return False
            x += dx
            y += dy
        return True


class Bishop(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.BISHOP, color, pos)

    def can_move(self, frm: Position, to: Position, board):
        dx = to.x - frm.x
        dy = to.y - frm.y
        if abs(dx) != abs(dy):
            return False

        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        x, y = frm.x + sx, frm.y + sy
        while (x, y) != to:
            if board[y][x] is not None:
                return False
            x += sx
            y += sy
        return True


class Queen(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.QUEEN, color, pos)

    def can_move(self, frm: Position, to: Position, board):
        r = Rook('temp', self.color)
        b = Bishop('temp', self.color)
        return r.can_move(frm, to, board) or b.can_move(frm, to, board)


class King(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.KING, color, pos)

    def can_move(self, frm: Position, to: Position, board):
        dx = abs(frm.x - to.x)
        dy = abs(frm.y - to.y)
        return max(dx, dy) == 1


class Pawn(Piece):
    def __init__(self, pid, color, pos=None):
        super().__init__(pid, PieceType.PAWN, color, pos)

    def can_move(self, frm: Position, to: Position, board):
        dir = 1 if self.color == Color.BLACK else -1
        if to.x == frm.x and to.y == frm.y + dir:
            return board[to.y][to.x] is None

        if abs(to.x - frm.x) == 1 and to.y == frm.y + dir:
            target = board[to.y][to.x]
            return (target is not None) and (target.color != self.color)
        return False
