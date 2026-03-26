"""Entry point for Calcio Manager."""

from calcio_manager.app import CalcioManagerApp


def main() -> None:
    """Launch the Calcio Manager TUI application."""
    app = CalcioManagerApp()
    app.run()


if __name__ == "__main__":
    main()
