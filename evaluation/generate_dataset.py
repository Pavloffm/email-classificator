import json
from pathlib import Path

from email_classificator.email_client import EmailClient
from email_classificator.logger import logger


def main() -> None:
    output_path = Path(__file__).resolve().parents[1] / "data/dataset/email_label.json"
    if output_path.exists():
        raise FileExistsError(f"Dataset already exists: {output_path}")

    logger.info("Initializing email client")
    client = EmailClient()

    logger.info("Fetching last 100 email IDs")
    email_ids = client.get_last_100_email_ids()
    logger.info("Found {} emails", len(email_ids))

    dataset = []
    for index, email_id in enumerate(email_ids, start=1):
        logger.info("Fetching email {}/{}: {}", index, len(email_ids), email_id)
        dataset.append(
            {
                "email_id": email_id,
                "content": client.get_email_content(email_id),
                "label": None,
            }
        )

    logger.info("Saving dataset to {}", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as file:
        json.dump(dataset, file, ensure_ascii=False, indent=2)
        file.write("\n")

    logger.success("Saved {} emails to {}", len(dataset), output_path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Dataset generation failed")
        raise
