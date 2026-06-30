from typing import Dict, Optional
from transformers.base_normalizer import BaseNormalizer

class SkillNormalizer(BaseNormalizer):
    """Normalizer for candidate skills mapping raw terms to canonical ones."""

    def __init__(self, skill_map: Optional[Dict[str, str]] = None):
        """Initializes the SkillNormalizer with a configurable skill map.
        
        Args:
            skill_map (Optional[Dict[str, str]]): Dictionary mapping lowercase skills to canonical names.
        """
        if skill_map is None:
            # Default standard skill map
            self.skill_map = {
                "cpp": "C++",
                "c++": "C++",
                "c plus plus": "C++",
                "py": "Python",
                "python": "Python",
                "javascript": "JavaScript",
                "js": "JavaScript",
                "reactjs": "React",
                "react": "React",
                "aws": "Amazon Web Services",
                "amazon web services": "Amazon Web Services",
                "sql": "SQL",
                "html": "HTML",
                "css": "CSS",
                "git": "Git",
                "docker": "Docker",
                "kubernetes": "Kubernetes",
                "linux": "Linux"
            }
        else:
            self.skill_map = {k.lower().strip(): v for k, v in skill_map.items()}

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
