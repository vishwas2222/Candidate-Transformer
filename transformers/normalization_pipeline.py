from typing import Dict, Any, List
from models.candidate import Candidate
from models.experience import Experience
from models.education import Education
from models.project import Project
from transformers.phone_normalizer import PhoneNormalizer
from transformers.email_normalizer import EmailNormalizer
from transformers.skill_normalizer import SkillNormalizer
from transformers.company_normalizer import CompanyNormalizer
from transformers.date_normalizer import DateNormalizer
from transformers.text_normalizer import TextNormalizer
from utils.logger import logger

class NormalizationPipeline:
    """Orchestrates the normalization and deduplication of candidate fields."""

    def __init__(self):
        self.phone_normalizer = PhoneNormalizer()
        self.email_normalizer = EmailNormalizer()
        self.skill_normalizer = SkillNormalizer()
        self.company_normalizer = CompanyNormalizer()
        self.date_normalizer = DateNormalizer()
        self.text_normalizer = TextNormalizer()

    def _deduplicate(self, lst: List[Any]) -> List[Any]:
        """Deduplicates a list while preserving original order."""
        seen = set()
        result = []
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def _normalize_end_date(self, end_date: str) -> str:
        """Normalize end date, preserving 'Present' variants."""
        if end_date.lower() in ["present", "current", "now"]:
            return "Present"
        return self.date_normalizer.normalize(end_date)

    def normalize_candidate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes and deduplicates all candidate fields in a raw dictionary.

        Args:
            raw_data (Dict[str, Any]): The raw candidate data dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing normalized candidate data.
        """
        logger.info("Starting normalization")

        normalized_data = {}

        # 1. Normalize full name
        raw_name = raw_data.get("full_name", "")
        normalized_data["full_name"] = self.text_normalizer.normalize_name(raw_name)

        # 2. Normalize emails and deduplicate
        emails = raw_data.get("emails", [])
        normalized_emails = []
        for email in emails:
            norm_email = self.email_normalizer.normalize(email)
            if norm_email:
                normalized_emails.append(norm_email)
        normalized_data["emails"] = self._deduplicate(normalized_emails)
        if normalized_data["emails"]:
            logger.info(f"Normalized {len(normalized_data['emails'])} email(s).")

        # 3. Normalize phones and deduplicate
        phones = raw_data.get("phones", [])
        normalized_phones = []
        for phone in phones:
            norm_phone = self.phone_normalizer.normalize(phone)
            if norm_phone:
                normalized_phones.append(norm_phone)
        normalized_data["phones"] = self._deduplicate(normalized_phones)
        if normalized_data["phones"]:
            logger.info(f"Normalized {len(normalized_data['phones'])} phone(s).")

        # 4. Normalize headline, current company, title
        normalized_data["headline"] = self.text_normalizer.normalize(raw_data.get("headline", ""))
        normalized_data["current_company"] = self.company_normalizer.normalize(
            raw_data.get("current_company", "")
        )
        normalized_data["title"] = self.text_normalizer.normalize(raw_data.get("title", ""))

        # 5. Normalize skills and deduplicate
        skills = raw_data.get("skills", [])
        normalized_skills = []
        for skill in skills:
            norm_skill = self.skill_normalizer.normalize(skill)
            if norm_skill:
                normalized_skills.append(norm_skill)
        normalized_data["skills"] = self._deduplicate(normalized_skills)
        if normalized_data["skills"]:
            logger.info(f"Normalized {len(normalized_data['skills'])} skills.")

        # 6. Normalize experience list
        # Items may already be Experience objects (from resume parser) or raw strings (legacy)
        raw_exp = raw_data.get("experience", [])
        normalized_exp = []
        for item in raw_exp:
            if isinstance(item, Experience):
                exp = item
            elif isinstance(item, dict):
                exp = Experience.from_dict(item)
            else:
                exp = Experience.from_raw_text(str(item))

            exp.company = self.company_normalizer.normalize(exp.company)
            exp.title = self.text_normalizer.normalize(exp.title)
            exp.location = self.text_normalizer.normalize(exp.location)
            exp.start_date = self.date_normalizer.normalize(exp.start_date)
            exp.end_date = self._normalize_end_date(exp.end_date)
            exp.description = [self.text_normalizer.normalize(d) for d in exp.description]
            normalized_exp.append(exp)
        normalized_data["experience"] = normalized_exp

        # 7. Normalize education list
        raw_edu = raw_data.get("education", [])
        normalized_edu = []
        for item in raw_edu:
            if isinstance(item, Education):
                edu = item
            elif isinstance(item, dict):
                edu = Education.from_dict(item)
            else:
                edu = Education.from_raw_text(str(item))

            edu.school = self.text_normalizer.normalize(edu.school)
            edu.institution = self.text_normalizer.normalize(edu.institution)
            edu.degree = self.text_normalizer.normalize(edu.degree)
            edu.specialization = self.text_normalizer.normalize(edu.specialization)
            edu.start_date = self.date_normalizer.normalize(edu.start_date)
            edu.end_date = self._normalize_end_date(edu.end_date)
            normalized_edu.append(edu)
        normalized_data["education"] = normalized_edu

        # 8. Normalize projects list
        raw_proj = raw_data.get("projects", [])
        normalized_proj = []
        for item in raw_proj:
            if isinstance(item, Project):
                proj = item
            elif isinstance(item, dict):
                proj = Project.from_dict(item)
            else:
                proj = Project.from_raw_text(str(item))

            proj.project_name = self.text_normalizer.normalize(proj.project_name)
            proj.start_date = self.date_normalizer.normalize(proj.start_date)
            proj.end_date = self._normalize_end_date(proj.end_date)
            proj.technology_stack = [
                self.skill_normalizer.normalize(t)
                for t in proj.technology_stack
                if t.strip()
            ]
            proj.description = [self.text_normalizer.normalize(d) for d in proj.description]
            normalized_proj.append(proj)
        normalized_data["projects"] = normalized_proj

        normalized_data["source"] = raw_data.get("source", "")

        return normalized_data
