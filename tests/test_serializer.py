from enum import Enum
from dataclasses import dataclass

from config.config_loader import OutputConfig
from projection.recursive_serializer import RecursiveSerializer
from projection.serializer import CandidateSerializer


def test_serializes_plain_scalars():
    assert RecursiveSerializer.serialize("hello") == "hello"
    assert RecursiveSerializer.serialize(42) == 42
    assert RecursiveSerializer.serialize(True) is True
    assert RecursiveSerializer.serialize(None) is None


def test_serializes_lists_and_dicts():
    assert RecursiveSerializer.serialize([1, 2, 3]) == [1, 2, 3]
    assert RecursiveSerializer.serialize({"a": 1}) == {"a": 1}


def test_serializes_nested_dataclass():
    @dataclass
    class Inner:
        x: int = 1

    @dataclass
    class Outer:
        inner: Inner = None
        items: list = None

    obj = Outer(inner=Inner(x=5), items=[Inner(x=1), Inner(x=2)])
    result = RecursiveSerializer.serialize(obj)
    assert result == {"inner": {"x": 5}, "items": [{"x": 1}, {"x": 2}]}


def test_serializes_enum():
    class Color(Enum):
        RED = "red"

    assert RecursiveSerializer.serialize(Color.RED) == "red"


def test_serializes_candidate_field(sample_canonical_candidate):
    result = RecursiveSerializer.serialize(sample_canonical_candidate.full_name)
    assert result["value"] == "Jane Doe"
    assert "confidence" in result
    assert "sources" in result


def test_candidate_serializer_builds_metadata_and_candidate(sample_canonical_candidate):
    config = OutputConfig(include_fields=["full_name", "emails"])
    document = CandidateSerializer().serialize(sample_canonical_candidate, config, candidate_sources=2)
    assert "metadata" in document
    assert "candidate" in document
    assert document["metadata"]["profile"] == config.profile
    assert document["metadata"]["candidate_sources"] == 2
    assert "schema_version" in document["metadata"]
    assert "generated_at" in document["metadata"]


def test_candidate_serializer_metadata_can_be_disabled(sample_canonical_candidate):
    config = OutputConfig(include_fields=["full_name"], metadata={"include": False})
    document = CandidateSerializer().serialize(sample_canonical_candidate, config)
    assert "metadata" not in document
    assert "candidate" in document
