from __future__ import annotations


class RuleViolation(AssertionError):
    def __init__(
        self,
        rule: str,
        message: str,
        *,
        method: dict | None = None,
        option: dict | None = None,
        actual=None,
    ):
        self.rule = rule
        self.method = method
        self.option = option
        self.actual = actual
        method_id = None if method is None else method.get("id")
        option_id = None if option is None else option.get("source_id")
        location = []
        if method_id is not None:
            location.append(f"method.id={method_id}")
        if option_id is not None:
            location.append(f"option.source_id={option_id}")
        where = f" [{', '.join(location)}]" if location else ""
        actual_part = "" if actual is None else f" | actual={actual!r}"
        super().__init__(f"{rule}: {message}{where}{actual_part}")
