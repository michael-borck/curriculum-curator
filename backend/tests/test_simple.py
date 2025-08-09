"""
Simple test to verify pytest setup
"""

def test_basic_math():
    """Basic test to verify pytest is working"""
    assert 2 + 2 == 4

def test_string_operations():
    """Test basic string operations"""
    assert "hello".upper() == "HELLO"
    assert "world".lower() == "world"