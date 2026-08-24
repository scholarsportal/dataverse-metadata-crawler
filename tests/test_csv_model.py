"""Test models/csv_model.py."""

import pytest

from dvmeta.models.csv_model import DatasetSubjects


@pytest.mark.parametrize(
    ("subject_str", "expected_subjects"),
    [
        (DatasetSubjects.CM_Subject_AH.value, DatasetSubjects.CM_Subject_AH.name),
        ("not a real subject", None),
    ],
)
def test_dataset_subjects(subject_str, expected_subjects):
    """Test DatasetSubjects enum."""
    assert DatasetSubjects.from_value(subject_str) == expected_subjects
