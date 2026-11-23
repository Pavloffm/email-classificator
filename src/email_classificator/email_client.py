import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class EmailClient:
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(self):
        secrets_dir = (
            Path(os.environ.get("EMAIL_SECRETS_DIR", "secrets")).expanduser().resolve()
        )
        self.credentials_path = secrets_dir / "credentials.json"
        self.token_path = secrets_dir / "token.json"
        self.gmail = None

    def init_gmail(self):
        credentials = None
        if self.token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(self.token_path), self.SCOPES
            )

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES
                )
                credentials = flow.run_local_server(port=0)

            self.token_path.write_text(credentials.to_json(), encoding="utf-8")
            self.token_path.chmod(0o600)

        self.gmail = build("gmail", "v1", credentials=credentials)

    def get_new_emails(self):
        # Get new emails that was not used by user
        ...

    def create_draft(self):
        # Create draft for email
        ...
