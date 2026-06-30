from dataclasses import dataclass, field
import re
from typing import List

@dataclass
class Project:
    """Dataclass representing a candidate's project.

    Fields
    ------
    raw_text        : Original joined text for traceability.
    project_name    : Title of the project.
    technology_stack: List of technologies used.
    description     : List of bullet-point strings describing the project.
    start_date      : Start date string.
    end_date        : End date string.
    github          : GitHub URL if present.
    demo            : Demo URL if present.
    """
    raw_text: str
    project_name: str = ""
    technology_stack: List[str] = field(default_factory=list)
    description: List[str] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    github: str = ""
    demo: str = ""

    # backward-compat alias
    @property
    def technologies(self) -> List[str]:
        return self.technology_stack

    @classmethod
    def from_dict(cls, entry: dict) -> 'Project':
        """Build a Project from a structured dict produced by ResumeExtractor.

        The dict has keys: header, tech_line, description, raw_lines.

        Args:
            entry: Dict with keys 'header', 'tech_line', 'description', 'raw_lines'.

        Returns:
            Project: Fully populated Project object.
        """
        header = entry.get("header", "")
        tech_line = entry.get("tech_line") or ""
        description = entry.get("description", [])
        raw_text = "\n".join(entry.get("raw_lines", [header]))

        project_name, technology_stack, start_date, end_date, github, demo = cls._parse_header(
            header, tech_line
        )

        # Also infer technologies mentioned in narrative description bullets
        # (e.g. "Built using React and Flask") that weren't already captured
        # from an explicit header/tech-line list.
        if description:
            try:
                from extractors.resume_extractor import extract_technologies_from_text
                desc_text = " ".join(description)
                inferred = extract_technologies_from_text(desc_text)
                seen = {t.lower() for t in technology_stack}
                for tech in inferred:
                    if tech.lower() not in seen:
                        seen.add(tech.lower())
                        technology_stack.append(tech)
            except ImportError:
                pass

        return cls(
            raw_text=raw_text,
            project_name=project_name,
            technology_stack=technology_stack,
            description=description,
            start_date=start_date,
            end_date=end_date,
            github=github,
            demo=demo,
        )

    @classmethod
    def from_raw_text(cls, text: str) -> 'Project':
        """Backward-compatible factory: parse from a raw text string.

        Accepts both plain strings and ' | '-separated grouped entries.

        Args:
            text: Raw project text.

        Returns:
            Project: Populated Project object.
        """
        if not text:
            return cls("")

        if isinstance(text, dict):
            return cls.from_dict(text)

        parts = [p.strip() for p in text.split(' | ')]
        header = parts[0]
        remaining = parts[1:] if len(parts) > 1 else []

        tech_line = ""
        description = []
        for part in remaining:
            tokens = [t.strip() for t in part.split(',')]
            avg_len = sum(len(t) for t in tokens) / max(len(tokens), 1)
            if len(tokens) >= 2 and avg_len < 25:
                tech_line = part
            else:
                description.append(part)

        entry = {
            "header": header,
            "tech_line": tech_line,
            "description": description,
            "raw_lines": [text],
        }
        return cls.from_dict(entry)

    @staticmethod
    def _parse_header(header: str, tech_line: str = ""):
        """Parse project_name, technology_stack, dates, github, demo from header/tech lines.

        Header formats:
        1. "ProjectName, Tech1, Tech2 MM/YYYY – MM/YYYY"  (tech in header with date)
        2. "ProjectName MM/YYYY – Present"                 (date in header, no tech)
        3. "ProjectName"                                   (no date, no tech in header)

        Tech line is a standalone comma-separated technology list on the next line.

        Returns:
            Tuple (project_name, technology_stack, start_date, end_date, github, demo)
        """
        project_name = ""
        technology_stack = []
        start_date = ""
        end_date = ""
        github = ""
        demo = ""

        if not header:
            return project_name, technology_stack, start_date, end_date, github, demo

        working = header

        # Extract GitHub / demo URLs
        github_m = re.search(r'https?://(?:www\.)?github\.com/[^\s,]+', working)
        if github_m:
            github = github_m.group(0)
            working = working.replace(github, '').strip()

        demo_m = re.search(
            r'https?://(?!github\.com)[^\s,]+',
            working
        )
        if demo_m:
            demo = demo_m.group(0)
            working = working.replace(demo, '').strip()

        # Extract date range at the end of the header
        date_m = re.search(
            r'\s+(\d{1,2}/\d{4}|\d{4})\s*(?:[-–]|to)\s*(Present|Current|Now|\d{1,2}/\d{4}|\d{4})\s*$',
            working, re.IGNORECASE
        )
        if date_m:
            start_date = date_m.group(1).strip()
            end_date = date_m.group(2).strip()
            working = working[:date_m.start()].strip().rstrip(',').strip()

        # The remainder is "ProjectName[, Tech1, Tech2, ...]"
        comma_parts = [p.strip() for p in working.split(',')]
        if comma_parts:
            project_name = comma_parts[0].strip()

        # Remaining comma parts after the project name could be inline techs
        inline_techs = [
            p.strip() for p in comma_parts[1:]
            if p.strip() and len(p.strip()) < 30
        ]

        # Build technology_stack: inline techs + tech_line tokens
        all_techs = list(inline_techs)
        if tech_line:
            all_techs += [t.strip() for t in tech_line.split(',') if t.strip()]

        # Deduplicate preserving order
        seen = set()
        for t in all_techs:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                technology_stack.append(t)

        return project_name, technology_stack, start_date, end_date, github, demo
