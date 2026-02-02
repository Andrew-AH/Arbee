from libs.utils.strings import standardize_string


def test_standardize_string_when_string_has_whitespace():
    # arrange
    input_string = " s hbou  rne rebel"
    expected_result = "shbournerebel"

    # act
    result = standardize_string(input_string)

    # assert
    assert result == expected_result


def test_standardize_string_when_string_has_puncutation():
    # arrange
    input_string = "sh'bo.ur,n/ereb$el"
    expected_result = "shbournerebel"

    # act
    result = standardize_string(input_string)

    # assert
    assert result == expected_result


def test_standardize_string_when_string_has_capital_letter():
    # arrange
    input_string = "ShboUrneRebEl"
    expected_result = "shbournerebel"

    # act
    result = standardize_string(input_string)

    # assert
    assert result == expected_result
