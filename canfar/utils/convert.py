"""Convert between different data types."""

from typing import Any


def dict_to_tuples(dictionary: dict[str, Any]) -> list[tuple[str, Any]]:
    """Convert a dictionary to a list of tuples.

    Args:
        dictionary (Dict[str, Any]): Input dictionary.

    Returns:
        List[Tuple[str, Any]]: List of tuples.
    """
    # Create an empty list to store the tuples
    tuples: list[tuple[str, Any]] = []
    # Iterate over the key-value pairs in the dictionary
    for key, value in dictionary.items():
        # If the value is a dictionary, convert it to a list of tuples
        # where the key is repeated for each tuple
        if isinstance(value, dict):
            for k, v in value.items():
                tuples.append((key, f"{k}={v}"))
        else:
            # Add the tuple (key, value) to the list
            tuples.append((key, value))
    return tuples
