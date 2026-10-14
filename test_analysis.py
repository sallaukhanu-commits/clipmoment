import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from analysis import Candidate, dedupe, weighted_score, _windows
from providers import Segment


def test_weighted_score_bounds():
    assert weighted_score({"hook": 100, "self_contained": 100, "value": 100, "completeness": 100}) == 100
    assert weighted_score({}) == 0
    assert weighted_score({"hook": 200, "self_contained": -5}) == 30  # clamped


def test_dedupe_removes_heavy_overlap_keeps_best():
    a = Candidate(0, 30, "a", "", 90, {}, "")
    b = Candidate(5, 35, "b", "", 70, {}, "")   # heavy overlap with a
    c = Candidate(100, 130, "c", "", 60, {}, "")
    kept = dedupe([b, a, c])
    assert [k.title for k in kept] == ["a", "c"]


def test_windows_cover_all_segments():
    segs = [Segment(i * 10, i * 10 + 10, "x") for i in range(500)]
    wins = _windows(segs, window_sec=1500, overlap_sec=120)
    assert wins[0][0] == 0 and wins[-1][1] == 500
    assert all(hi > lo for lo, hi in wins)
