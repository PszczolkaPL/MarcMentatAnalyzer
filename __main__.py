import sys

try:
    from .main import main
except ImportError:  # pragma: no cover
    from main import main


if __name__ == "__main__":
    main(sys.argv[1:])
