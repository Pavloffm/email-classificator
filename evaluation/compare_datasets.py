import json
from pathlib import Path

from email_classificator.email_client import EmailLabels
from email_classificator.logger import logger


def load_labels(path: Path) -> dict[str, str]:
    dataset = json.loads(path.read_text(encoding="utf-8"))
    labels: dict[str, str] = {}

    for email in dataset:
        email_id = email["email_id"]
        if email_id in labels:
            raise ValueError(f"Duplicate email ID in {path.name}: {email_id}")

        try:
            labels[email_id] = EmailLabels(email["label"]).value
        except ValueError as error:
            raise ValueError(
                f"Missing or invalid label in {path.name}: {email_id}"
            ) from error

    return labels


def main() -> None:
    dataset_dir = Path(__file__).resolve().parents[1] / "data/dataset"
    expected = load_labels(dataset_dir / "email_label.json")
    predicted = load_labels(dataset_dir / "email_label_llm.json")

    if expected.keys() != predicted.keys():
        missing = expected.keys() - predicted.keys()
        extra = predicted.keys() - expected.keys()
        raise ValueError(
            f"Dataset IDs differ. Missing predictions: {sorted(missing)}; "
            f"Extra predictions: {sorted(extra)}"
        )

    if not expected:
        raise ValueError("Dataset is empty")

    correct = 0
    for email_id, expected_label in expected.items():
        predicted_label = predicted[email_id]
        if expected_label == predicted_label:
            correct += 1
        else:
            logger.info(
                "Mismatch {}: expected={}, predicted={}",
                email_id,
                expected_label,
                predicted_label,
            )

    total = len(expected)
    logger.info("Correct: {}/{}", correct, total)
    logger.info("Incorrect: {}", total - correct)
    logger.info("Accuracy: {:.2%}", correct / total)

    for label in EmailLabels:
        email_ids = [
            email_id for email_id, value in expected.items() if value == label.value
        ]
        if not email_ids:
            continue

        matches = sum(predicted[email_id] == label.value for email_id in email_ids)
        logger.info(
            "{} recall: {}/{} ({:.2%})",
            label.value,
            matches,
            len(email_ids),
            matches / len(email_ids),
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Dataset comparison failed")
        raise
