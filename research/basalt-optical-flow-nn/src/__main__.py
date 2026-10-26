"""Allow `python -m src.compare` and `python -m src`."""

from .compare import main

if __name__ == "__main__":
    raise SystemExit(main())
