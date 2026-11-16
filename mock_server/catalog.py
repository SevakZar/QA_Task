"""Maps CellNumber values to fixture files and HTTP status codes."""

from pathlib import Path

TESTDATA = Path(__file__).resolve().parent.parent / "testdata"

CELL_SCENARIOS = {
    "09121111111": {"file": "01_positive/S01_happy_path.json", "http_status": 200},
    "09122222222": {"file": "01_positive/S02_bnpl_blocked.json", "http_status": 200},
    "09123333333": {"file": "01_positive/S03_insufficient_credit.json", "http_status": 200},
    "09124444444": {"file": "01_positive/S04_non_active_option.json", "http_status": 200},
    "09125555555": {"file": "02_negative/S05_invalid_default.json", "http_status": 200},
    "09126666666": {"file": "02_negative/S06_missing_required_field.json", "http_status": 200},
    "09127777777": {"file": "02_negative/S07_wrong_types.json", "http_status": 200},
    "09128888888": {"file": "02_negative/S09_http_500.json", "http_status": 500},
    "09129999999": {"file": "02_negative/S08_body_status.json", "http_status": 200},
    "09120000009": {"file": "02_negative/S10_missing_source_id.json", "http_status": 200},
    "09120000010": {"file": "02_negative/S11_invalid_price_type.json", "http_status": 200},
    "09120000011": {"file": "02_negative/S12_empty_options_clickable.json", "http_status": 200},
}


def resolve(cell_number: str) -> tuple[int, Path] | tuple[int, None]:
    scenario = CELL_SCENARIOS.get(cell_number)
    if scenario is None:
        return 404, None
    return scenario["http_status"], TESTDATA / scenario["file"]
