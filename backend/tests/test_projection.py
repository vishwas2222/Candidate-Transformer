from config.config_loader import OutputConfig
from projection.projector import Projector


def test_projection_includes_only_requested_fields(sample_canonical_candidate):
    config = OutputConfig(include_fields=["full_name", "emails"])
    projected = Projector().project(sample_canonical_candidate, config)
    assert set(projected.keys()) == {"full_name", "emails"}
    assert projected["full_name"] == "Jane Doe"


def test_projection_does_not_modify_original_candidate(sample_canonical_candidate):
    original_name = sample_canonical_candidate.full_name.value
    original_skills = list(sample_canonical_candidate.skills.value)
    config = OutputConfig(include_fields=["full_name", "skills"], sort_skills=True)

    projected = Projector().project(sample_canonical_candidate, config)
    # mutate the projected output
    projected["skills"].append("Hacked")
    projected["full_name"] = "Someone Else"

    assert sample_canonical_candidate.full_name.value == original_name
    assert list(sample_canonical_candidate.skills.value) == original_skills


def test_nested_projection_only_project_names(sample_canonical_candidate):
    config = OutputConfig(include_fields=["projects.project_name"])
    projected = Projector().project(sample_canonical_candidate, config)
    assert projected["projects"] == [{"project_name": "Portfolio Website"}]


def test_nested_projection_only_experience_title(sample_canonical_candidate):
    config = OutputConfig(include_fields=["experience.title"])
    projected = Projector().project(sample_canonical_candidate, config)
    assert projected["experience"] == [{"title": "Senior Engineer"}]


def test_nested_projection_only_education_institution(sample_canonical_candidate):
    config = OutputConfig(include_fields=["education.institution"])
    projected = Projector().project(sample_canonical_candidate, config)
    assert projected["education"] == [{"institution": "XYZ University"}]


def test_field_exclusion(sample_canonical_candidate):
    config = OutputConfig(
        include_fields=["full_name", "emails", "phones", "skills"],
        exclude_fields=["phones"],
    )
    projected = Projector().project(sample_canonical_candidate, config)
    assert "phones" not in projected


def test_field_mapping_renames_output_keys(sample_canonical_candidate):
    config = OutputConfig(
        include_fields=["full_name", "phones"],
        field_mapping={"full_name": "candidate_name", "phones": "mobile_numbers"},
    )
    projected = Projector().project(sample_canonical_candidate, config)
    assert "candidate_name" in projected
    assert "mobile_numbers" in projected
    assert "full_name" not in projected


def test_sort_skills(sample_canonical_candidate):
    config = OutputConfig(include_fields=["skills"], sort_skills=True)
    projected = Projector().project(sample_canonical_candidate, config)
    skills = projected["skills"]
    assert skills == sorted(skills, key=str.lower)


def test_empty_field_policy_remove(sample_canonical_candidate):
    sample_canonical_candidate.headline.value = ""
    config = OutputConfig(include_fields=["full_name", "headline"], empty_field_policy="remove")
    projected = Projector().project(sample_canonical_candidate, config)
    assert "headline" not in projected


def test_empty_field_policy_null(sample_canonical_candidate):
    sample_canonical_candidate.headline.value = ""
    config = OutputConfig(include_fields=["full_name", "headline"], empty_field_policy="null")
    projected = Projector().project(sample_canonical_candidate, config)
    assert projected["headline"] is None


def test_empty_field_policy_keep(sample_canonical_candidate):
    sample_canonical_candidate.headline.value = ""
    config = OutputConfig(include_fields=["full_name", "headline"], empty_field_policy="keep")
    projected = Projector().project(sample_canonical_candidate, config)
    assert projected["headline"] == ""


def test_confidence_and_sources_included_when_configured(sample_canonical_candidate):
    config = OutputConfig(include_fields=["full_name"], include_confidence=True, include_sources=True)
    projected = Projector().project(sample_canonical_candidate, config)
    assert projected["full_name"]["value"] == "Jane Doe"
    assert 0 <= projected["full_name"]["confidence"] <= 1
    assert isinstance(projected["full_name"]["sources"], list)


def test_confidence_and_sources_excluded_by_default(sample_canonical_candidate):
    config = OutputConfig(include_fields=["full_name"])
    projected = Projector().project(sample_canonical_candidate, config)
    assert projected["full_name"] == "Jane Doe"


def test_date_format_iso_normalizes_dates(sample_canonical_candidate):
    config = OutputConfig(include_fields=["experience"], date_format="ISO")
    projected = Projector().project(sample_canonical_candidate, config)
    assert projected["experience"][0]["start_date"] == "2022-01"
    assert projected["experience"][0]["end_date"] == "Present"


def test_raw_text_excluded_by_default(sample_canonical_candidate):
    config = OutputConfig(include_fields=["projects"])
    projected = Projector().project(sample_canonical_candidate, config)
    assert "raw_text" not in projected["projects"][0]


def test_raw_text_included_when_configured(sample_canonical_candidate):
    config = OutputConfig(include_fields=["projects"], include_raw_text=True)
    projected = Projector().project(sample_canonical_candidate, config)
    assert "raw_text" in projected["projects"][0]
