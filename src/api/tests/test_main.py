"""
Testes temporários para validação do pipeline CI.

Estes testes serão substituídos pelos testes reais da API.
"""

import pytest

from ci_test import add, multiply


class TestCIValidation:
    """Testes básicos para validação do pipeline CI."""

    def test_add_positive(self) -> None:
        """Testa adição de números positivos."""
        assert add(2, 3) == 5

    def test_add_negative(self) -> None:
        """Testa adição com números negativos."""
        assert add(-2, 3) == 1

    def test_multiply_positive(self) -> None:
        """Testa multiplicação de números positivos."""
        assert multiply(3, 4) == 12

    def test_multiply_zero(self) -> None:
        """Testa multiplicação por zero."""
        assert multiply(5, 0) == 0


@pytest.mark.parametrize("a,b,expected", [(1, 1, 2), (10, 20, 30), (-5, 5, 0)])
def test_add_parametrized(a: int, b: int, expected: int) -> None:
    """Testes parametrizados para adição."""
    assert add(a, b) == expected
