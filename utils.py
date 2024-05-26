digits = "abcdefghijklmnopqrstuvwxyz0123456789._"


def is_valid_tag(new_tag: str) -> bool:
    for char in new_tag:
        if char not in digits:
            return False

    return True
