"""scripts/generate_test_plan.py の `_all_pairs` greedy アルゴリズムを検証する。

Codex レビュー Maj-6 で指摘された「pairwise 品質の保証なし」に対し、
- 全 2 因子組合せ (pair) が必ず網羅されること
- 単一因子では values 数の case をそのまま返すこと
- 0 因子では空 list を返すこと
を回帰テストで固定する。
"""

from __future__ import annotations

import itertools

from generate_test_plan import Factor, _all_pairs


def _all_required_pairs(factors: list[Factor]) -> set[tuple[str, str, str, str]]:
    required = set()
    for fa, fb in itertools.combinations(factors, 2):
        for va in fa.values:
            for vb in fb.values:
                required.add((fa.name, va, fb.name, vb))
    return required


def _covered_pairs(case: dict[str, str], factors: list[Factor]) -> set:
    out = set()
    for fa, fb in itertools.combinations(factors, 2):
        out.add((fa.name, case[fa.name], fb.name, case[fb.name]))
    return out


class TestAllPairs:
    def test_zero_factors(self):
        assert _all_pairs([]) == []

    def test_single_factor(self):
        f = Factor(name="country", values=["JP", "US", "EU"])
        out = _all_pairs([f])
        assert out == [{"country": "JP"}, {"country": "US"}, {"country": "EU"}]

    def test_two_factors_full_coverage(self):
        # 2x2 → 全組合せ 4 件で all-pairs も 4 件
        a = Factor("a", ["a1", "a2"])
        b = Factor("b", ["b1", "b2"])
        out = _all_pairs([a, b])
        required = _all_required_pairs([a, b])
        covered = set().union(*[_covered_pairs(c, [a, b]) for c in out])
        assert required <= covered

    def test_three_factors_pairs_all_covered(self):
        a = Factor("a", ["1", "2", "3"])
        b = Factor("b", ["x", "y"])
        c = Factor("c", ["t", "f"])
        out = _all_pairs([a, b, c])
        required = _all_required_pairs([a, b, c])
        covered = set().union(*[_covered_pairs(case, [a, b, c]) for case in out])
        # 全 2 因子 pair が網羅されること (2-factor coverage の最低要件)
        assert required <= covered, f"missing: {required - covered}"
        # 全組合せ (12) より小さい削減が効いているはず
        assert len(out) <= 3 * 2 * 2

    def test_each_case_includes_all_factor_keys(self):
        a = Factor("a", ["1", "2"])
        b = Factor("b", ["x", "y", "z"])
        out = _all_pairs([a, b])
        for case in out:
            assert set(case.keys()) == {"a", "b"}
