# app/schemas/resume_utils.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def str_to_bool(value: Any) -> bool:
    """
    Convert any value to boolean, handling 'Yes'/'No' strings.

    Args:
        value: Input value to convert to boolean

    Returns:
        bool: Converted boolean value

    Examples:
        >>> str_to_bool('Yes')
        True
        >>> str_to_bool('No')
        False
        >>> str_to_bool(True)
        True
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "yes"
    return bool(value)

