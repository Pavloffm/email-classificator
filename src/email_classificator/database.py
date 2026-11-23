from enum import StrEnum


class EmailStatus(StrEnum):
    TO_READ = "to_read"
    NEED_REPLY = "need_reply"
    HAVE_DRAFT = "have_draft"
    IS_SPAM = "is_spam"
    DONE = "done"


class Database:
    def __init__(self, db_path):
        # Create table if it not exist
        ...

    # Methods for classify
