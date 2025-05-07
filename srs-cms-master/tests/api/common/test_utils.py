import pytest
from api.common.utils import Utils


def test_it_parses_method_call_strings():
    # Not a method call, returns None
    name, pos_args, kw_args = Utils.parse_str_method("get")
    assert name is None
    assert pos_args is None
    assert kw_args is None

    # No args
    name, pos_args, kw_args = Utils.parse_str_method("get()")
    assert name == "get"
    assert pos_args == []
    assert kw_args == {}

    # Only positional args
    name, pos_args, kw_args = Utils.parse_str_method("get(1,'2',3)")
    assert name == "get"
    assert pos_args == [1, "2", 3]
    assert kw_args == {}

    # Only keyword args
    name, pos_args, kw_args = Utils.parse_str_method("get(one='1', two=2)")
    assert name == "get"
    assert pos_args == []
    assert kw_args == {"one": "1", "two": 2}

    # Positional and keyword args
    name, pos_args, kw_args = Utils.parse_str_method("get(1,'2',3, one='1', two=2)")
    assert name == "get"
    assert pos_args == [1, "2", 3]
    assert kw_args == {"one": "1", "two": 2}

    # Raises exception for invalid code
    with pytest.raises(SyntaxError):
        Utils.parse_str_method("get(1, one='1)")
