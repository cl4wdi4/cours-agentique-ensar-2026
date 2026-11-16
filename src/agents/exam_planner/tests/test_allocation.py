"""Tests de validation et de répartition du temps de révision."""

import pytest

from ..allocation import allocate_revision_time


def test_equal_scores_share_time_equally():
    """Des scores égaux donnent le même temps lorsque le budget est divisible."""
    result = allocate_revision_time({"SD_212": 1.0, "SSI_212": 1.0}, 600)
    assert result == {"SD_212": 300, "SSI_212": 300}


def test_different_scores_share_time_proportionally():
    """Les durées suivent les proportions des scores."""
    result = allocate_revision_time({"SD_212": 3.0, "SSI_212": 1.0}, 600)
    assert result == {"SD_212": 450, "SSI_212": 150}


def test_rounding_preserves_total_budget():
    """À reste égal, la première UE reçoit la minute supplémentaire."""
    result = allocate_revision_time({"SD_212": 1.0, "SSI_212": 1.0, "TC_101": 1.0}, 10)
    assert result == {"SD_212": 4, "SSI_212": 3, "TC_101": 3}
    assert sum(result.values()) == 10
    assert all(type(minutes) is int for minutes in result.values())


def test_zero_score_receives_no_time():
    """Une UE de score nul ne reçoit pas les minutes restantes."""
    result = allocate_revision_time({"TC_101": 0.0, "SD_212": 1.0, "SSI_212": 1.0}, 5)
    assert result == {"TC_101": 0, "SD_212": 3, "SSI_212": 2}


def test_largest_remainder_receives_extra_minute():
    """La minute restante va au plus grand reste, pas au plus grand score."""
    result = allocate_revision_time({"SD_212": 6.0, "SSI_212": 3.0, "TC_101": 1.0}, 7)
    assert result == {"SD_212": 4, "SSI_212": 2, "TC_101": 1}


def test_budget_smaller_than_number_of_ues():
    """Un budget très court peut laisser certaines UE sans minute attribuée."""
    result = allocate_revision_time({"SD_212": 1.0, "SSI_212": 1.0, "TC_101": 1.0}, 1)
    assert result == {"SD_212": 1, "SSI_212": 0, "TC_101": 0}


def test_single_ue_receives_entire_budget():
    """Une seule UE reçoit la totalité du temps ; les scores fournis restent inchangés."""
    scores = {"SD_212": 3.0}
    assert allocate_revision_time(scores, 600) == {"SD_212": 600}
    assert scores == {"SD_212": 3.0}


def test_zero_budget_is_rejected():
    """Un temps de révision nul ne permet pas de construire une répartition utile."""
    with pytest.raises(ValueError, match="entier strictement positif"):
        allocate_revision_time({"SD_212": 3.0}, 0)


def test_negative_budget_is_rejected():
    """Le temps disponible ne peut pas être négatif."""
    with pytest.raises(ValueError, match="entier strictement positif"):
        allocate_revision_time({"SD_212": 3.0}, -1)


@pytest.mark.parametrize("invalid_budget", [1.5, "600", None, True])
def test_non_integer_budget_is_rejected(invalid_budget):
    """Les minutes doivent être entières ; un booléen n'est pas un budget."""
    with pytest.raises(ValueError, match="entier strictement positif"):
        allocate_revision_time({"SD_212": 3.0}, invalid_budget)


def test_negative_score_is_rejected():
    """Chaque score doit être vérifié, même si un autre est positif."""
    with pytest.raises(ValueError, match="SSI_212"):
        allocate_revision_time({"SD_212": 3.0, "SSI_212": -1.0}, 600)


@pytest.mark.parametrize("invalid_score", [float("nan"), float("inf"), -float("inf")])
def test_non_finite_score_is_rejected(invalid_score):
    """NaN et les infinis ne permettent pas une répartition proportionnelle."""
    with pytest.raises(ValueError, match="SD_212"):
        allocate_revision_time({"SD_212": invalid_score}, 600)


@pytest.mark.parametrize("invalid_score", ["3", None, True])
def test_non_numeric_score_is_rejected(invalid_score):
    """Les scores doivent être numériques, sans conversion implicite."""
    with pytest.raises(ValueError, match="SD_212"):
        allocate_revision_time({"SD_212": invalid_score}, 600)


def test_empty_scores_are_rejected():
    """Il faut au moins une UE à laquelle attribuer du temps."""
    with pytest.raises(ValueError, match="au moins une UE"):
        allocate_revision_time({}, 600)


def test_all_zero_scores_are_rejected():
    """Même avec un budget valide, il faut au moins un score strictement positif."""
    with pytest.raises(ValueError, match="strictement positif"):
        allocate_revision_time({"SD_212": 0.0, "SSI_212": 0.0}, 600)
