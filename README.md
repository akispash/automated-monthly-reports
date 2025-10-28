# automated-monthly-reports

One-line: Python utility to aggregate taxi route Excel reports and produce ranked summaries.

## Quickstart
1. Clone:
   git clone https://github.com/akispash/automated-monthly-reports.git
2. Create & activate venv:
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
3. Install:
   pip install -r requirements.txt
4. Run (auto detect):
   python -m src.automated_reports.report_cli --input "Δρομολόγια Ταξι 25-26.xlsx"

Run specific mode:
- Flow A (workbook with sheets "Ανάλυση ανά δρομολόγιο" & "Σύνολο ανά αυτοκίνητο"):
  python -m src.automated_reports.report_cli --input "Αναφορά_Οκτώβριος.xlsx" --mode flowA --output "Κατάταξη_Οκτώβριος.xlsx"

- Flow B (wide sheet + fares):
  python -m src.automated_reports.report_cli --input "Δρομολόγια Ταξι 25-26.xlsx" --mode wide --month "Οκτώβριος" --fares-sheet "Δρομολόγια" --output "Αναφορά_Οκτώβριος.xlsx"

## Tests
pytest

## License
MIT
