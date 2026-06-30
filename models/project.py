from dataclasses import dataclass, field
import re
from typing import List

@dataclass
class Project:
    """Dataclass representing a candidate's project."""
    raw_text: str
    project_name: str = ""
    technologies: List[str] = field(default_factory=list)
    description: List[str] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""

    @classmethod
    def from_raw_text(cls, text: str) -> 'Project':
        """Heuristic to parse a grouped project entry into structured fields.
        
        Expects grouped format: "Header line | Tech line | Bullet1 | Bullet2"
        Header examples:
        - "Hybrid Vision-Based Indoor Localization Framework, 2026 – Present"
        - "ProctorAI, React, Flask, Python, MediaPipe, YOLOv8 10/2025 – 11/2025"
        
        Args:
            text (str): The raw grouped project text.
            
        Returns:
            Project: A Project object with parsed fields.
        """
        if not text:
            return cls("")

        parts = [p.strip() for p in text.split(' | ')]
        header = parts[0]
        remaining_parts = parts[1:] if len(parts) > 1 else []

        project_name = ""
        technologies = []
        description = []
        start_date = ""
        end_date = ""

        # Extract date range from the header line
        date_match = re.search(
            r'\s+(\d{1,2}/\d{4}|\d{4})\s*(?:[-–]|to)\s*(Present|Current|Now|\d{1,2}/\d{4}|\d{4})\s*$',
            header, re.IGNORECASE
        )

        header_no_date = header
        if date_match:
            start_date = date_match.group(1).strip()
            end_date = date_match.group(2).strip()
            header_no_date = header[:date_match.start()].strip().rstrip(',').strip()

        # Split header by first comma to get project name
        comma_parts = [p.strip() for p in header_no_date.split(',', 1)]
        project_name = comma_parts[0]

        # Check remaining parts for a dedicated technology line
        # A tech line is typically a comma-separated list of short terms (e.g. "Python, OpenCV, SLAM")
        for part in remaining_parts:
            # Heuristic: if line is mostly short comma-separated tokens, treat as tech
            tokens = [t.strip() for t in part.split(',')]
            avg_len = sum(len(t) for t in tokens) / max(len(tokens), 1)
            if len(tokens) >= 2 and avg_len < 25:
                technologies.extend(tokens)
            else:
                description.append(part)

        return cls(
            raw_text=text,
            project_name=project_name,
            technologies=technologies,
            description=description,
            start_date=start_date,
            end_date=end_date
        )
