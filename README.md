
# Stockfish + Randomfish 🐟🎲

A tiny local chess website where the engine flips a coin every turn:

- **Stockfish mode:** choose the best legal move.
- **Randomfish mode:** choose the worst legal move according to Stockfish's own evaluation.
- Use the **Randomfish probability** slider from 0% to 100%.

## 1. Get Stockfish

Download/build Stockfish, then either:

- put the executable next to `app.py` and name it `stockfish`, or
- set the environment variable `STOCKFISH_PATH`.

On macOS with Homebrew, if available:

```bash
brew install stockfish
```

## 2. Install Python packages

```bash
python3 -m pip install -r requirements.txt
```

## 3. Run

```bash
python3 app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## How the cursed move picker works

The backend asks Stockfish for a MultiPV ranking of all legal moves.

- best move = highest evaluation from the side-to-move point of view
- worst move = lowest evaluation
- a random number decides which one is played

This is intentionally ridiculous.

## Notes

- You play White in this first version.
- Click source square, then destination square.
- Promotions become queens automatically.
- Increasing thinking time makes the rankings stronger but slower.
