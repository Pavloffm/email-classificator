# Add linters ruff, pyright, setting pre-commit, may be github CI 
# Add some wrapper, maybe docker or postman to make more simple init and deploy on any system
from email_classificator.llm import OllamaLLM


def main():
    # 0. Define llm model that will used everywhere
    llm = OllamaLLM(model="TODO")
    
    # 1. Get new emails and check status change
    # Get emails id to classify
    # Track if user read emails (to_read) and replied to email (need_reply)? change status to done
    # Filter emails id from persistent project (that already classified)
    # Get unique emails to classify 

    # 2. Classify new email and change their statuses
    # Classify emails, use Ollama (maybe abstract class with implementation using Ollama, but changable in future easily to another not local provider)
    # Possible categories: need_reply, is_spam, to_read {EmailStatus}
    # Save to persistent local storage changes (SQLite3)

    # 3. Process emails that need_reply and make status have_draft
    # If there is emails to that need_reply than generate Drafts (Using first name surname from .env)
    # Add drafts to emails

if __name__ == "__main__":
    main()