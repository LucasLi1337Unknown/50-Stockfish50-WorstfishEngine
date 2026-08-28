
from flask import Flask, render_template, request, jsonify
import chess
import chess.engine
import os
import random
import shutil
from pathlib import Path

app = Flask(__name__)

board = chess.Board()
last_mode = None
last_eval = None

def find_stockfish():
    env = os.environ.get("STOCKFISH_PATH")
    if env and Path(env).exists():
        return env

    candidates = [
        "./stockfish",
        "./stockfish.exe",
        "./Stockfish/src/stockfish",
        "./Stockfish/src/stockfish.exe",
        "/opt/homebrew/bin/stockfish",
        "/usr/local/bin/stockfish",
    ]
    for p in candidates:
        if Path(p).exists():
            return p

    found = shutil.which("stockfish")
    if found:
        return found

    return None

def score_to_number(info, turn):
    score = info["score"].pov(turn)
    # Huge finite values for mate so sorting still works.
    return score.score(mate_score=100000)

def choose_fish_move(engine, bad_probability=0.50, think_time=0.12):
    """
    1-bad_probability: choose Stockfish's best move.
    bad_probability: choose Stockfish's WORST legal move.
    """
    global last_mode, last_eval

    legal_count = board.legal_moves.count()
    if legal_count == 0:
        return None

    # Ask Stockfish to rank every legal move.
    infos = engine.analyse(
        board,
        chess.engine.Limit(time=max(0.03, float(think_time))),
        multipv=legal_count
    )

    ranked = []
    for info in infos:
        pv = info.get("pv")
        if not pv:
            continue
        ranked.append((score_to_number(info, board.turn), pv[0]))

    if not ranked:
        return None

    ranked.sort(key=lambda x: x[0], reverse=True)

    best_score, best_move = ranked[0]
    worst_score, worst_move = ranked[-1]

    if random.random() < bad_probability:
        last_mode = "RANDOMFISH"
        last_eval = worst_score
        return worst_move
    else:
        last_mode = "STOCKFISH"
        last_eval = best_score
        return best_move

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/state")
def state():
    return jsonify({
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "game_over": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None,
        "last_mode": last_mode,
        "last_eval": last_eval,
    })

@app.post("/reset")
def reset():
    global board, last_mode, last_eval
    board = chess.Board()
    last_mode = None
    last_eval = None
    return jsonify({"ok": True, "fen": board.fen()})

@app.post("/move")
def move():
    global board
    data = request.get_json(force=True)
    move_uci = (data.get("move") or "").strip().lower()
    bad_probability = float(data.get("bad_probability", 0.50))
    think_time = float(data.get("think_time", 0.12))

    # Human plays White in this prototype.
    if board.turn != chess.WHITE:
        return jsonify({"ok": False, "error": "It is not your turn."}), 400

    try:
        move = chess.Move.from_uci(move_uci)
    except Exception:
        return jsonify({"ok": False, "error": "Use UCI format, for example e2e4 or e7e8q."}), 400

    if move not in board.legal_moves:
        return jsonify({"ok": False, "error": "Illegal move."}), 400

    board.push(move)

    if board.is_game_over():
        return jsonify({
            "ok": True,
            "fen": board.fen(),
            "game_over": True,
            "result": board.result(),
            "fish_move": None,
        })

    stockfish_path = find_stockfish()
    if not stockfish_path:
        return jsonify({
            "ok": False,
            "error": "Stockfish executable not found. Put it beside app.py or set STOCKFISH_PATH."
        }), 500

    try:
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            fish_move = choose_fish_move(engine, bad_probability, think_time)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Could not run Stockfish: {e}"}), 500

    if fish_move is None:
        return jsonify({"ok": False, "error": "Randomfish could not find a move."}), 500

    board.push(fish_move)

    return jsonify({
        "ok": True,
        "fen": board.fen(),
        "fish_move": fish_move.uci(),
        "mode": last_mode,
        "evaluation": last_eval,
        "game_over": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None,
    })

if __name__ == "__main__":
    print("Stockfish + Randomfish")
    print("Open http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
