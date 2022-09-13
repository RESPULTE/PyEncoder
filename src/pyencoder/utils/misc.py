from pyencoder import Settings


def check_is_symbol(__str: str) -> bool:
    if not isinstance(__str, str):
        raise TypeError(f"symbol must be of type (str), not ({type(__str).__name__})")
    elif len(__str) != 1:
        raise ValueError(f"symbol must be of length (1), not ({len(__str)})")
    elif __str not in Settings.SYMBOLS:
        raise ValueError(f"unknown symbol detected: {__str}")

    return True
