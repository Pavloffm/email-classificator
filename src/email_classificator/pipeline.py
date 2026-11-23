# {{Add linters ruff, pyright, setting pre-commit,}} may be github CI
# Add some wrapper, maybe docker or postman to make more simple init and deploy on any system
from email_classificator.classificator import classify_email
from email_classificator.email_client import (
    EmailClient,
    EmailLabels,
    normalize_email_body,
)
from email_classificator.llm import OllamaLLM


def delete_labels():
    "Dangerous!!! Remove app labels from unread emails received in the last 14 days"
    client = EmailClient()
    app_names = {label.value for label in EmailLabels}
    response = client.gmail.users().labels().list(userId="me").execute()
    label_ids = [
        label["id"]
        for label in response.get("labels", [])
        if label["name"] in app_names
    ]

    if not label_ids:
        return

    for email_id in client.get_unread_unlabeled_email_ids():
        client.gmail.users().messages().modify(
            userId="me",
            id=email_id,
            body={"removeLabelIds": label_ids},
        ).execute()


def main():
    llm = OllamaLLM(model="gemma4:e4b")
    client = EmailClient()
    for email_id in client.get_unread_unlabeled_email_ids():
        content = normalize_email_body(client.get_email_content(email_id))
        label = classify_email(content, llm)
        client.set_label_for_email(email_id, label)


if __name__ == "__main__":
    main()
