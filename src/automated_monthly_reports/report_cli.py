#!/usr/bin/env python3
from pathlib import Path
from typing import Union
import argparse
import logging
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def process_report_flowA(input_path: Union[str, Path], output_path: Union[str, Path]) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)

    xls = pd.ExcelFile(input_path)

    df_routes = pd.read_excel(xls, "Ανάλυση ανά δρομολόγιο")
    df_totals = pd.read_excel(xls, "Σύνολο ανά αυτοκίνητο")

    df_routes.columns = df_routes.columns.str.strip()
    df_totals.columns = df_totals.columns.str.strip()

    if "Έσοδα" in df_totals.columns:
        df_totals = df_totals.rename(columns={"Έσοδα": "Έσοδα_Σύνολο"})

    summary = df_routes.groupby("Αυτοκίνητο").agg({
        "Αρ. Δρομολογίου": "count",
        "Δρομολόγια": lambda x: list(x),
        "Έσοδα": "sum"
    }).rename(columns={
        "Αρ. Δρομολογίου": "Σύνολο Δρομολογίων",
        "Δρομολόγια": "Λίστα Δρομολογίων",
        "Έσοδα": "Συνολικά Έσοδα"
    }).reset_index()

    merged = pd.merge(summary, df_totals, on="Αυτοκίνητο", how="left")

    for col in ["Έσοδα_Σύνολο", "Συνολικά Έσοδα"]:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)

    merged["Διαφορά"] = merged.get("Έσοδα_Σύνολο", 0) - merged.get("Συνολικά Έσοδα", 0)

    sorted_by_routes = merged.sort_values(by="Σύνολο Δρομολογίων", ascending=False)
    sorted_by_income = merged.sort_values(by="Συνολικά Έσοδα", ascending=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path) as writer:
        sorted_by_routes.to_excel(writer, sheet_name="Κατάταξη Δρομολογίων", index=False)
        sorted_by_income.to_excel(writer, sheet_name="Κατάταξη Εσόδων", index=False)

    return output_path


def process_report_wide(input_path: Union[str, Path],
                        month_sheet: str,
                        fares_sheet: str,
                        output_path: Union[str, Path]) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)

    df = pd.read_excel(input_path, sheet_name=month_sheet)
    fares = pd.read_excel(input_path, sheet_name=fares_sheet)

    df_long = df.melt(id_vars=["Ημερομηνία"],
                      var_name="Αρ. Δρομολόγιου",
                      value_name="Αυτοκίνητο")

    df_long = df_long.dropna(subset=["Αυτοκίνητο"])

    df_long["Αρ. Δρομολόγιου"] = pd.to_numeric(df_long["Αρ. Δρομολόγιου"], errors="coerce")
    df_long["Αυτοκίνητο"] = pd.to_numeric(df_long["Αυτοκίνητο"], errors="coerce")
    df_long = df_long.dropna(subset=["Αρ. Δρομολόγιου", "Αυτοκίνητο"])
    df_long["Αρ. Δρομολόγιου"] = df_long["Αρ. Δρομολόγιου"].astype(int)
    df_long["Αυτοκίνητο"] = df_long["Αυτοκίνητο"].astype(int)

    df_merged = df_long.merge(fares, on="Αρ. Δρομολόγιου", how="left")

    report = df_merged.groupby(["Αυτοκίνητο", "Αρ. Δρομολόγιου"]).agg(
        Δρομολόγια=("Αρ. Δρομολόγιου", "count"),
        Έσοδα=("Τιμή", "sum")
    ).reset_index()

    total_per_car = report.groupby("Αυτοκίνητο")["Έσοδα"].sum().reset_index()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path) as writer:
        report.to_excel(writer, sheet_name="Ανάλυση ανά δρομολόγιο", index=False)
        total_per_car.to_excel(writer, sheet_name="Σύνολο ανά αυτοκίνητο", index=False)

    return output_path


def detect_flow_and_run(input_path: Union[str, Path],
                        month: str,
                        fares_sheet: str,
                        output_path: Union[str, Path]) -> Path:
    xls = pd.ExcelFile(input_path)
    sheets = [s.strip() for s in xls.sheet_names]

    if "Ανάλυση ανά δρομολόγιο" in sheets and "Σύνολο ανά αυτοκίνητο" in sheets:
        logger.info("Detected Flow A (standard report workbook).")
        return process_report_flowA(input_path, output_path)

    if month in sheets and fares_sheet in sheets:
        logger.info("Detected Flow B (wide workbook).")
        return process_report_wide(input_path, month, fares_sheet, output_path)

    raise RuntimeError("Could not detect a supported workbook layout. Check sheet names.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Automated monthly reports (single script)")
    parser.add_argument("--input", "-i", required=True, help="Path to input Excel workbook")
    parser.add_argument("--output", "-o", help="Path to output Excel file")
    parser.add_argument("--mode", "-m", choices=["auto", "flowA", "wide"], default="auto",
                        help="Processing mode: auto / flowA / wide")
    parser.add_argument("--month", help="Month sheet name for wide flow (e.g. Οκτώβριος)")
    parser.add_argument("--fares-sheet", default="Δρομολόγια", help="Fares sheet name for wide flow (default: Δρομολόγια)")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("Input file does not exist: %s", input_path)
        raise SystemExit(1)

    if args.output:
        output_path = Path(args.output)
    else:
        month_name = args.month or "Αναφορά"
        output_path = Path(f"Αναφορά_{month_name}.xlsx")

    if args.mode == "flowA":
        out = process_report_flowA(input_path, output_path)
    elif args.mode == "wide":
        if not args.month:
            logger.error("For mode 'wide' you must provide --month")
            raise SystemExit(1)
        out = process_report_wide(input_path, args.month, args.fares_sheet, output_path)
    else:  # auto
        if not args.month:
            inferred_month = None
            xls = pd.ExcelFile(input_path)
            for s in xls.sheet_names:
                if s.strip() in ("Ιανουάριος","Φεβρουάριος","Μάρτιος","Απρίλιος","Μάιος","Ιούνιος","Ιούλιος",
                                 "Αύγουστος","Σεπτέμβριος","Οκτώβριος","Νοέμβριος","Δεκέμβριος"):
                    inferred_month = s.strip()
                    break
            args.month = inferred_month or "Αναφορά"
        out = detect_flow_and_run(input_path, args.month, args.fares_sheet, output_path)

    logger.info("Report created: %s", out)
    print(f"✅ Η αναφορά δημιουργήθηκε: {out}")


if __name__ == "__main__":
    main()
