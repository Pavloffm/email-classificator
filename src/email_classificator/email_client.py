import base64
import os
import re
from email import policy
from email.parser import BytesParser
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class EmailLabels(StrEnum):
    TO_READ = "to_read"
    NEED_REPLY = "need_reply"
    IS_SPAM = "is_spam"
    CAN_SKIP = "can_skip"


class EmailClient:
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.labels",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    def __init__(self, *, interactive: bool = True, reauthorize: bool = False):
        self.interactive = interactive
        secrets_dir = (
            Path(os.environ.get("EMAIL_SECRETS_DIR", "secrets")).expanduser().resolve()
        )
        self.credentials_path = secrets_dir / "credentials.json"
        self.token_path = secrets_dir / "token.json"
        self.gmail = self._build_gmail(reauthorize=reauthorize)
        self._ensure_labels()

    def _build_gmail(self, *, reauthorize: bool = False):
        credentials = None
        if self.token_path.exists() and not reauthorize:
            credentials = Credentials.from_authorized_user_file(
                str(self.token_path), self.SCOPES
            )

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                if not self.interactive:
                    raise RuntimeError(
                        "Gmail authorization required. Run 'email-classificator auth' "
                        "on a desktop and deploy secrets/token.json before scheduling."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES
                )
                credentials = flow.run_local_server(port=0)

            self.token_path.write_text(credentials.to_json(), encoding="utf-8")
            self.token_path.chmod(0o600)

        return build("gmail", "v1", credentials=credentials)

    # Not that good in design to adding in email_client, but too much abstractions will be worse for that kind small project
    def _ensure_labels(self) -> None:
        labels_api = self.gmail.users().labels()
        response = labels_api.list(userId="me").execute()
        existing_names = {label["name"] for label in response.get("labels", [])}

        for label in EmailLabels:
            if label.value not in existing_names:
                labels_api.create(
                    userId="me",
                    body={"name": label.value},
                ).execute()

    def set_label_for_email(self, email_id: str, label: EmailLabels) -> dict:
        response = self.gmail.users().labels().list(userId="me").execute()

        label_id = next(
            item["id"]
            for item in response.get("labels", [])
            if item["name"] == label.value
        )

        return (
            self.gmail.users()
            .messages()
            .modify(
                userId="me",
                id=email_id,
                body={"addLabelIds": [label_id]},
            )
            .execute()
        )

    def get_unread_unlabeled_email_ids(self) -> list[str]:
        """Find recent unread emails without any app-owned label."""
        email_ids = []
        page_token = None
        query = "is:unread newer_than:14d " + " ".join(
            f"-label:{label.value}" for label in EmailLabels
        )

        while True:
            response = (
                self.gmail.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=500,
                    pageToken=page_token,
                )
                .execute()
            )

            email_ids.extend(message["id"] for message in response.get("messages", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                return email_ids

    def get_email_content(self, email_id: str) -> str:
        response = (
            self.gmail.users()
            .messages()
            .get(userId="me", id=email_id, format="raw")
            .execute()
        )

        raw = response["raw"]
        decoded = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
        message = BytesParser(policy=policy.default).parsebytes(decoded)

        body = message.get_body(preferencelist=("plain", "html"))
        content = (
            normalize_email_body(
                body.get_content(), is_html=body.get_content_type() == "text/html"
            )
            if body
            else ""
        )
        subject = " ".join(str(message.get("Subject", "")).split())
        sender = " ".join(str(message.get("From", "")).split())

        return f"Subject: {subject}\nFrom: {sender}\n\n{content}".rstrip()

    def get_last_100_email_ids(self) -> list[str]:
        """Return up to 100 newest inbox email IDs, excluding drafts and sent."""
        email_ids: list[str] = []
        page_token = None

        while len(email_ids) < 100:
            response = (
                self.gmail.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=["INBOX"],
                    q="-in:drafts -in:sent",
                    maxResults=100 - len(email_ids),
                    pageToken=page_token,
                )
                .execute()
            )
            email_ids.extend(message["id"] for message in response.get("messages", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return email_ids


def normalize_email_body(body: str, *, is_html: bool = False) -> str:
    """Normalize HTML when applicable, then links and whitespace."""
    if is_html:
        body = normalize_html(body)
    return normalize_whitespace(normalize_links(body))


def normalize_html(body: str) -> str:
    """Extract readable text and link destinations without markup or styles."""
    soup = BeautifulSoup(body, "html.parser")
    for tag in soup.select("head, script, style, template"):
        tag.decompose()

    for link in soup.select("a[href]"):
        href = link.get("href")
        if isinstance(href, str) and href.lower().startswith(("http://", "https://")):
            link.append(f" ({href})")

    return soup.get_text(separator="\n", strip=True)


def normalize_links(body: str) -> str:
    """Replace URL paths and tracking parameters with hostnames."""

    def replace_url(match: re.Match[str]) -> str:
        original = match.group()
        url = original.rstrip(".,;:!?)]}")
        suffix = original[len(url) :]
        try:
            hostname = urlsplit(url if "://" in url else f"https://{url}").hostname
        except ValueError:
            return original
        return f"{hostname}{suffix}" if hostname else original

    return re.sub(
        r"(?:https?://|www\.)[^\s<>\"']+", replace_url, body, flags=re.IGNORECASE
    )


def normalize_whitespace(body: str) -> str:
    """Collapse repeated spaces and blank lines while retaining paragraphs."""
    lines = [" ".join(line.split()) for line in body.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
