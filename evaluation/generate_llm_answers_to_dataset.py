import json
from pathlib import Path

from email_classificator.classificator import classify_email
from email_classificator.email_client import normalize_email_body
from email_classificator.llm import OllamaLLM
from email_classificator.logger import logger


def main() -> None:
    dataset_dir = Path(__file__).resolve().parents[1] / "data/dataset"
    input_path = dataset_dir / "email_label.json"
    output_path = dataset_dir / "email_label_llm.json"

    if output_path.exists():
        raise FileExistsError(f"Dataset already exists: {output_path}")

    logger.info("Loading dataset from {}", input_path)
    dataset = json.loads(input_path.read_text(encoding="utf-8"))
    logger.info("Loaded {} emails", len(dataset))

    logger.info("Initializing LLM")
    llm = OllamaLLM(model="gemma4:e4b")

    predictions = []
    for index, email in enumerate(dataset, start=1):
        logger.info(
            "Classifying email {}/{}: {}",
            index,
            len(dataset),
            email["email_id"],
        )
        content = normalize_email_body(email["content"])
        label = classify_email(content, llm)
        predictions.append({**email, "label": label.value})
        logger.info("Predicted label: {}", label.value)

    logger.info("Saving predictions to {}", output_path)
    with output_path.open("x", encoding="utf-8") as file:
        json.dump(predictions, file, ensure_ascii=False, indent=2)
        file.write("\n")

    logger.success("Saved {} predictions to {}", len(predictions), output_path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Dataset classification failed")
        raise
