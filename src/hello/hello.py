"""A simple hello world script."""

def print_hello(name: str) -> None:
    """Print a hello message.

    Args:
        name: The name to greet.

    Example:
        >>> print_hello("World")
        Hello, World!
    """
    print(f"Hello, {name}!")
