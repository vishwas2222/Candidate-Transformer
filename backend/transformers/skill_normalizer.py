import os
import json
from typing import Dict, Optional
from transformers.base_normalizer import BaseNormalizer

# Default location of the externalized, configurable skill mapping file.
DEFAULT_SKILL_MAPPING_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "skill_mapping.json"
)

# Minimal built-in fallback used only if the config file is missing/unreadable,
# so the normalizer never fails outright.
_FALLBACK_SKILL_MAP = {
    "cpp": "C++",
    "c++": "C++",
    "python": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "react": "React",
    "aws": "Amazon Web Services",
    "sql": "SQL",
}


class SkillNormalizer(BaseNormalizer):
    """Normalizer for candidate skills mapping raw terms to canonical ones.
    
    The canonical skill mapping is externalized to config/skill_mapping.json
    so it can be edited without touching code. A custom mapping or path can
    still be supplied programmatically for testing or overrides.
    """

    def __init__(self, skill_map: Optional[Dict[str, str]] = None, mapping_path: Optional[str] = None):
        """Initializes the SkillNormalizer with a configurable skill map.
        
        Args:
            skill_map (Optional[Dict[str, str]]): Explicit dictionary mapping lowercase
                skills to canonical names. Takes precedence over mapping_path if given.
            mapping_path (Optional[str]): Path to a JSON skill-mapping file. Defaults to
                config/skill_mapping.json relative to the project root.
        """
        if skill_map is not None:
            self.skill_map = {k.lower().strip(): v for k, v in skill_map.items()}
        else:
            self.skill_map = self._load_mapping(mapping_path or DEFAULT_SKILL_MAPPING_PATH)

    @staticmethod
    def _load_mapping(path: str) -> Dict[str, str]:
        """Loads the skill mapping from a JSON config file.
        
        Falls back to a small built-in default mapping if the file is missing,
        unreadable, or malformed, so normalization never hard-fails.
        
        Args:
            path (str): Path to the JSON skill-mapping file.
            
        Returns:
            Dict[str, str]: Lowercase-keyed skill mapping.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_map = json.load(f)
            return {k.lower().strip(): v for k, v in raw_map.items()}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return dict(_FALLBACK_SKILL_MAP)

    def normalize(self, value: str) -> str:
        """Canonicalizes skills based on the skill mapping.
        
        Examples:
            - "cpp" -> "C++"
            - "python" -> "Python"
            - "js" -> "JavaScript"
            - "reactjs" -> "React"
            - "MyCustomSkill" -> "MyCustomSkill"
            
        Args:
            value (str): The raw skill term.
            
        Returns:
            str: The normalized/canonical skill.
        """
        if not isinstance(value, str) or not value:
            return ""
            
        cleaned = value.strip().lower()
        if cleaned in self.skill_map:
            return self.skill_map[cleaned]
            
        return value.strip()
