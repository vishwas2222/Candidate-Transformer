import pytest
from merger.conflict_resolver import ConflictResolver
from merger.confidence_engine import ConfidenceEngine
from merger.candidate_merger import CandidateMerger

def test_conflict_resolver_priority():
    resolver = ConflictResolver()
    
    # Priority: CSV (recruiter.csv) > Resume (sample_resume.pdf)
    # val1 from CSV, val2 from Resume -> val1 wins
    winner_val, winner_src = resolver.resolve("current_company", "Google", "recruiter.csv", "Amazon", "sample_resume.pdf")
    assert winner_val == "Google"
    assert winner_src == "recruiter.csv"
    
    # Reverse args, priority rules should still select CSV
    winner_val, winner_src = resolver.resolve("current_company", "Amazon", "sample_resume.pdf", "Google", "recruiter.csv")
    assert winner_val == "Google"
    assert winner_src == "recruiter.csv"
    
    # If one is empty, select the non-empty one regardless of source priority
    winner_val, winner_src = resolver.resolve("title", "", "recruiter.csv", "Staff Engineer", "sample_resume.pdf")
    assert winner_val == "Staff Engineer"
    assert winner_src == "sample_resume.pdf"

def test_confidence_engine():
    engine = ConfidenceEngine()
    
    assert engine.get_confidence_for_source("recruiter.csv") == 1.00
    assert engine.get_confidence_for_source("sample_resume.pdf") == 0.90
    assert engine.get_confidence_for_source("unknown.txt") == 0.50
    
    assert engine.get_merged_confidence(["sample_resume.pdf"]) == 0.90
    assert engine.get_merged_confidence(["sample_resume.pdf", "recruiter.csv"]) == 1.00

def test_merger_scalar_conflict():
    merger = CandidateMerger()
    
    cand1 = {
        "full_name": "John Doe",
        "current_company": "Google",
        "title": "SDE",
        "source": "recruiter.csv"
    }
    
    cand2 = {
        "full_name": "Johnathan Doe",
        "current_company": "Amazon",
        "title": "",
        "source": "sample_resume.pdf"
    }
    
    cc = merger.merge(cand1, cand2)
    
    # Name: Conflict! CSV "John Doe" should win
    assert cc.full_name.value == "John Doe"
    assert cc.full_name.confidence == 1.00
    assert cc.full_name.sources == ["recruiter.csv"]
    
    # Company: Conflict! CSV "Google" should win
    assert cc.current_company.value == "Google"
    assert cc.current_company.confidence == 1.00
    assert cc.current_company.sources == ["recruiter.csv"]
    
    # Title: CSV has "SDE", Resume has "". CSV wins
    assert cc.title.value == "SDE"
    assert cc.title.confidence == 1.00
    assert cc.title.sources == ["recruiter.csv"]


def test_conflict_resolver_tracks_conflict_report():
    """ConflictResolver should record structured conflict details (field, old/new
    value, winner, reason) for every conflict it resolves."""
    resolver = ConflictResolver()

    resolver.resolve("current_company", "Google LLC", "recruiter.csv", "Google", "sample_resume.pdf")

    assert len(resolver.conflicts) == 1
    report = resolver.conflicts[0]
    assert report["field"] == "current_company"
    assert report["old_value"] == "Google LLC"
    assert report["new_value"] == "Google"
    assert report["winner"] == "Google LLC"
    assert "recruiter.csv" in report["reason"]


def test_merge_produces_candidate_field_with_normalized_flag():
    """Every CandidateField produced by the merger should expose the new
    'normalized' attribute alongside value/confidence/sources."""
    merger = CandidateMerger()

    cand1 = {"full_name": "John Doe", "source": "recruiter.csv"}
    cand2 = {"full_name": "John Doe", "source": "sample_resume.pdf"}

    cc = merger.merge(cand1, cand2)

    assert hasattr(cc.full_name, "normalized")
    assert cc.full_name.normalized is True
