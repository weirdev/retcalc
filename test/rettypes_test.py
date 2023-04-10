from typing import Any, Callable, List, Optional, Type, TypeVar
import unittest

from rettypes import *


T = TypeVar('T')


def test_eq(case: unittest.TestCase, vals1: List[T], vals2: List[T],
            transform: Optional[Callable[[T], Any]] = None) -> None:
    # Hard assert for test code, not code being tested
    assert len(vals1) == len(vals2)
    for i in range(len(vals1)):
        a1 = vals1[i]
        if transform is not None:
            a1 = transform(a1)
        for j in range(len(vals2)):
            a2 = vals2[j]
            if transform is not None:
                a2 = transform(a2)
            if i == j:
                case.assertEqual(a1, a2)
            else:
                case.assertNotEqual(a1, a2)


def test_copy(case: unittest.TestCase, origlist: List[Any]) -> None:
    copylist = [a.copy() for a in origlist]
    test_eq(case, origlist, copylist)


def test_structured(case: unittest.TestCase, origlist: List[T], type: Type[T]) -> None:
    destructuredlist = [type.from_structured(  # type: ignore
        a.to_structured()) for a in origlist]  # type: ignore
    test_eq(case, origlist, destructuredlist)


def create_assets() -> List[Asset]:
    return [Asset("Asset1", 0.1, 0.01, 0.001),
            Asset("Asset2", 0.0, 10000, 0.0),
            Asset("Asset1", 0.01, 0.1, 0.001)]


class RetTypesTest(unittest.TestCase):
    def test_asset_eq(self):
        test_eq(self, create_assets(), create_assets())

    def test_asset_hash(self):
        test_eq(self, create_assets(), create_assets(),
                lambda a: hash(a))

    def test_asset_copy(self):
        test_copy(self, create_assets())

    def test_asset_structured(self):
        test_structured(self, create_assets(), Asset)


if __name__ == "__main__":
    unittest.main()
