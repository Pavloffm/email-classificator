from email_classificator.database import EmailStatus
from email_classificator.llm import LLM_Provider


def classify_email(email: str, llm: LLM_Provider) -> EmailStatus:
    # Get email and go through classification graph
    ...
    return EmailStatus.IS_SPAM
