import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from validator import is_valid_email


def test_regular_email():
    assert is_valid_email("hello@gmail.com") is True


def test_plus_address():
    assert is_valid_email("hello+work@gmail.com") is True


def test_another_plus_address():
    assert is_valid_email("hello+college@gmail.com") is True


def test_invalid_email():
    assert is_valid_email("hello@gmail") is False


def test_plus_address_with_special_chars():
    assert is_valid_email("hello+work@gmail.com") is True


def test_plus_address_at_end():
    assert is_valid_email("hello+@gmail.com") is True


def test_plus_address_multiple_pluses():
    assert is_valid_email("hello++work@gmail.com") is True

if __name__ == "__main__":
    import unittest
    suite = unittest.TestLoader().loadTestsFromTestCase(sys.modules[__name__])
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")