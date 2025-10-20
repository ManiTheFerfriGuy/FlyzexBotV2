from flyzexbot.services.xp import calculate_level_progress, xp_required_for_level


def test_xp_required_matches_examples() -> None:
    assert xp_required_for_level(1) == 10
    assert xp_required_for_level(2) == 25
    assert xp_required_for_level(3) == 45


def test_calculate_level_progress_increases_levels() -> None:
    base = calculate_level_progress(0)
    assert base.level == 0
    assert base.next_threshold > base.current_threshold

    mid = calculate_level_progress(50)
    assert mid.level == 3
    assert mid.xp_to_next == mid.next_threshold - mid.total_xp

    high = calculate_level_progress(160)
    assert high.level > mid.level
