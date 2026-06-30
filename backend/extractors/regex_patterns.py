import re

# Email regex — allows optional whitespace before '@' to handle PDF text extraction artifacts
# where pdfplumber may insert spaces (e.g. "vishwasr762 @gmail.com")
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)

# Phone regex
# Handles the following real-world formats found in Indian resumes:
#   3-3-4  (US/global): +1-987-654-3210  (123) 456-7890  123.456.7890
#   5-5    (Indian):    +91 90147 46514   90147 46514   +91-90147-46514
#   10-dig (Indian):    +91 9014746514    9876543210
PHONE_PATTERN = re.compile(
    r'(?:\+?\d{1,3}[\s.-]?)?'      # optional country code: +91, +1, etc.
    r'(?:'
    r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'   # 3-3-4: (123) 456-7890 / 9876543210
    r'|\d{5}[\s.-]\d{5}'                        # 5-5:   90147 46514  (Indian split)
    r')'
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
