from collections import namedtuple
from enum import Enum

Position = namedtuple("Position", ["x", "y"])


class Color(Enum):
    WHITE = 'w'
    BLACK = 'b'


class PieceType(Enum):
    PAWN = "pawn"
    ROOK = "rook"
    KNIGHT = "knight"
    BISHOP = "bishop"
    QUEEN = "queen"
    KING = "king"

    @property
    def abbr(self):
        return "N" if self == PieceType.KNIGHT else self.value[0].upper()
