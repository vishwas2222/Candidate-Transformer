import re
from typing import List, Dict, Any
from extractors.regex_patterns import EMAIL_PATTERN, PHONE_PATTERN

# Keywords used to identify section boundaries in the resume text
EXPERIENCE_KEYWORDS = [
    "experience", "work history", "employment history",
    "professional experience", "work experience", "employment",
    "professional background", "internships", "internship",
    "relevant experience", "career history", "work experiences",
    "industry experience", "experience & internships",
]
EDUCATION_KEYWORDS = [
    "education", "academic profile", "academic background",
    "academic qualifications", "qualifications", "academic credentials",
    "academic history", "education & qualifications", "educational background",
    "academics", "scholastic record",
]
SKILLS_KEYWORDS = [
    "skills", "technical skills", "core competencies",
    "skills & expertise", "skills and technologies", "technologies",
    "technical expertise", "technical proficiencies", "key skills",
    "skill set", "skillset", "areas of expertise", "competencies",
    "technology stack", "tech stack", "tools & technologies",
    "programming skills", "expertise",
]
PROJECTS_KEYWORDS = [
    "projects", "personal projects", "academic projects",
    "side projects", "key projects", "project work",
    "research projects", "major projects", "minor projects",
    "course projects", "capstone projects", "selected projects",
]
# Sections that should be routed to "other" (recognized but not core-parsed).
# Headings in this list stop the skills parser from continuing into non-skill content.
OTHER_SECTION_KEYWORDS = [
    # Standard resume sections
    "certifications", "summary", "objective", "profile", "professional summary",
    "interests", "languages", "publications", "awards",
    "achievements", "hobbies", "extracurricular", "volunteer",
    "volunteer experience", "leadership", "leadership experience",
    "recognition", "honors", "honors & awards", "research",
    "activities", "co-curricular activities", "strengths",
    # Extra headings that must terminate skills parsing
    "organizations", "organization",
    "co-curricular", "extra-curricular", "extra curricular",
    "extracurricular activities", "co-curricular activities",
    "positions of responsibility", "positions",
    "leadership and event organization",
    "achievements & activities", "achievements and activities",
    "references", "reference",
    "contact", "contacts", "contact information", "contact details",
    "personal details", "personal information", "personal",
    "declaration", "signature",
    "accomplishments", "notable achievements",
    "social media", "social profiles", "online profiles",
    "open source", "open source contributions",
    "competitions", "hackathons",
    "sports", "cultural activities",
]

# Section sub-headings that should NOT be treated as skills.
# These are category labels inside a Skills section (e.g. "Languages:", "Tools:").
SKILL_SECTION_HEADINGS = {
    # Layout sub-headings
    "languages", "core subjects", "backend", "frontend", "backend / development",
    "development", "tools", "frameworks", "databases", "devops", "cloud",
    "web technologies", "programming languages", "soft skills", "other",
    "mobile", "testing", "infrastructure",
    "computer organization & architecture (coa)", "computer organization",
    "technology stack", "tech stack",
    # Confusable section names that are NOT real skills
    "achievements", "profiles", "projects", "education", "experience",
    # Additional category labels seen in real resumes
    "core skills", "technical skills", "key skills", "skill set", "skillset",
    "libraries", "libraries & frameworks", "libraries and frameworks",
    "version control", "operating system",
    "build tools", "platforms", "methodologies", "concepts",
    "areas of expertise", "competencies", "tools & technologies",
    "skills & expertise", "programming", "scripting", "markup",
    "design", "networking", "security", "embedded",
    "others", "miscellaneous", "additional",
}

# Sorted longest-first so multi-word headings are matched before shorter substrings
_SORTED_HEADINGS = sorted(SKILL_SECTION_HEADINGS, key=len, reverse=True)

# ─────────────────────────────────────────────────────────────────────────────
# Skills extraction constants
# ─────────────────────────────────────────────────────────────────────────────

# Stop words: tokens that are definitively NOT skills.
# This list is intentionally generous to avoid false positives.
SKILL_STOP_WORDS: frozenset = frozenset({
    # Articles / prepositions / conjunctions
    "a", "an", "the", "and", "or", "but", "nor", "so", "yet",
    "of", "to", "for", "with", "on", "in", "at", "by", "from",
    "about", "above", "after", "along", "also", "as", "into",
    "like", "near", "off", "over", "past", "than", "through",
    "under", "until", "up", "upon", "via", "vs", "while",
    # Common verbs / auxiliaries
    "is", "it", "its", "be", "been", "being", "are", "was", "were",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall",
    "use", "used", "using", "based", "built", "work", "worked",
    "not", "no", "this", "that", "these", "those",
    # Temporal / status words (not skills)
    "present", "current", "now", "till", "until", "ongoing",
    # Role / org / event words
    "student", "representative", "media", "head", "coordinator",
    "club", "organization", "organizations", "leadership", "member",
    "committee", "team", "society", "chapter", "college", "university",
    "department", "course", "semester", "year", "batch",
    "intern", "internship", "associate", "director",
    "manager", "officer", "executive", "secretary", "treasurer",
    "president", "vice", "cultural", "sports", "event", "events",
    "management", "volunteer", "participation", "workshop",
    "training", "seminar", "certification", "certificate",
    "social", "media", "content", "production", "studio",
    # Soft skills / interpersonal traits — never technical skills
    "adaptability", "communication", "leadership", "teamwork",
    "collaboration", "creativity", "initiative", "motivation",
    "responsibility", "accountability", "resilience", "empathy",
    "punctuality", "diligence", "integrity", "dedication",
    "enthusiasm", "confidence", "patience", "flexibility",
    "reliability", "discipline", "professionalism",
    # Generic/ambiguous single words that look like category labels
    "scripting",   # caught as orphan; "Shell Scripting" is protected as phrase
    "thinking",    # from "Critical Thinking" split across columns
    "critical",    # same
    "learning",    # orphan from "Machine Learning" split
    "testing",     # orphan from "Software Testing" split
    "engineering", # orphan from "Software Engineering" split
    "architecture", # orphan from "Computer Organization and Architecture" split
    "time",        # from "Time Management"
    "solving",     # from "Problem-Solving" split
    # Ambiguous single-word orphans from two-column PDF splits.
    # These words only make sense as part of a protected multi-word phrase
    # (e.g. "Shell Scripting", "Machine Learning", "Operating Systems").
    # They are filtered here so that the broken-off half is not emitted alone.
    "shell",        # only meaningful as "Shell Scripting"
    "machine",      # only meaningful as "Machine Learning"
    "os",           # too ambiguous alone ("Operating Systems" is a full phrase)
    "debugging",    # general activity, not a discrete technology
    "problem-solving",  # soft skill / general competency
    # Common noise tokens from PDFs
    "etc", "viz", "eg", "ie", "na", "nil",
})

# Canonical name normalizations applied after extraction.
# Key: lowercase variant seen in resumes → Value: preferred display name.
SKILL_TECH_NORMALIZATIONS: dict = {
    # JavaScript ecosystem
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "react": "React.js",
    "reactjs": "React.js",
    "react.js": "React.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    # Database
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    # Python
    "py": "Python",
    # Cloud
    "gcp": "GCP",
    "aws": "AWS",
    # Version control
    "github": "GitHub",
    "gitlab": "GitLab",
    # DevOps / pipeline
    "ci/cd": "CI/CD",
    "ci / cd": "CI/CD",
    # System abbreviations
    "oops": "OOPS",
    "dbms": "DBMS",
    "dsa": "DSA",
}

# Known multi-word skill phrases that must be kept intact (not split on whitespace).
# Sorted longest-first for greedy left-to-right matching.
MULTI_WORD_SKILL_PHRASES: list = sorted([
    "data structures and algorithms",
    "object-oriented programming",
    "object oriented programming",
    "natural language processing",
    "computer organization and architecture",
    "computer organization & architecture",
    "computer vision",
    "computer networks",
    "operating systems",
    "machine learning",
    "deep learning",
    "software engineering",
    "software testing",
    "shell scripting",
    "shell script",
    "version control",
    "web technologies",
    "data science",
    "artificial intelligence",
    "rest apis",
    "rest api",
    "context api",
    "local storage",
    "scikit-learn",
    "scikit learn",
    "visual studio code",
    "visual studio",
    "android studio",
    "node.js",
    "react.js",
    "express.js",
    "next.js",
    "vue.js",
    "react native",
    "spring boot",
    "tailwind css",
    "ci/cd",
    "ci / cd",
    "test driven development",
    "agile methodology",
    "design patterns",
    "data structures",
], key=len, reverse=True)

# Compiled patterns for multi-word phrase matching (word-boundary anchored)
_MULTI_WORD_PATTERNS: list = [
    (phrase, re.compile(rf'(?i)(?<![\w/])(?:{re.escape(phrase)})(?![\w/])'))
    for phrase in MULTI_WORD_SKILL_PHRASES
]

# Pattern: standalone 4-digit year (1990–2099)
_YEAR_RE = re.compile(r'^(?:19|20)\d{2}$')

# Pattern: a token that contains NO alphanumeric characters at all
_NOISE_TOKEN_RE = re.compile(r'^[^a-zA-Z0-9#+.]+$')

# Date pattern to detect a date range anywhere in a line.
# Matches:
#   - Numeric formats : "01/2026 – Present", "(2022 - 2024)"
#   - Month-name formats: "Jan 2024 – Dec 2024", "January 2024 – Present"
_MONTH_NAMES = (
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
)
DATE_RANGE_PATTERN = re.compile(
    r'(?:\(?)?'
    r'(?:'
    r'(?:\d{1,2}/)?' + r'(?:\d{4})'
    r'|'
    + _MONTH_NAMES + r'\s+\d{4}'
    r')'
    r'\s*(?:[-–]|to)\s*'
    r'(?:Present|Current|Now|(?:\d{1,2}/)?\d{4}|' + _MONTH_NAMES + r'\s+\d{4})'
    r'\s*\)?\s*$',
    re.IGNORECASE
)

# Bullet character pattern
BULLET_PATTERN = re.compile(r'^[•\-*–►▸→]\s*')


# Common technology keywords scanned for anywhere in free text (e.g. project
# description sentences like "Built using React and Flask"). Shared between
# extract_skills() and the Project model's description-based tech extraction.
COMMON_TECH_KEYWORDS = [
    "python", "java", "c\\+\\+", "cpp", "c#", "go", "golang", "rust", "ruby",
    "php", "javascript", "typescript", "html", "css", "sql", "nosql", "mongodb",
    "postgresql", "mysql", "react", "angular", "vue", "node\\.js", "django",
    "flask", "fastapi", "spring", "aws", "azure", "gcp", "docker", "kubernetes",
    "git", "linux", "machine learning", "deep learning", "nlp", "tensorflow",
    "pytorch", "pandas", "numpy", "scikit-learn", "mediapipe", "yolov8", "yolo",
    "llvm", "clang", "opencv", "express\\.js", "express", "slam", "android",
    "openCV", "rest api", "rest apis", "graphql", "redis", "kafka", "spark",
    "hadoop", "firebase", "next\\.js", "redux", "tailwind", "bootstrap",
    "jenkins", "terraform", "ansible", "swift", "kotlin", "r\\b", "scala",
]

_COMMON_TECH_PATTERNS = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in COMMON_TECH_KEYWORDS]


def extract_technologies_from_text(text: str) -> List[str]:
    """Scans free-form text for known technology keywords.

    Used to pull technologies mentioned inside narrative sentences (e.g. project
    bullet points like "Built using React and Flask" or "Implemented with OpenCV
    and Python") rather than only from an explicit comma-separated tech list.

    Args:
        text: Free-form text to scan (e.g. joined project description bullets).

    Returns:
        List[str]: Technology names found, in first-seen order, deduplicated
        case-insensitively.
    """
    if not text:
        return []
    found = []
    seen = set()
    for pattern in _COMMON_TECH_PATTERNS:
        for match in pattern.finditer(text):
            matched_text = match.group(0)
            key = matched_text.lower()
            if key not in seen:
                seen.add(key)
                found.append(matched_text)
    return found


class ResumeExtractor:
    """Extractor class for parsing candidate information from raw resume text."""

    @staticmethod
    def _preprocess_text(text: str) -> str:
        """Cleans up common PDF text extraction artifacts.

        Fixes:
        - Spaces inserted before '@' in email addresses (e.g. "user @gmail.com")
        - Removes zero-width spaces and other unicode artifacts

        Args:
            text (str): The raw extracted text.

        Returns:
            str: The cleaned text.
        """
        # Fix spaces before '@' in emails (common pdfplumber artifact)
        text = re.sub(r'(\S)\s+@\s*(\S)', r'\1@\2', text)
        # Remove zero-width spaces
        text = text.replace('\u200b', '').replace('\ufeff', '')
        return text

    @staticmethod
    def _fuzzy_section_match(check_line: str):
        """Loosely matches a heading-like line against known section keywords.

        Used as a fallback when a heading line doesn't exactly match the curated
        keyword lists (e.g. "Work Experience & Internships", "Technical Skill Set",
        "Academic Projects & Research"). Only fires for short, heading-shaped lines.

        Args:
            check_line: Lowercased, punctuation-trimmed candidate heading line.

        Returns:
            One of "experience", "education", "skills", "projects", "other", or
            None if no confident match is found.
        """
        if not check_line or len(check_line.split()) > 7:
            return None

        # Token-overlap based matching: a line matches a section if it contains
        # one of that section's signal words as a whole word.
        def _has_word(words, line):
            return any(re.search(rf'(?<!\w){re.escape(w)}(?!\w)', line) for w in words)

        if _has_word(["experience", "internship", "employment"], check_line):
            return "experience"
        # Check "project" before "research" so that "Research Projects" routes
        # to "projects" rather than being swallowed by the "other" bucket.
        if _has_word(["project", "projects"], check_line):
            return "projects"
        if _has_word(["skill", "skills", "competenc", "expertise", "proficienc", "stack"], check_line):
            return "skills"
        if _has_word(["education", "academic", "academics", "qualification", "scholastic"], check_line):
            return "education"
        # "research" is listed here only as a catch-all for "Research" sections
        # that do NOT also contain a project signal word (handled above).
        if _has_word([
            "certification", "summary", "objective", "profile", "interest",
            "language", "publication", "award", "achievement", "hobbies",
            "extracurricular", "volunteer", "leadership", "honor", "research",
            "activit", "strength"
        ], check_line):
            return "other"
        return None

    @classmethod
    def extract_sections(cls, text: str) -> Dict[str, List[str]]:
        """Splits the raw text into logical sections based on keyword headers.

        Args:
            text (str): The full raw text of the resume.

        Returns:
            Dict[str, List[str]]: A dictionary mapping section names to their lines of text.
        """
        sections = {
            "header": [],
            "experience": [],
            "education": [],
            "skills": [],
            "projects": []
        }

        current_section = "header"
        lines = text.split('\n')

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            # Clean punctuation / decorators for matching headers.
            # Strip leading '#' (Markdown), leading emoji characters, and
            # trailing ':' so headings like "🛠️ Skills" or "## Experience:"
            # are matched correctly.
            check_line = cleaned.lower().lstrip('#').strip().rstrip(':').strip()
            # Strip leading emoji / non-ASCII decorators (e.g. "🛠️ Skills" → "skills")
            check_line = re.sub(r'^[^\x00-\x7F\w]+', '', check_line).strip()

            if check_line in EXPERIENCE_KEYWORDS:
                current_section = "experience"
                continue
            elif check_line in EDUCATION_KEYWORDS:
                current_section = "education"
                continue
            elif check_line in SKILLS_KEYWORDS:
                current_section = "skills"
                continue
            elif check_line in PROJECTS_KEYWORDS:
                current_section = "projects"
                continue
            elif current_section == "skills" and check_line in SKILL_SECTION_HEADINGS:
                # Sub-headings inside the Skills section (e.g. "Languages", "Core Subjects",
                # "Backend / Development") are labels, not new top-level resume sections.
                # Stay in "skills" so the technologies listed beneath them are still captured.
                continue
            elif len(check_line) < 40 and check_line in OTHER_SECTION_KEYWORDS:
                # We skip non-core sections, routing their lines to "other"
                current_section = "other"
                continue
            elif (
                len(check_line) < 40
                and len(check_line.split()) <= 4
                and not BULLET_PATTERN.match(cleaned)
                and ',' not in check_line
                and not check_line.endswith('.')
                and cls._fuzzy_section_match(check_line) is not None
            ):
                # Fallback: heading-shaped line (short, no bullet, no trailing
                # punctuation/commas typical of body text) that loosely matches a
                # known section name (e.g. "Work Experience & Internships",
                # "Technical Skill Set") but didn't hit an exact keyword above.
                current_section = cls._fuzzy_section_match(check_line)
                continue

            if current_section in sections:
                sections[current_section].append(cleaned)

        return sections

    @staticmethod
    def _is_bullet_line(line: str) -> bool:
        """Returns True if the line starts with a bullet character."""
        return bool(BULLET_PATTERN.match(line.strip()))

    @staticmethod
    def _strip_bullet(line: str) -> str:
        """Strips leading bullet characters from a line."""
        return BULLET_PATTERN.sub('', line.strip()).strip()

    @staticmethod
    def _split_inline_bullets(line: str) -> List[str]:
        """Splits a line that has embedded mid-sentence bullet '•' characters.

        pdfplumber sometimes concatenates adjacent lines into one string, with
        bullet characters embedded mid-line, e.g.:
            "Built system. •Implemented feature. •Integrated component."

        Only splits on '•' (the true list bullet), NOT on arrows like '→' which
        are used as flow arrows in descriptions (e.g. "Request → Accept → Start").

        Args:
            line: Raw line from the PDF.

        Returns:
            List of clean sub-strings (one per bullet fragment).
        """
        # Only split on inline '•' characters
        parts = re.split(r'(?<!\A)\s*•\s*', line)
        result = []
        for part in parts:
            cleaned = part.strip().lstrip('•').strip()
            if cleaned:
                result.append(cleaned)
        return result if result else [line.strip()]


    @staticmethod
    def _is_continuation_line(line: str) -> bool:
        """Heuristic: returns True if line is a continuation of the previous sentence.

        A continuation line:
        - Does NOT end with a date range
        - Does NOT look like a new entry header (short standalone title-case line)
        - Starts with lowercase OR starts with a bullet
        """
        stripped = line.strip()
        if not stripped:
            return False
        # Lines starting with bullets are always content, not headers
        if BULLET_PATTERN.match(stripped):
            return True
        # Lines that start with lowercase are continuations
        if stripped[0].islower():
            return True
        return False

    @classmethod
    def _group_experience_entries(cls, lines: List[str]) -> List[Dict]:
        """Groups raw experience section lines into structured entry dicts.

        A new entry starts when a line:
        - Contains a date range (e.g. "Title, Company 01/2026 – Present")
        - OR looks like a standalone role header (short line, no bullet, ends with date or comma)

        All subsequent bullet/continuation lines belong to that entry's description.

        Args:
            lines: Raw lines from the experience section.

        Returns:
            List of dicts with keys: header, description, raw_lines
        """
        if not lines:
            return []

        entries = []
        current_header = None
        current_desc = []
        current_raw = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped in ['•', '-', '*', '–', '►', '▸']:
                continue

            is_date_header = bool(DATE_RANGE_PATTERN.search(stripped))
            is_bullet = cls._is_bullet_line(stripped)

            if is_date_header and not is_bullet:
                # Save previous entry
                if current_header is not None:
                    entries.append({
                        "header": current_header,
                        "description": current_desc,
                        "raw_lines": current_raw
                    })
                current_header = stripped
                current_desc = []
                current_raw = [stripped]
            elif is_bullet:
                # It's a description bullet
                clean_bullet = cls._strip_bullet(stripped)
                if clean_bullet:
                    if current_header is None:
                        # Orphan bullet — start an implicit entry
                        current_header = ""
                        current_raw = []
                    current_desc.append(clean_bullet)
                    current_raw.append(stripped)
            else:
                # Non-bullet, non-date-header line
                if current_header is not None:
                    # ── Wrapped-line merging ──────────────────────────────────
                    # pdfplumber sometimes wraps long lines. A line is a
                    # continuation of the previous description item (not a new
                    # standalone bullet) when ALL of the following are true:
                    #   1. It starts with a lowercase letter.
                    #   2. There is already at least one description item.
                    #   3. The previous item did NOT end with sentence-terminal
                    #      punctuation (., !, ?, :), which would mean the
                    #      previous sentence was already complete.
                    if (
                        stripped
                        and stripped[0].islower()
                        and current_desc
                        and not current_desc[-1].rstrip().endswith(('.', '!', '?', ':'))
                    ):
                        # Merge continuation text onto the previous item
                        current_desc[-1] = current_desc[-1].rstrip() + ' ' + stripped
                        current_raw.append(stripped)
                    else:
                        # Treat as a new description line (sub-header or detail)
                        current_desc.append(stripped)
                        current_raw.append(stripped)
                else:
                    # Start a new entry with this as the header
                    current_header = stripped
                    current_desc = []
                    current_raw = [stripped]

        if current_header is not None:
            entries.append({
                "header": current_header,
                "description": current_desc,
                "raw_lines": current_raw
            })

        return entries

    @classmethod
    def _group_project_entries(cls, lines: List[str]) -> List[Dict]:
        """Groups raw project section lines into structured entry dicts.

        Projects often have NO date range on the header line. A new project starts when:
        - A short non-bullet line appears that is NOT a pure continuation
        - OR a line has a date range

        Bullet lines and continuation lines belong to the current project's description.
        The second line after a project header (if short and comma-separated) is treated
        as the technology stack.

        Args:
            lines: Raw lines from the projects section.

        Returns:
            List of dicts with keys: header, tech_line, description, raw_lines
        """
        if not lines:
            return []

        entries = []
        current_header = None
        current_tech_line = None
        current_desc = []
        current_raw = []
        awaiting_tech = False  # True right after a header is set

        # Action verbs commonly used to start a description bullet/sentence
        # (past tense or gerund) — used to distinguish a project HEADING
        # (a short title, e.g. "Portfolio Website") from a project DESCRIPTION
        # line (e.g. "Designed and deployed a personal portfolio site.").
        _DESC_VERBS = {
            "built", "developed", "designed", "implemented", "created",
            "worked", "led", "managed", "architected", "engineered",
            "integrated", "deployed", "wrote", "optimized", "improved",
            "added", "fixed", "collaborated", "contributed", "achieved",
            "automated", "reduced", "increased", "handled", "maintained",
            "tested", "launched", "founded", "initiated", "developed,",
            "responsible", "involved", "utilized", "used", "leveraged",
        }

        def _looks_like_description_sentence(line: str) -> bool:
            """Heuristic: True if the line reads like prose (a description),
            not a short heading/title.

            Signals:
            - Ends with sentence-terminal punctuation
            - Is long (6+ words) — titles are almost always short
            - Starts with a common past-tense/gerund action verb
            """
            s = line.strip()
            if not s:
                return False
            if s.endswith(('.', ';')):
                return True
            words = s.split()
            if len(words) >= 6:
                return True
            first_word = re.sub(r'[^A-Za-z]', '', words[0]).lower() if words else ''
            if first_word in _DESC_VERBS:
                return True
            return False

        def _looks_like_duration_line(line: str) -> bool:
            """A standalone parenthesized duration, e.g. '(Jan 2024 - Mar 2024)'."""
            s = line.strip()
            return bool(re.match(r'^\(.{2,40}\)$', s))

        def _looks_like_project_header(line: str) -> bool:
            """A project header is a short standalone line without a leading bullet.

            Heuristics:
            - No bullet prefix
            - Relatively short (< 120 chars)
            - Does not start with a lowercase letter (which would indicate continuation)
            - Not purely a percentage/CGPA/grade line
            - Does not read like a description sentence (see _looks_like_description_sentence)
            """
            s = line.strip()
            if not s:
                return False
            if BULLET_PATTERN.match(s):
                return False
            if s[0].islower():
                return False
            if not (s[0].isalnum()):
                return False
            if re.match(r'^(CGPA|Percentage|Grade|GPA)\s*:', s, re.IGNORECASE):
                return False
            if _looks_like_description_sentence(s):
                return False
            return len(s) < 120

        def _looks_like_tech_line(line: str) -> bool:
            """A technology line is comma-separated with mostly short tokens."""
            s = line.strip()
            if BULLET_PATTERN.match(s):
                return False
            tokens = [t.strip() for t in s.split(',')]
            if len(tokens) < 2:
                return False
            avg_len = sum(len(t) for t in tokens) / len(tokens)
            return avg_len < 20

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped in ['•', '-', '*', '–', '►', '▸']:
                continue

            is_bullet = cls._is_bullet_line(stripped)

            # Parenthesized standalone duration line (e.g. '(Jan 2024 - Mar 2024)')
            # must be handled BEFORE the date-range guard so it is folded into the
            # current header rather than being mistaken for a new entry header.
            if _looks_like_duration_line(stripped) and current_header is not None and not current_desc:
                current_header = current_header.rstrip() + ' ' + stripped
                current_raw.append(stripped)
                # Still may be followed by a tech line
                continue

            is_date_header = bool(DATE_RANGE_PATTERN.search(stripped)) and not is_bullet

            # Case 1: Line with explicit date range → always a new entry header
            if is_date_header:
                if current_header is not None:
                    entries.append({
                        "header": current_header,
                        "tech_line": current_tech_line,
                        "description": current_desc,
                        "raw_lines": current_raw
                    })
                current_header = stripped
                current_tech_line = None
                current_desc = []
                current_raw = [stripped]
                awaiting_tech = True


            # Case 2: Bullet line → description content
            elif is_bullet:
                clean_bullet = cls._strip_bullet(stripped)
                if clean_bullet:
                    if current_header is None:
                        current_header = ""
                        current_raw = []
                    # Split inline bullets (pdfplumber may merge multiple bullets into one line)
                    sub_bullets = cls._split_inline_bullets(clean_bullet)
                    current_desc.extend(sub_bullets)
                    current_raw.append(stripped)
                    awaiting_tech = False

            # Case 3: Non-bullet, non-date line
            else:
                # Could be: project header, tech line, duration line, or description
                if current_header is None:
                    # Start fresh entry
                    current_header = stripped
                    current_tech_line = None
                    current_desc = []
                    current_raw = [stripped]
                    awaiting_tech = True
                elif _looks_like_duration_line(stripped) and not current_desc:
                    # A standalone "(Jan 2024 - Mar 2024)" style line right after the
                    # project title is metadata, not a new project or a description
                    # bullet — fold it into the header.
                    current_header = current_header.rstrip() + ' ' + stripped
                    current_raw.append(stripped)
                    # Still may be followed by a tech line
                elif awaiting_tech and _looks_like_tech_line(stripped):
                    # Second line after header — treat as technology stack
                    current_tech_line = stripped
                    current_raw.append(stripped)
                    awaiting_tech = False
                elif _looks_like_description_sentence(stripped):
                    # Reads like prose, not a title — always belongs to the
                    # current project's description, regardless of whether any
                    # bullets/tech-line have been seen yet (Style A support).
                    sub_bullets = cls._split_inline_bullets(stripped)
                    current_desc.extend(sub_bullets)
                    current_raw.append(stripped)
                    awaiting_tech = False
                elif _looks_like_project_header(stripped) and (current_desc or current_tech_line or not awaiting_tech):
                    # A genuine new project heading: only split here once the
                    # current entry already has *some* content (a tech line or
                    # description), so we don't mistake a project's subtitle/
                    # second header line for a brand new project.
                    entries.append({
                        "header": current_header,
                        "tech_line": current_tech_line,
                        "description": current_desc,
                        "raw_lines": current_raw
                    })
                    current_header = stripped
                    current_tech_line = None
                    current_desc = []
                    current_raw = [stripped]
                    awaiting_tech = True
                else:
                    # Continuation description text (no bullet, not a new header)
                    # Still may have embedded bullets from PDF layout
                    sub_bullets = cls._split_inline_bullets(stripped)
                    current_desc.extend(sub_bullets)
                    current_raw.append(stripped)
                    awaiting_tech = False

        if current_header is not None:
            entries.append({
                "header": current_header,
                "tech_line": current_tech_line,
                "description": current_desc,
                "raw_lines": current_raw
            })

        return entries

    @classmethod
    def _group_education_entries(cls, lines: List[str]) -> List[Dict]:
        """Groups raw education section lines into structured entry dicts.

        Education entries can span multiple lines:
        - "B.E., Information Science & Engineering, 2023 – 2027"  (may have date inline)
        - "B.M.S. College of Engineering (BMSCE)"                (school on next line)
        - "CGPA: 7.04/ 10"
        - "12th, Sir mv pu college 2023"                         (single-year entry)
        - "Percentage:96"
        - "2021"                                                  (year continuation)

        A new entry starts when a line unambiguously looks like a degree/class header.

        Args:
            lines: Raw lines from the education section.

        Returns:
            List of dicts with keys: header, school_line, meta_lines, description, raw_lines
        """
        if not lines:
            return []

        entries = []
        current_header = None
        current_school = None
        current_meta = []   # CGPA, Percentage, Grade lines
        current_desc = []   # other description lines
        current_raw = []

        # Patterns for metadata lines
        # CGPA_PAT: matches both "CGPA: 7.04" and "CGPA 9.16" (no colon variant)
        CGPA_PAT   = re.compile(r'(cgpa|gpa)\s*[:.]?\s*\d', re.IGNORECASE)
        PCT_PAT    = re.compile(r'percentage\s*:', re.IGNORECASE)
        GRADE_PAT  = re.compile(r'grade\s*:', re.IGNORECASE)
        # Additional formats: "Score: 8.2/10", "Marks: 456/500", standalone "88.5%"
        SCORE_PAT  = re.compile(r'(score|marks)\s*:', re.IGNORECASE)
        INLINE_PCT = re.compile(r'^\s*\d+(?:\.\d+)?\s*%\s*$')  # lone percentage line
        YEAR_PAT   = re.compile(r'\b(19|20)\d{2}\b')
        STANDALONE_YEAR_PAT = re.compile(r'^\s*(19|20)\d{2}\s*$')

        def _is_meta_line(s: str) -> bool:
            return bool(
                CGPA_PAT.search(s) or PCT_PAT.search(s) or
                GRADE_PAT.search(s) or SCORE_PAT.search(s) or
                INLINE_PCT.match(s)
            )

        # Tighter degree pattern — must match at start-of-string or after comma/space
        # so that "B.M.S." does NOT match (it requires the full abbreviated form).
        DEGREE_PAT = re.compile(
            r'(?:^|,\s*|\s)'
            r'(B\.E\b|B\.Tech\b|M\.Tech\b|M\.E\b|M\.S\b|B\.S\b|MBA\b|Ph\.D\b|'
            r'BCA\b|MCA\b|B\.Sc\b|M\.Sc\b|BE\b|BTech\b|MTech\b|BBA\b|'
            r'Class\s+X(?:II)?\b|10th\b|12th\b|Diploma\b|'
            r'SSC\b|HSC\b|SSLC\b|Matriculation\b|'
            r'Secondary\s+School\b|Higher\s+Secondary\b|High\s+School\b|'
            r'Bachelor(?:\'s)?\b|Master(?:\'s)?\b)',
            re.IGNORECASE
        )

        def _looks_like_school_name(s: str) -> bool:
            """Heuristic: line has a school/college/university keyword.
            Also catches explicit 'School: ...' label-style lines.
            """
            if BULLET_PATTERN.match(s):
                return False
            if _is_meta_line(s):
                return False
            # 'School: XYZ' label — treat value part as school name
            school_label_m = re.match(r'^school\s*:\s*(.+)', s, re.IGNORECASE)
            if school_label_m:
                return True
            if s[0].islower():
                return False
            return bool(re.search(
                r'\b(college|university|school|institute|pu\s+college|institution|academy)\b',
                s, re.IGNORECASE
            ))

        def _looks_like_edu_header(s: str) -> bool:
            """A degree/class header has a recognizable degree keyword or a year.
            Degree keyword takes priority over school-name classification.
            Only pure school-name lines (no degree keyword) are excluded.
            """
            if BULLET_PATTERN.match(s):
                return False
            if _is_meta_line(s):
                return False
            # 'School: ...' label lines are never degree headers
            if re.match(r'^school\s*:', s, re.IGNORECASE):
                return False
            if s[0].islower():
                return False
            if STANDALONE_YEAR_PAT.match(s):
                return False
            has_degree = bool(DEGREE_PAT.search(s))
            # Degree keyword always wins — even if line also has a school keyword
            if has_degree:
                return True
            has_year = bool(YEAR_PAT.search(s))
            # Year-only line: only a header if it doesn't look like a pure school name
            if has_year and not _looks_like_school_name(s):
                return True
            return False



        def _save_current():
            if current_header is not None:
                entries.append({
                    "header": current_header,
                    "school_line": current_school,
                    "meta_lines": list(current_meta),
                    "description": list(current_desc),
                    "raw_lines": list(current_raw)
                })

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped in ['•', '-', '*', '–']:
                continue

            is_bullet = cls._is_bullet_line(stripped)

            # Bullets -> description content
            if is_bullet:
                if current_header is not None:
                    current_desc.append(cls._strip_bullet(stripped))
                    current_raw.append(stripped)
                continue

            # Meta lines (CGPA, Percentage, Grade, Score, Marks, standalone %)
            if _is_meta_line(stripped):
                if current_header is not None:
                    current_meta.append(stripped)
                    current_raw.append(stripped)
                # If no entry has started yet, silently skip (orphan meta before any degree).
                continue

            # Standalone year -> append to previous header as end_date continuation
            if STANDALONE_YEAR_PAT.match(stripped):
                if current_header is not None:
                    current_header = current_header.rstrip() + ' ' + stripped.strip()
                    current_raw.append(stripped)
                continue

            # Degree header line -> starts a new education entry
            # (checked BEFORE school_name so '12th, Sir mv pu college 2023' becomes a new entry)
            if _looks_like_edu_header(stripped):
                _save_current()
                current_header = stripped
                current_school = None
                current_meta = []
                current_desc = []
                current_raw = [stripped]
                continue

            # School name line -> group under current entry as school_line
            if (current_header is not None
                    and current_school is None
                    and _looks_like_school_name(stripped)):
                # For 'School: XYZ' labels, strip the prefix
                label_m = re.match(r'^school\s*:\s*(.+)', stripped, re.IGNORECASE)
                current_school = label_m.group(1).strip() if label_m else stripped
                current_raw.append(stripped)
                continue

            # Anything else: description or orphan
            if current_header is not None:
                current_desc.append(stripped)
                current_raw.append(stripped)
            else:
                current_header = stripped
                current_school = None
                current_meta = []
                current_desc = []
                current_raw = [stripped]

        _save_current()
        return entries

    @classmethod
    def extract_name(cls, text: str, sections: Dict[str, List[str]]) -> str:
        """Heuristic to extract candidate name (usually at the very top).

        Args:
            text (str): Full text of the resume.
            sections (Dict[str, List[str]]): The split sections of the resume.

        Returns:
            str: The extracted name, or empty string.
        """
        header_lines = sections.get("header", [])
        for line in header_lines:
            cleaned = line.strip()
            if len(cleaned) < 3:
                continue
            # Ignore lines containing typical contact info
            if "@" in cleaned or "http" in cleaned or "www." in cleaned:
                continue
            # Ignore lines with excessive numbers (dates, zip codes, phone numbers)
            if sum(c.isdigit() for c in cleaned) > 2:
                continue
            return cleaned

        # Fallback to the first non-empty line of the file
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines[:5]:
            if "@" not in line and "http" not in line and sum(c.isdigit() for c in line) <= 2 and len(line) >= 3:
                return line

        return ""

    @classmethod
    def extract_emails(cls, text: str) -> List[str]:
        """Extracts all email addresses found in the text.

        Pre-processes text to fix PDF artifacts before running regex.

        Args:
            text (str): Full text.

        Returns:
            List[str]: Found email addresses with spaces removed.
        """
        cleaned_text = cls._preprocess_text(text)
        emails = EMAIL_PATTERN.findall(cleaned_text)
        return [e.replace(' ', '') for e in emails]

    @classmethod
    def extract_phones(cls, text: str) -> List[str]:
        """Extracts all phone numbers found in the text.

        Args:
            text (str): Full text.

        Returns:
            List[str]: Found phone numbers.
        """
        return PHONE_PATTERN.findall(text)

    @classmethod
    def _is_section_heading(cls, text: str) -> bool:
        """Checks if a text fragment is a section sub-heading rather than an actual skill."""
        return text.lower().strip() in SKILL_SECTION_HEADINGS

    @classmethod
    def _strip_embedded_headings(cls, text: str) -> str:
        """Removes known section heading phrases embedded inside a line of text."""
        cleaned = text
        for heading in _SORTED_HEADINGS:
            pattern = re.compile(rf'(?<!\w){re.escape(heading)}(?!\w)', re.IGNORECASE)
            cleaned = pattern.sub(' ', cleaned)
        return re.sub(r'\s+', ' ', cleaned).strip()

    @classmethod
    def _split_glued_tokens(cls, token: str) -> List[str]:
        """Splits glued tokens like 'JavaScript DSA' into ['JavaScript', 'DSA'].

        Some PDFs merge adjacent items that should be separate skills.
        This splits on whitespace, but preserves known multi-word skill phrases.

        Args:
            token: A single skill candidate string.

        Returns:
            List of split skill strings.
        """
        # Multi-word skill phrases that must be kept together
        protected_phrases = {
            "javascript", "typescript", "postgresql", "mongodb",
            "tensorflow", "pytorch", "scikit", "opencv", "mediapipe",
            "yolov8", "yolo", "llvm", "clang", "github", "gitlab",
            # multi-word phrases
            "web technologies", "shell scripting", "machine learning",
            "deep learning", "natural language processing",
            "computer vision", "data science", "rest api", "rest apis",
            "operating systems", "computer networks", "data structures",
            "object oriented", "object-oriented", "shell script",
            "visual studio", "node.js", "express.js", "react.js",
        }
        lower = token.lower().strip()
        if lower in protected_phrases:
            return [token]

        # If token is a single word, return as-is
        words = token.split()
        if len(words) == 1:
            return [token]

        # Two-word phrases: split only if it looks like two concatenated skills
        # (i.e. both words are meaningful non-heading standalone skills)
        if len(words) >= 2:
            result = []
            for word in words:
                w = word.strip().rstrip('.')
                if w and not cls._is_section_heading(w):
                    result.append(w)
            return result if result else [token]

        return [token]


    @classmethod
    def _is_noise_token(cls, token: str) -> bool:
        """Returns True when a token is definitively not a skill.

        Filters applied (in order):
        1. Empty or whitespace-only string.
        2. Pure symbol / punctuation (no alphanumeric characters).
        3. Standalone 4-digit year (1990-2099).
        4. Temporal status words (Present, Current, Now).
        5. Single-character tokens that are not known single-letter languages (C, R).
        6. Stop words.
        7. Known section sub-heading labels.

        Args:
            token: A stripped candidate skill string.

        Returns:
            bool: True if the token should be discarded.
        """
        t = token.strip()
        if not t:
            return True
        # Pure punctuation / symbols (e.g. "•", "&", ":", "–")
        if _NOISE_TOKEN_RE.match(t):
            return True
        # 4-digit year
        if _YEAR_RE.match(t):
            return True
        # Temporal words
        if t.lower() in {"present", "current", "now"}:
            return True
        # Single characters that are not language abbreviations
        if len(t) == 1 and t not in {"C", "R", "c", "r"}:
            return True
        # Stop words (case-insensitive)
        if t.lower() in SKILL_STOP_WORDS:
            return True
        # Known section sub-heading labels
        if cls._is_section_heading(t):
            return True
        return False

    @classmethod
    def _normalize_skill(cls, skill: str) -> str:
        """Applies canonical technology name normalizations.

        Examples:
            react     → React.js
            node      → Node.js
            js        → JavaScript
            mongo     → MongoDB
            postgres  → PostgreSQL

        Normalizations only apply when the entire token matches a known alias
        (case-insensitive exact match). Unknown tokens are returned unchanged.

        Args:
            skill: A single stripped skill string.

        Returns:
            str: The normalized skill name.
        """
        key = skill.strip().lower()
        return SKILL_TECH_NORMALIZATIONS.get(key, skill.strip())

    @classmethod
    def extract_skills(cls, text: str, sections: Dict[str, List[str]]) -> List[str]:
        """Extracts genuine technical skills from the skills section.

        Design principles
        -----------------
        * **Section-strict**: only lines captured inside the ``sections["skills"]``
          bucket are processed. The full resume text is NOT scanned, eliminating
          cross-section contamination from Experience, Projects, Organizations, etc.
        * **Multi-word first**: known multi-word phrases (e.g. "Data Structures and
          Algorithms", "Machine Learning") are extracted greedily before splitting
          by delimiter so they are never broken apart.
        * **Noise-free**: years, standalone symbols, stop words, and category
          sub-headings are discarded via ``_is_noise_token``.
        * **Normalised**: tech aliases are collapsed to canonical names
          (e.g. "react" → "React.js") via ``_normalize_skill``.
        * **Deduped**: case-insensitive deduplication preserving first-seen order.
        * **Order-preserving**: skills are returned in the order they appear.

        Args:
            text (str): Full resume text (kept for API compatibility; not scanned).
            sections (Dict[str, List[str]]): Resume sections from extract_sections().

        Returns:
            List[str]: Ordered, deduplicated list of genuine technical skills.
        """
        skills: List[str] = []
        # Lowercase keys for case-insensitive deduplication
        seen: set = set()

        def _add(raw: str) -> None:
            """Normalize, validate, and add a skill if it passes all filters."""
            s = raw.strip().rstrip('.,;').strip()
            if not s:
                return
            if cls._is_noise_token(s):
                return
            normalized = cls._normalize_skill(s)
            key = normalized.lower()
            if key not in seen:
                seen.add(key)
                skills.append(normalized)

        skills_lines = sections.get("skills", [])

        # ── Cross-line stitching for two-column PDF layouts ────────────────────
        # pdfplumber reads two-column resumes left-to-right across columns, which
        # causes multi-word skill phrases to be split across adjacent lines
        # (e.g. "Shell" ends line N, "Scripting" starts line N+1 after the right
        # column's content in between).  By joining all skills-section lines with
        # a comma separator before processing, we give the multi-word phrase
        # detector a chance to see "Shell Scripting" as a contiguous span.
        #
        # The joined blob is then processed as a single virtual line, applying
        # heading-skip, colon-split, phrase-match, and token-filter in one pass.
        if not skills_lines:
            return skills

        # Build one joined line: strip bullets, join with ", "
        cleaned_lines = []
        for raw_line in skills_lines:
            stripped = re.sub(
                r'^[\u2022\u25cf\u25cb\u25aa\u2219\u00b7\-\*\u2013\u2014\u25b8\u25ba]+\s*',
                '', raw_line.strip()
            ).strip()
            # Skip entire-line section boundaries
            if not stripped:
                continue
            check = stripped.lower().rstrip(':').strip()
            if check in OTHER_SECTION_KEYWORDS:
                break  # hard stop: rest of content is a different section
            # Skip pure heading lines so their text doesn't end up in the blob
            if cls._is_section_heading(stripped):
                continue
            cleaned_lines.append(stripped)

        # ── Single-pass processing of the joined blob ─────────────────────────
        # We treat the entire joined text as one "line" and reuse the same
        # phrase-extract → split → filter pipeline.
        #
        # IMPORTANT: multi-word phrase matching runs BEFORE _strip_embedded_headings
        # because some phrases (e.g. "Software Testing", "Computer Networks") contain
        # words that are also heading labels ("testing", "networking").  Stripping
        # headings first would break those phrases.

        joined = ", ".join(cleaned_lines)

        # Replace " : " style column-separator artifacts with comma
        joined = re.sub(r'\s*:\s*', ', ', joined)

        # ── Single-pass processing of the joined blob ─────────────────────────
        # We treat the entire joined text as one "line" and reuse the same
        # phrase-extract → split → filter pipeline.


        # ── Multi-word phrase extraction (greedy, longest-first) ──────────────
        # Scan the joined blob for known multi-word phrases first.
        # Replace each match with a placeholder so commas inside the phrase
        # survive the subsequent split.
        working = joined
        phrase_slots: list = []  # [(placeholder, display_name), ...]

        for phrase, pattern in _MULTI_WORD_PATTERNS:
            m = pattern.search(working)
            if m:
                # Canonical display name
                display = SKILL_TECH_NORMALIZATIONS.get(
                    phrase.lower(),
                    ' '.join(
                        w.capitalize() if w not in ('and', 'of', 'the', '&')
                        else w
                        for w in phrase.split()
                    )
                )
                placeholder = f"__PHRASE_{len(phrase_slots)}__"
                phrase_slots.append((placeholder, display))
                working = working[:m.start()] + placeholder + working[m.end():]

        # ── Split remaining blob by comma and semicolon ────────────────────────
        for raw_token in re.split(r'[,;]', working):
            raw_token = raw_token.strip()
            if not raw_token:
                continue

            # Resolve phrase placeholders
            resolved = False
            for placeholder, display in phrase_slots:
                if placeholder in raw_token:
                    _add(display)
                    resolved = True
                    break

            if resolved:
                continue

            # No placeholder — split remaining token on whitespace
            # (handles space-separated skill lists like "Python Java C++")
            for sub in cls._split_glued_tokens(raw_token):
                _add(sub)

        return skills


    @classmethod
    def extract_experience(cls, sections: Dict[str, List[str]]) -> List[Dict]:
        """Extracts and groups experience entries into structured dicts.

        Args:
            sections (Dict[str, List[str]]): The parsed sections.

        Returns:
            List[Dict]: Structured experience entry dicts.
        """
        raw_lines = sections.get("experience", [])
        return cls._group_experience_entries(raw_lines)

    @classmethod
    def extract_education(cls, sections: Dict[str, List[str]]) -> List[Dict]:
        """Extracts and groups education entries into structured dicts.

        Args:
            sections (Dict[str, List[str]]): The parsed sections.

        Returns:
            List[Dict]: Structured education entry dicts.
        """
        raw_lines = sections.get("education", [])
        return cls._group_education_entries(raw_lines)

    @classmethod
    def extract_projects(cls, sections: Dict[str, List[str]]) -> List[Dict]:
        """Extracts and groups project entries into structured dicts.

        Args:
            sections (Dict[str, List[str]]): The parsed sections.

        Returns:
            List[Dict]: Structured project entry dicts.
        """
        raw_lines = sections.get("projects", [])
        return cls._group_project_entries(raw_lines)
