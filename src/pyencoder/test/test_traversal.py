import pytest
from pyencoder import utils

@pytest.fixture
def matrix2D():
    return [
        [1, 2, 3, 4], 
        [5, 6, 7, 8], 
        [9, 10, 11, 12], 
        [13, 14, 15, 16]
    ]


def test_diagonal_zigzag_traversal(matrix2D):
    assert (
        utils._diagonal_zigzag_traversal(matrix2D) == 
        [1, 2, 5, 9, 6, 3, 4, 7, 10, 13, 14, 11, 8, 12, 15, 16]
    )


def test_vertical_zigzag_traversal(matrix2D):
    assert (
        utils._vertical_zigzag_traversal(matrix2D) == 
        [1, 5, 9, 13, 14, 10, 6, 2, 3, 7, 11, 15, 16, 12, 8, 4]
    )


def test_horizontal_zigzag_traversal(matrix2D):
    assert (
        utils._horizontal_zigzag_traversal(matrix2D) == 
        [1, 2, 3, 4, 8, 7, 6, 5, 9, 10, 11, 12, 16, 15, 14, 13]
    )