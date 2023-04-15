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


def test_structured(case: unittest.TestCase, origlist: List[T],
                    type: Type[T]) -> None:
    destructuredlist = [type.from_structured(  # type: ignore
        a.to_structured()) for a in origlist]  # type: ignore
    test_eq(case, origlist, destructuredlist)


def create_asset1() -> Asset:
    return Asset("Asset1", 0.1, 0.01, 0.001)


def create_assets() -> List[Asset]:
    return [create_asset1(),
            Asset("Asset2", 0.0, 10000, 0.0),
            Asset("Asset1", 0.01, 0.1, 0.001)]


def create_asset_alloc1(asset: Asset = create_asset1()) -> AssetAllocation:
    return AssetAllocation(asset, 1, 10.1, 0.1)


def create_asset_allocs() -> List[AssetAllocation]:
    assets = create_assets()
    return [create_asset_alloc1(assets[0]),
            AssetAllocation(assets[1], 0, 0, 0),
            AssetAllocation(assets[2], 1, 0.1, 10.1)]


def create_ret_settings1(
        asset_allocs: List[AssetAllocation] = create_asset_allocs()
) -> RetirementSettings:
    return RetirementSettings(10, (0.1, 0.01), 10, 1.1,
                              AssetDistribution(asset_allocs))


def create_ret_settings() -> List[RetirementSettings]:
    asset_allocs = create_asset_allocs()
    return [create_ret_settings1(asset_allocs),
            RetirementSettings(0, (0.0, 0.0), 0, 0.0,
                               AssetDistribution(asset_allocs[1:2])),
            RetirementSettings(10, (0.01, 0.1), 10, 1.1,
                               AssetDistribution(asset_allocs))]


class RetTypesTest(unittest.TestCase):
    # Asset tests

    def test_asset_eq(self):
        test_eq(self, create_assets(), create_assets())

    def test_asset_hash(self):
        test_eq(self, create_assets(), create_assets(),
                lambda a: hash(a))

    def test_asset_copy(self):
        test_copy(self, create_assets())

    def test_asset_structured(self):
        test_structured(self, create_assets(), Asset)

    def test_asset_update_values(self):
        asset = create_asset1()

        asset.update_val(AssetSetting.NAME, lambda _: "New name")
        self.assertEqual(asset.name, "New name")

        # TODO: Remaining member values

    # AssetAllocation tests

    def test_asset_alloc_eq(self):
        test_eq(self, create_asset_allocs(), create_asset_allocs())

    def test_asset_alloc_hash(self):
        test_eq(self, create_asset_allocs(), create_asset_allocs(),
                lambda a: hash(a))

    def test_asset_alloc_copy(self):
        test_copy(self, create_asset_allocs())

    def test_asset_alloc_structured(self):
        test_structured(self, create_asset_allocs(), AssetAllocation)

    def test_asset_alloc_update_values(self):
        asset_alloc = create_asset_alloc1()

        orig_asset_value = asset_alloc.asset.value
        asset_alloc.update_val(
            AllocationValue(AllocationSetting.ASSET,
                            AssetSetting.VALUE),  # type: ignore
            lambda value: value + 1)
        self.assertEqual(asset_alloc.asset.value, orig_asset_value + 1)

        asset_alloc.update_val(AllocationValue(
            AllocationSetting.PRIORITY), lambda _: 5)
        self.assertEqual(asset_alloc.priority, 5)

        # TODO: Remaining member values

    # RetirementSettings test

    def test_ret_settings_eq(self):
        test_eq(self, create_ret_settings(), create_ret_settings())

    def test_ret_settings_hash(self):
        test_eq(self, create_ret_settings(), create_ret_settings(),
                lambda a: hash(a))

    def test_ret_settings_copy(self):
        test_copy(self, create_ret_settings())

    def test_ret_settings_structured(self):
        test_structured(self, create_ret_settings(), RetirementSettings)

    def test_ret_settings_update_values(self):
        ret_settings = create_ret_settings1()

        ret_settings.update_val(RValue(RSetting.EXPENDATURE), lambda _: 99)
        self.assertEqual(ret_settings.expendature, 99)

        orig_alloc1_asset_value = \
            ret_settings.asset_distribution.asset_allocations[1].asset.value
        ret_settings.update_val(
            RValue(RSetting.ASSET_DISTRIBUTION,
                   DistributionValue(DistributionSetting.ASSET_ALLOCATIONS,
                                     (1, AllocationValue(AllocationSetting.ASSET,
                                                         AssetSetting.VALUE)))),  # type: ignore
            lambda value: value + 1)
        self.assertEqual(
            ret_settings.asset_distribution.asset_allocations[1].asset.value,
            orig_alloc1_asset_value + 1)

        # TODO: Remaining member values


if __name__ == "__main__":
    unittest.main()
