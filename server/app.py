# server/app.py
import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room

from game import Game

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Game Management ---
games = {}
player_game_map = {}


def get_game_for_player(sid):
    game_id = player_game_map.get(sid)
    if game_id:
        return games.get(game_id)
    return None


# ---------------------------
# SocketIO events
# ---------------------------
@socketio.on('connect')
def on_connect():
    sid = request.sid
    print(f"connect {sid}")
    # For this refactoring, we create a new game for each connection.
    # A real implementation would have a lobby, game creation, and joining logic.
    game = Game()
    games[game.id] = game
    player_game_map[sid] = game.id
    join_room(game.id)

    emit('connected', {'sid': sid, 'game_id': game.id})
    # send initial state for the new game
    emit('game_state', game.to_json())


@socketio.on('join_game')  # A new event to handle rejoining/multiple players
def on_join(data):
    sid = request.sid
    game_id = data.get('game_id')
    game = games.get(game_id)
    if game:
        player_game_map[sid] = game_id
        join_room(game.id)
        emit('joined', {'game_id': game.id}, to=sid)
        socketio.emit('game_state', game.to_json(), to=game.id)
    else:
        emit('error', {'reason': 'game_not_found'}, to=sid)


@socketio.on('move_request')
def on_move_request(data):
    sid = request.sid
    game = get_game_for_player(sid)
    if not game:
        emit('move_rejected', {'reason': 'game_not_found'}, to=sid)
        return

    player_color = data.get('player_color')
    pid = data.get('piece_id')
    frm = tuple(data.get('from'))
    to = tuple(data.get('to'))

    # check turn
    if player_color != game.turn:
        emit('move_rejected', {'reason': 'not_your_turn'}, to=sid)
        return

    if game.action_done.get(player_color):
        emit('move_rejected', {'reason': 'already_moved_this_turn'}, to=sid)
        return

    piece = game.get_piece(pid)
    if piece is None:
        emit('move_rejected', {'reason': 'no_such_piece'}, to=sid)
        return

    if piece.stun > 0:
        emit('move_rejected', {'reason': 'stunned', 'stun': piece.stun}, to=sid)
        return

    if not piece.can_move(frm, to, game.board_pieces()):
        emit('move_rejected', {'reason': 'illegal_move'}, to=sid)
        return

    if not game.safe_after_move(pid, frm, to, piece.color):
        emit('move_rejected', {'reason': 'suicide_or_king_lost'}, to=sid)
        return

    ok, msg = game.move_piece(player_color, pid, frm, to)
    if not ok:
        emit('move_rejected', {'reason': msg}, to=sid)
        return
    game.action_done[player_color] = True
    socketio.emit('move_accepted', {'by': player_color, 'move': {'piece': pid, 'from': frm, 'to': to}}, to=game.id)
    socketio.emit('game_state', game.to_json(), to=game.id)
    if msg == "win":
        winner = player_color
        loser = 'b' if player_color == 'w' else 'w'
        socketio.emit('game_end', {'winner': winner, 'loser': loser, 'reason': 'king_capture'}, to=game.id)
        return


@socketio.on('drop_request')
def on_drop_request(data):
    sid = request.sid
    game = get_game_for_player(sid)
    if not game:
        emit('drop_rejected', {'reason': 'game_not_found'}, to=sid)
        return

    player_color = data.get('player_color')
    pid = data.get('piece_id')
    to = tuple(data.get('to'))

    if player_color != game.turn:
        emit('drop_rejected', {'reason': 'not_your_turn'}, to=sid)
        return

    ok, msg = game.drop_piece(player_color, pid, to[0], to[1])
    if not ok:
        emit('drop_rejected', {'reason': msg}, to=sid)
        return

    socketio.emit('drop_accepted', {'by': player_color, 'piece': pid, 'to': to}, to=game.id)
    socketio.emit('game_state', game.to_json(), to=game.id)


@socketio.on('end_turn')
def on_end_turn():
    sid = request.sid
    game = get_game_for_player(sid)
    if not game:
        # Or just log an error, since there's no specific client to reject to.
        print(f"end_turn requested by {sid} but no game found.")
        return

    game.end_turn()
    socketio.emit('turn_ended', {'turn': game.turn}, to=game.id)
    socketio.emit('game_state', game.to_json(), to=game.id)


@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    print(f"disconnect {sid}")
    game_id = player_game_map.pop(sid, None)
    if game_id:
        game = games.get(game_id)
        # Optional: Implement logic to handle player disconnection, 
        # e.g., pause game, notify other player, or clean up game if empty.
        # For now, we'll just remove the player from the map.
        pass


# basic http endpoint
@app.route('/ping')
def ping():
    return {"ok": True}


if __name__ == "__main__":
    socketio.run(app, host=os.getenv("HOST"), port=int(os.getenv("PORT")), debug=os.getenv("DEBUG") == "True")
