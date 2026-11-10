import pytest

from app.engine.rules import Rules
from app.strategy.solver import UPCARDS, chart

US = Rules(hole_card="peek", h17=False, das=True, surrender=False)

# Kanoniczna strategia podstawowa: 4–8 talii, S17, DAS, peek, bez poddania. Kolumny: 2 3 4 5 6 7 8 9 10 A
US_HARD = {
    5: "HHHHHHHHHH", 6: "HHHHHHHHHH", 7: "HHHHHHHHHH", 8: "HHHHHHHHHH",
    9: "HDDDDHHHHH", 10: "DDDDDDDDHH", 11: "DDDDDDDDDH",
    12: "HHSSSHHHHH", 13: "SSSSSHHHHH", 14: "SSSSSHHHHH", 15: "SSSSSHHHHH", 16: "SSSSSHHHHH",
    17: "SSSSSSSSSS", 18: "SSSSSSSSSS", 19: "SSSSSSSSSS", 20: "SSSSSSSSSS",
}
US_SOFT = {
    13: "HHHDDHHHHH", 14: "HHHDDHHHHH", 15: "HHDDDHHHHH", 16: "HHDDDHHHHH",
    17: "HDDDDHHHHH", 18: "SDDDDSSHHH", 19: "SSSSSSSSSS", 20: "SSSSSSSSSS",
}
US_PAIRS = {
    "2": "PPPPPPHHHH", "3": "PPPPPPHHHH", "4": "HHHPPHHHHH", "5": "DDDDDDDDHH",
    "6": "PPPPPHHHHH", "7": "PPPPPPHHHH", "8": "PPPPPPPPPP", "9": "PPPPPSPPSS",
    "10": "SSSSSSSSSS", "A": "PPPPPPPPPP",
}


def letters(rows, key):
    return "".join(c["code"][0] for c in rows[key])


@pytest.mark.parametrize("section,expected", [("hard", US_HARD), ("soft", US_SOFT), ("pairs", US_PAIRS)])
def test_us_basic_strategy_cell_by_cell(section, expected):
    tbl = chart(US)
    assert tbl["upcards"] == UPCARDS
    rows = {r["label"]: r["cells"] for r in tbl[section]}
    diffs = []
    for row, exp in expected.items():
        got = letters(rows, str(row))
        for up, e, g in zip(UPCARDS, exp, got):
            if e != g:
                diffs.append(f"{section} {row} vs {up}: oczekiwano {e}, jest {g}")
    assert diffs == []


def cell(rules, section, row, up):
    tbl = chart(rules)
    r = next(r for r in tbl[section] if r["label"] == str(row))
    return r["cells"][UPCARDS.index(up)]["code"]


def test_h17_differences():
    h17 = Rules(hole_card="peek", h17=True)
    assert cell(h17, "hard", 11, "A")[0] == "D"
    assert cell(h17, "soft", 18, "2") == "Ds"
    assert cell(h17, "soft", 19, "6") == "Ds"


def test_surrender_cells():
    r = Rules(hole_card="peek", surrender=True)
    for up in ("9", "10", "A"):
        assert cell(r, "hard", 16, up) == "Rh", up
    assert cell(r, "hard", 15, "10") == "Rh"
    assert cell(r, "hard", 15, "9") == "H"


def test_enhc_no_obo_is_more_careful():
    eu = Rules()  # domyślne: ENHC, bez OBO
    assert cell(eu, "hard", 11, "10") == "H"
    assert cell(eu, "hard", 11, "A") == "H"
    assert cell(eu, "hard", 11, "9")[0] == "D"
    assert cell(eu, "pairs", "8", "6") == "P"


def test_double_fallback_codes():
    assert cell(US, "hard", 11, "6") == "Dh"
    assert cell(US, "soft", 18, "6") == "Ds"


def test_evs_present_and_sane():
    c = chart(US)["hard"][0]["cells"][0]
    assert set(c["evs"]) >= {"H", "S", "D"}
    for row in chart(US)["hard"]:
        for cell_ in row["cells"]:
            assert all(-2.0 <= v <= 2.0 for v in cell_["evs"].values())
