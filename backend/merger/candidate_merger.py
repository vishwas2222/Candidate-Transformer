import uuid
from typing import Dict, Any, List
from models.candidate import CanonicalCandidate, FieldMetadata
from merger.conflict_resolver import ConflictResolver
from merger.confidence_engine import ConfidenceEngine
from merger.provenance_tracker import ProvenanceTracker
from utils.logger import logger


class CandidateMerger:
    """Merges multiple normalized candidate profiles into one CanonicalCandidate profile."""

    def __init__(self):
        self.conflict_resolver = ConflictResolver()
        self.confidence_engine = ConfidenceEngine()
        self.provenance_tracker = ProvenanceTracker()

    def merge(self, cand1: Dict[str, Any], cand2: Dict[str, Any]) -> CanonicalCandidate:
        """Merges two normalized candidate dictionaries.

        Args:
            cand1 (Dict[str, Any]): First normalized candidate profile.
            cand2 (Dict[str, Any]): Second normalized candidate profile.

        Returns:
            CanonicalCandidate: The merged candidate profile.
        """
        canonical = CanonicalCandidate()
        field_count = 0
        duplicate_counts = {"emails": 0, "phones": 0, "skills": 0}

        # 1. Helper to merge scalar fields using conflict resolution
        def merge_scalar(field_name: str) -> FieldMetadata:
            nonlocal field_count
            val1 = cand1.get(field_name, "")
            src1 = cand1.get("source", "")
            val2 = cand2.get(field_name, "")
            src2 = cand2.get("source", "")

            winner_val, winner_src = self.conflict_resolver.resolve(
                field_name, val1, src1, val2, src2
            )

            if val1 == val2 and val1:
                sources = self.provenance_tracker.merge_provenance([src1], [src2])
            else:
                sources = self.provenance_tracker.get_provenance(winner_src)

            confidence = self.confidence_engine.get_merged_confidence(sources)
            field_count += 1
            return FieldMetadata(value=winner_val, confidence=confidence, sources=sources)

        canonical.full_name = merge_scalar("full_name")
        canonical.headline = merge_scalar("headline")
        canonical.current_company = merge_scalar("current_company")
        canonical.title = merge_scalar("title")

        # 2. Helper to merge list fields (emails, phones, skills) using UNION rule
        def merge_list(field_name: str) -> FieldMetadata:
            nonlocal field_count
            list1 = cand1.get(field_name, [])
            src1 = cand1.get("source", "")
            list2 = cand2.get(field_name, [])
            src2 = cand2.get("source", "")

            merged_list = []
            duplicates_removed = 0
            for val in list1 + list2:
                if val not in merged_list:
                    merged_list.append(val)
                else:
                    duplicates_removed += 1
            if field_name in duplicate_counts:
                duplicate_counts[field_name] = duplicates_removed

            sources = []
            if list1:
                sources.append(src1)
            if list2 and src2 not in sources:
                sources.append(src2)

            confidence = self.confidence_engine.get_merged_confidence(sources)
            field_count += 1
            return FieldMetadata(value=merged_list, confidence=confidence, sources=sources)

        canonical.emails = merge_list("emails")
        canonical.phones = merge_list("phones")
        canonical.skills = merge_list("skills")

        # 3. Helper to merge list fields (experience, education) using APPEND rule
        def merge_append(field_name: str) -> FieldMetadata:
            nonlocal field_count
            list1 = cand1.get(field_name, [])
            src1 = cand1.get("source", "")
            list2 = cand2.get(field_name, [])
            src2 = cand2.get("source", "")

            merged_list = list1 + list2
            sources = []
            if list1:
                sources.append(src1)
            if list2 and src2 not in sources:
                sources.append(src2)

            confidence = self.confidence_engine.get_merged_confidence(sources)
            field_count += 1
            return FieldMetadata(value=merged_list, confidence=confidence, sources=sources)

        canonical.experience = merge_append("experience")
        canonical.education = merge_append("education")
        canonical.projects = merge_append("projects")

        # ── New fields ─────────────────────────────────────────────────────────

        # 4. location — dict merge: prefer the richer source (more filled keys)
        loc1 = cand1.get("location") or {}
        loc2 = cand2.get("location") or {}
        src1 = cand1.get("source", "")
        src2 = cand2.get("source", "")
        filled1 = sum(1 for v in loc1.values() if v)
        filled2 = sum(1 for v in loc2.values() if v)
        winner_loc = loc1 if filled1 >= filled2 else loc2
        winner_loc_src = src1 if filled1 >= filled2 else src2
        loc_sources = [s for s in [winner_loc_src] if s]
        canonical.location = FieldMetadata(
            value=winner_loc,
            confidence=self.confidence_engine.get_merged_confidence(loc_sources),
            sources=loc_sources,
        )
        field_count += 1

        # 5. links — dict merge: fill each key from whichever source has it
        lnk1 = cand1.get("links") or {}
        lnk2 = cand2.get("links") or {}
        merged_links = {
            "linkedin":  lnk1.get("linkedin")  or lnk2.get("linkedin")  or "",
            "github":    lnk1.get("github")     or lnk2.get("github")    or "",
            "portfolio": lnk1.get("portfolio")  or lnk2.get("portfolio") or "",
            "other":     list({
                u for u in (lnk1.get("other", []) + lnk2.get("other", []))
                if u
            }),
        }
        lnk_sources = list({s for s, l in [(src1, lnk1), (src2, lnk2)] if any(l.get(k) for k in ["linkedin","github","portfolio"]) and s})
        canonical.links = FieldMetadata(
            value=merged_links,
            confidence=self.confidence_engine.get_merged_confidence(lnk_sources) if lnk_sources else 0.0,
            sources=lnk_sources,
        )
        field_count += 1

        # 6. years_experience — take the larger value (more sources → richer data)
        ye1 = cand1.get("years_experience")
        ye2 = cand2.get("years_experience")
        if ye1 is not None and ye2 is not None:
            winner_ye = max(ye1, ye2)
            ye_src = src1 if ye1 >= ye2 else src2
        elif ye1 is not None:
            winner_ye, ye_src = ye1, src1
        elif ye2 is not None:
            winner_ye, ye_src = ye2, src2
        else:
            winner_ye, ye_src = None, ""
        ye_sources = [ye_src] if ye_src else []
        canonical.years_experience = FieldMetadata(
            value=winner_ye,
            confidence=self.confidence_engine.get_merged_confidence(ye_sources) if ye_sources else 0.0,
            sources=ye_sources,
        )
        field_count += 1

        # 7. candidate_id — generate a deterministic UUID from full_name + first email
        name_val  = canonical.full_name.value or ""
        email_val = (canonical.emails.value or [""])[0]
        seed_str  = f"{name_val.lower().strip()}:{email_val.lower().strip()}"
        canonical.candidate_id = FieldMetadata(
            value=str(uuid.uuid5(uuid.NAMESPACE_URL, seed_str)),
            confidence=1.0,
            sources=["system"],
        )
        field_count += 1

        # 8. overall_confidence — average of all field confidences
        field_confidences = [
            canonical.full_name.confidence,
            canonical.emails.confidence,
            canonical.phones.confidence,
            canonical.headline.confidence,
            canonical.current_company.confidence,
            canonical.title.confidence,
            canonical.skills.confidence,
            canonical.experience.confidence,
            canonical.education.confidence,
            canonical.projects.confidence,
            canonical.location.confidence,
            canonical.links.confidence,
            canonical.years_experience.confidence,
        ]
        non_zero = [c for c in field_confidences if c > 0]
        canonical.overall_confidence = round(
            sum(non_zero) / len(non_zero) if non_zero else 0.0, 3
        )

        logger.info(f"Assigned confidence to {field_count} fields.")

        source_count = len({s for s in (cand1.get("source", ""), cand2.get("source", "")) if s})
        logger.info(f"Merged {source_count} candidate source(s).")

        conflicts_found = len(self.conflict_resolver.conflicts)
        logger.info(
            "\n================================================\n"
            "Merge Summary\n"
            "================================================\n"
            f"Candidate Sources        : {source_count}\n"
            f"Fields Normalized        : {field_count}\n"
            f"Duplicate Skills Removed : {duplicate_counts['skills']}\n"
            f"Duplicate Emails Removed : {duplicate_counts['emails']}\n"
            f"Duplicate Phones Removed : {duplicate_counts['phones']}\n"
            f"Conflicts Found          : {conflicts_found}\n"
            f"Conflicts Resolved       : {conflicts_found}\n"
            f"Confidence Assigned      : {field_count}\n"
            f"Overall Confidence       : {canonical.overall_confidence}\n"
            "================================================"
        )
        return canonical
