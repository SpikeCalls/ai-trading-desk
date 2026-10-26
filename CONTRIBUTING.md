# Contributing

Thanks for helping make the desk sharper.

## Ground rules

1. **No live execution, no keys.** PRs that add signing, private keys or seed phrases will be closed.
2. **The model never sizes a trade.** Sizing and limits live in `desk/risk.py`, in plain code.
3. **Numbers live in `config.py`.** No magic thresholds inside functions.
4. **Facts before judgements.** If a check can be a comparison, it doesn't go to the model.
5. **Every rejection returns a reason** and lands in the journal.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make test
```

## Pull requests

- One change per PR. Tests for anything that is code.
- Run `make test` before you push. CI runs the same suite on Python 3.10 to 3.13.
- Describe which seat the change touches and why.
