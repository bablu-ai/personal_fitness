import io
import json
import openpyxl
from app.services.excel_parser import parse_workbook, get_pillars_from_workbook


def _make_workbook(sheets: dict[str, list[list]]) -> io.BytesIO:
    """Build an in-memory .xlsx with given sheet data."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(sheet_name)
        for row in rows:
            ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def test_sheet_name_becomes_pillar():
    buf = _make_workbook({
        "Exercise": [["Name", "Schedule"], ["Zone 2 Cardio", "daily"]],
        "Nutrition": [["Name", "Target"], ["Protein", "150g"]],
    })
    tasks = parse_workbook(buf, "plan-1")
    pillars = {t["pillar"] for t in tasks}
    assert "exercise" in pillars
    assert "nutrition" in pillars


def test_flexible_column_mapping():
    buf = _make_workbook({
        "Supplements": [
            ["Activity", "Dose", "Best Time"],
            ["Vitamin D", "2000 IU", "morning"],
        ]
    })
    tasks = parse_workbook(buf, "plan-1")
    assert len(tasks) == 1
    assert tasks[0]["name"] == "Vitamin D"
    assert tasks[0]["target_value"] == "2000 IU"
    assert tasks[0]["timing"] == "morning"


def test_unknown_columns_stored_as_metadata():
    # "Brand" is an unknown column → stored in extra_metadata
    # "Source" maps to source_key in COLUMN_HINTS → stored as a direct field
    buf = _make_workbook({
        "Sleep": [
            ["Name", "Brand", "Source"],
            ["Sleep Stack", "Thorne", "Amazon"],
        ]
    })
    tasks = parse_workbook(buf, "plan-1")
    meta = json.loads(tasks[0]["extra_metadata"])
    assert meta.get("Brand") == "Thorne"
    assert tasks[0].get("source_key") == "Amazon"


def test_empty_rows_skipped():
    buf = _make_workbook({
        "Rest": [
            ["Name", "Schedule"],
            ["Meditation", "daily"],
            [None, None],
            ["Nap", "daily"],
        ]
    })
    tasks = parse_workbook(buf, "plan-1")
    assert len(tasks) == 2


def test_rows_without_name_skipped():
    buf = _make_workbook({
        "Exercise": [
            ["Name", "Schedule"],
            [None, "daily"],
            ["Valid Task", "daily"],
        ]
    })
    tasks = parse_workbook(buf, "plan-1")
    assert len(tasks) == 1
    assert tasks[0]["name"] == "Valid Task"


def test_get_pillars():
    buf = _make_workbook({
        "Exercise": [["Name"], ["Run"]],
        "Sleep": [["Name"], ["Sleep"]],
        "Custom Pillar": [["Name"], ["Task"]],
    })
    pillars = get_pillars_from_workbook(buf)
    assert "exercise" in pillars
    assert "sleep" in pillars
    assert "custom_pillar" in pillars
