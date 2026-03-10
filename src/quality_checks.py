import pandas as pd
import numpy as np
from datetime import date

def _pct(numerator, denominator):
    """Calculate pass rate as a percentage."""
    if denominator == 0:
        return 100.0
    return round(100.0 * numerator / denominator, 2)

def _issue(dimension, field, description, affected_rows, total_rows, severity):
    return {
        "dimension":     dimension,
        "field":         field,
        "description":   description,
        "affected_rows": affected_rows,
        "total_rows":    total_rows,
        "pass_rate":     _pct(total_rows - affected_rows, total_rows),
        "severity":      severity,
    }
