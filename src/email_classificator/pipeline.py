import os

from email_classificator.classificator import classify_email
from email_classificator.email_client import (
    EmailClient,
    EmailLabels,
    normalize_email_body,
)
from email_classificator.llm import OllamaLLM
from email_classificator.logger import logger


def delete_labels():
    """Dangerous!!! remove app labels from unread emails received in the last 14 days."""
    logger.warning("Starting app-label removal.")

    client = EmailClient()
    app_names = {label.value for label in EmailLabels}
    response = client.gmail.users().labels().list(userId="me").execute()
    label_ids = [
        label["id"]
        for label in response.get("labels", [])
        if label["name"] in app_names
    ]

    if not label_ids:
        logger.info("No app labels found; nothing to remove.")
        return

    query = (
        "is:unread newer_than:14d {"
        + " ".join(f"label:{label.value}" for label in EmailLabels)
        + "}"
    )
    email_ids = []
    page_token = None

    # Collect every page before changing labels so the result set stays stable.
    while True:
        response = (
            client.gmail.users()
            .messages()
            .list(userId="me", q=query, maxResults=500, pageToken=page_token)
            .execute()
        )
        email_ids.extend(message["id"] for message in response.get("messages", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    logger.warning("Removing app labels from {} emails.", len(email_ids))
    for updated, email_id in enumerate(email_ids, start=1):
        try:
            client.gmail.users().messages().modify(
                userId="me",
                id=email_id,
                body={"removeLabelIds": label_ids},
            ).execute()
        except Exception as error:
            logger.error(
                "Label removal failed ({}) after {} successful updates.",
                type(error).__name__,
                updated - 1,
            )
            raise
        logger.debug("Removed app labels from email {}/{}.", updated, len(email_ids))
    logger.info("Label removal completed: {} emails updated.", len(email_ids))


def main():
    llm = OllamaLLM(model=os.environ.get("OLLAMA_MODEL", "gemma4:e4b"))
    client = EmailClient(interactive=False)
    for email_id in client.get_unread_unlabeled_email_ids():
        content = normalize_email_body(client.get_email_content(email_id))
        label = classify_email(content, llm)
        client.set_label_for_email(email_id, label)


if __name__ == "__main__":
    main()
