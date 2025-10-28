import pandas as pd
from pathlib import Path
from src.automated_reports.report import process_report_flowA, process_report_wide

def make_sample_flowA(path: Path):
    df_routes = pd.DataFrame({
        "Αυτοκίνητο": ["A", "A", "B"],
        "Αρ. Δρομολογίου": [1, 2, 1],
        "Δρομολόγια": ["r1", "r2", "r3"],
        "Έσοδα": [10.0, 20.0, 15.0]
    })
    df_totals = pd.DataFrame({
        "Αυτοκίνητο": ["A", "B"],
        "Έσοδα": [30.0, 15.0]
    })
    with pd.ExcelWriter(path) as writer:
        df_routes.to_excel(writer, sheet_name="Ανάλυση ανά δρομολόγιο", index=False)
        df_totals.to_excel(writer, sheet_name="Σύνολο ανά αυτοκίνητο", index=False)


def make_sample_wide(path: Path):
    df_wide = pd.DataFrame({
        "Ημερομηνία": ["2025-10-01", "2025-10-02"],
        1: [25, None],
        2: [None, 25]
    })
    fares = pd.DataFrame({
        "Αρ. Δρομολόγιου": [1, 2],
        "Τιμή": [15.0, 20.0]
    })
    with pd.ExcelWriter(path) as writer:
        df_wide.to_excel(writer, sheet_name="Οκτώβριος", index=False)
        fares.to_excel(writer, sheet_name="Δρομολόγια", index=False)


def test_flowA_creates_output(tmp_path):
    in_file = tmp_path / "flowA.xlsx"
    out_file = tmp_path / "outA.xlsx"
    make_sample_flowA(in_file)
    res = process_report_flowA(in_file, out_file)
    assert res.exists()
    xls = pd.ExcelFile(res)
    assert "Κατάταξη Δρομολογίων" in xls.sheet_names
    assert "Κατάταξη Εσόδων" in xls.sheet_names

def test_wide_creates_output(tmp_path):
    in_file = tmp_path / "flowB.xlsx"
    out_file = tmp_path / "outB.xlsx"
    make_sample_wide(in_file)
    res = process_report_wide(in_file, "Οκτώβριος", "Δρομολόγια", out_file)
    assert res.exists()
    xls = pd.ExcelFile(res)
    assert "Ανάλυση ανά δρομολόγιο" in xls.sheet_names
    assert "Σύνολο ανά αυτοκίνητο" in xls.sheet_names
