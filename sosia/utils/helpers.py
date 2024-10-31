"""Module with helper functions."""


def custom_print(text, verbose):
    """Print text if verbose."""
    if verbose:
        print(text)


def validate_param(value, label, accepted_types=(int, float)):
    """Validates that a given value is of the specified types."""
    if value is not None and not isinstance(value, accepted_types):
        accepted_types_names = ", ".join(t.__name__ for t in accepted_types)
        msg = f"Argument '{label}' must be one of the following " \
              f"types: {accepted_types_names}"
        raise TypeError(msg)

