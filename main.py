import os
import sys

if __package__ is None or __package__ == "":
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from .cli.app import MarcAnalyzerApp
else:
    from .cli.app import MarcAnalyzerApp


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] in {"--help", "-h"}:
        if __package__ is None or __package__ == "":
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from .cli.outputs import print_help_menu
        else:
            from .cli.outputs import print_help_menu

        print_help_menu()
        return

    default_file = argv[0] if argv and not argv[0].startswith("-") else "model6_Stress.out"
    app = MarcAnalyzerApp(
        default_file=default_file if os.path.exists(default_file) else None
    )
    app.cmdloop()


if __name__ == "__main__":
    main()
