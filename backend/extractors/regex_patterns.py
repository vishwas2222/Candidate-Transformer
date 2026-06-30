import re

# Email regex — allows optional whitespace before '@' to handle PDF text extraction artifacts
# where pdfplumber may insert spaces (e.g. "vishwasr762 @gmail.com")
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)

# Phone regex (Supports: 9876543210, +1-987-654-3210, (123) 456-7890, 123.456.7890, etc.)
PHONE_PATTERN = re.compile(
    r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
)

# LinkedIn Profile URL regex
LINKEDIN_PATTERN = re.compile(
    r'https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?'
)

# GitHub Profile URL regex
GITHUB_PATTERN = re.compile(
    r'https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+/?'
)

# Portfolio or Generic Personal Site URL regex (excluding linkedin/github)
PORTFOLIO_PATTERN = re.compile(
    r'https?://(?:www\.)?(?!linkedin\.com|github\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[a-zA-Z0-9_-]*)*/?'
)
