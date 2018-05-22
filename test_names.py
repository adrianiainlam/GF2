import pytest
from names import Names


@pytest.fixture
def empty_names():
    """ Returns a Names instance with initialising values of error_code_count = 0 and names = []"""
    return Names()

@pytest.fixture
def filled_names():
    """ Returns a Names instance with initialising values of error_code_count = 3 and names = []"""
    names = Names()
    names.unique_error_codes(3)
    names.lookup(["SW1", "SW2", "G1"])
    return names


def test_empty_init_values(empty_names):
    assert empty_names.error_code_count == 0
    assert empty_names.names == []

def test_filled_values(filled_names):
    assert filled_names.error_code_count == 3
    assert filled_names.names == ["SW1", "SW2", "G1"]


@pytest.mark.parametrize("name_string_list, expected_name_ID_list", [
    (["SW1", "SW2", "G1"], [0,1,2])
])
def test_lookup(filled_names, empty_names, name_string_list, expected_name_ID_list):
    assert filled_names.lookup(name_string_list) == expected_name_ID_list
    # also check that lookup will add names to name_list if not existing
    assert empty_names.lookup(name_string_list) == expected_name_ID_list



def test_lookup_raises_exceptions(filled_names):
    with pytest.raises(TypeError):
        filled_names.lookup("G1")
    with pytest.raises(TypeError):
        filled_names.lookup([5, "SW1"])



@pytest.mark.parametrize("name_ID, expected_name_string", [
    (0, "SW1"),
    (1, "SW2",),
    (2, "G1"),
    (5, None)
])
def test_get_name_string(filled_names, name_ID, expected_name_string):
    assert filled_names.get_name_string(name_ID) == expected_name_string

def test_get_name_string_raises_exceptions(filled_names):
    with pytest.raises(TypeError):
        filled_names.get_name_string("SW1")  #as "SW1" is not an integers
    with pytest.raises(IndexError):
        filled_names.get_name_string(-3)

@pytest.mark.parametrize("name_string, expected_name_ID", [
    ("SW1", 0),
    ("SW2", 1),
    ("G1", 2,),
    ("X1", None)
])
def test_query(filled_names, name_string, expected_name_ID):
    assert filled_names.query(name_string) == expected_name_ID

def test_query_raises_exceptions(filled_names):
    with pytest.raises(TypeError):
        filled_names.query(5) #as input to query should be a string
