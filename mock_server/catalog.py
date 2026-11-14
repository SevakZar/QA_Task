"""Maps CellNumber values to fixture files and HTTP status codes."""

from pathlib import Path

TESTDATA = Path(__file__).resolve().parent.parent / "testdata"

CELL_SCENARIOS = {
    "09121111111": {"file": "s1_happy_path.json", "http_status": 200},
    "09122222222": {"file": "s2_bnpl_blocked.json", "http_status": 200},
    "09123333333": {"file": "s3_insufficient_credit.json", "http_status": 200},
    "09124444444": {"file": "s4_non_active_option.json", "http_status": 200},
    "09125555555": {"file": "s5_invalid_default.json", "http_status": 200},
    "09126666666": {"file": "s6_missing_field.json", "http_status": 200},
    "09127777777": {"file": "s7_wrong_types.json", "http_status": 200},
    "09128888888": {"file": "s8_http_500.json", "http_status": 500},
    "09129999999": {"file": "s8_body_status.json", "http_status": 200},
    "09120000009": {"file": "s9_missing_source_id.json", "http_status": 200},
    "09120000010": {"file": "s10_invalid_price_type.json", "http_status": 200},
    "09120000011": {"file": "s11_empty_options_clickable.json", "http_status": 200},
}


def resolve(cell_number: str) -> tuple[int, Path] | tuple[int, None]:
    scenario = CELL_SCENARIOS.get(cell_number)
    if scenario is None:
        return 404, None
    return scenario["http_status"], TESTDATA / scenario["file"]
