import copy

def clone_game(game):
    return copy.deepcopy(game)

def get_all_actions(game, color):
    actions = []

    # 이동
    for pid, p in game.pieces.items():
        if p.color != color:
            continue
        if p.pos is None:
            continue
        for to in game.get_legal_moves(pid):
            actions.append(("move", pid, p.pos, to))

    # 드롭
    empty_squares = []
    for y in range(8):
        for x in range(8):
            if game.pos_empty(x, y):
                empty_squares.append((x, y))

    for pid in game.hands[color]:
        piece = game.get_piece(pid)
        if not piece:
            continue

        # 첫 턴에는 킹만 드롭 가능
        if not game.first_turn_done[color] and piece.type != 'king':
            continue

        for x, y in empty_squares:
            # 폰 드롭 규칙
            if piece.type == 'pawn':
                if color == 'w' and y == 7: # 백은 마지막 랭크에 드롭 불가
                    continue
                if color == 'b' and y == 0: # 흑은 첫 랭크에 드롭 불가
                    continue
            
            # 모든 조건을 통과하면 합법적인 드롭
            actions.append(("drop", pid, (x, y)))
            
    return actions

def apply_action(game, action):
    kind = action[0]

    if kind == "move":
        _, pid, frm, to = action
        game.move_piece(game.turn, pid, frm, to)

    elif kind == "drop":
        _, pid, to = action
        game.drop_piece(game.turn, pid, to[0], to[1])

    return game