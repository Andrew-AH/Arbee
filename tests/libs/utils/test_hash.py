from libs.utils.hash import get_hash


def test_get_hash_when_same():
    assert get_hash("abc", "abc") == get_hash(
        "abc", "abc"
    ), "Hashes should be equal for same opportunities"


def test_get_hash_when_different():
    assert get_hash("abcdefg", "abc") != get_hash(
        "abc", "abc"
    ), "Hashes should not be equal for different opportunities"
