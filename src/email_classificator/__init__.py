def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Classify Gmail messages using Ollama."
    )
    parser.add_argument(
        "command",
        choices=("auth", "classify", "schedule"),
        nargs="?",
        default="classify",
    )
    command = parser.parse_args().command

    if command == "auth":
        from email_classificator.email_client import EmailClient

        EmailClient(reauthorize=True)
    else:
        from email_classificator.scheduler import run_once, schedule

        if command == "schedule":
            schedule()
        else:
            run_once()
