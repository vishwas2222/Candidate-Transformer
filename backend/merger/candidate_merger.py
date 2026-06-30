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
        
        # 1. Helper to merge scalar fields (Name, Headline, Company, Title) using conflict resolution
        def merge_scalar(field_name: str) -> FieldMetadata:
            nonlocal field_count
            val1 = cand1.get(field_name, "")
            src1 = cand1.get("source", "")
            val2 = cand2.get(field_name, "")
            src2 = cand2.get("source", "")
            
            winner_val, winner_src = self.conflict_resolver.resolve(
                field_name, val1, src1, val2, src2
            )
            
            # Provenance: If both provided the same non-empty value, track both
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
            
            # Combine unique elements, counting duplicates removed for the merge summary
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
            
            # Direct concatenation
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
            "================================================"
        )
        return canonical
