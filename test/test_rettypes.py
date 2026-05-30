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
            AssetAllocation(assets[2], 1, 0.1, 0.2)]


def create_asset_distribution1(
        asset_allocs: List[AssetAllocation] = create_asset_allocs()
) -> AssetDistribution:
    return AssetDistribution(asset_allocs)


def create_asset_distributions() -> List[AssetDistribution]:
    asset_allocs = create_asset_allocs()
    return [create_asset_distribution1(asset_allocs),
            AssetDistribution(asset_allocs[1:2]),
            AssetDistribution(asset_allocs[0:2])]


def create_ret_settings1(
        asset_allocs: List[AssetAllocation] = create_asset_allocs()
) -> RetirementSettings:
    return RetirementSettings(10, (0.1, 0.01), 10, 1.1,
                              AssetDistribution(asset_allocs), None)


def create_ret_settings() -> List[RetirementSettings]:
    asset_allocs = create_asset_allocs()
    return [create_ret_settings1(asset_allocs),
            RetirementSettings(0, (0.0, 0.0), 0, 0.0,
                               AssetDistribution(asset_allocs[1:2]), None),
            RetirementSettings(10, (0.01, 0.1), 10, 1.1,
                               AssetDistribution(asset_allocs), None)]


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

        asset.update_val(AssetSetting.VALUE, lambda _: 42.0)
        self.assertEqual(asset.value, 42.0)

        asset.update_val(AssetSetting.MEAN_RETURN, lambda _: 0.5)
        self.assertEqual(asset.mean_return, 0.5)

        asset.update_val(AssetSetting.RETURN_STDEV, lambda _: 0.2)
        self.assertEqual(asset.return_stdev, 0.2)

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

        asset_alloc.update_val(AllocationValue(
            AllocationSetting.MINIMUM_VALUE), lambda _: 99.9)
        self.assertEqual(asset_alloc.minimum_value, 99.9)

        asset_alloc.update_val(AllocationValue(
            AllocationSetting.DESIRED_FRACTION_OF_TOTAL_ASSETS),
            lambda _: 0.5)
        self.assertEqual(asset_alloc.desired_fraction_of_total_assets, 0.5)

    # AssetDistribution tests

    def test_asset_distribution_eq(self):
        test_eq(self, create_asset_distributions(),
                create_asset_distributions())

    def test_asset_distribution_hash(self):
        test_eq(self, create_asset_distributions(),
                create_asset_distributions(), lambda a: hash(a))

    def test_asset_distribution_copy(self):
        test_copy(self, create_asset_distributions())

    def test_asset_distribution_structured(self):
        test_structured(self, create_asset_distributions(),
                        AssetDistribution)

    def test_asset_distribution_current_value(self):
        dist = create_asset_distribution1()
        expected = sum(aa.asset.value for aa in dist.asset_allocations)
        self.assertAlmostEqual(dist.current_value(), expected)

    def test_asset_distribution_current_value_empty(self):
        dist = AssetDistribution([])
        self.assertAlmostEqual(dist.current_value(), 0)

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

        ret_settings.update_val(RValue(RSetting.EXPENDITURE), lambda _: 99)
        self.assertEqual(ret_settings.expenditure, 99)

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

        ret_settings.update_val(RValue(RSetting.INFLATION),
                                lambda _: (0.05, 0.02))
        self.assertEqual(ret_settings.inflation, (0.05, 0.02))

        ret_settings.update_val(RValue(RSetting.T), lambda _: 20)
        self.assertEqual(ret_settings.t, 20)

        ret_settings.update_val(RValue(RSetting.EMERGENCY_MIN),
                                lambda _: 5000)
        self.assertEqual(ret_settings.emergency_min, 5000)

        ret_settings.update_val(
            RValue(RSetting.EXPENDITURE_REDUCTION_FRAC), lambda _: 0.1)
        self.assertEqual(ret_settings.expenditure_reduction_frac, 0.1)

    def test_ret_settings_legacy_from_structured(self):
        rs = create_ret_settings1()
        structured = rs.to_structured()
        structured["asset_allocations"] = \
            structured.pop("asset_distribution")["asset_allocations"]
        legacy_rs = RetirementSettings.from_structured(structured)
        self.assertEqual(rs, legacy_rs)

    def test_ret_settings_expenditure_reduction_frac_roundtrip(self):
        asset_allocs = create_asset_allocs()
        rs = RetirementSettings(10, (0.1, 0.01), 10, 1.1,
                                AssetDistribution(asset_allocs), 0.25)
        structured = rs.to_structured()
        self.assertEqual(structured["expenditure_reduction_frac"], 0.25)
        restored = RetirementSettings.from_structured(structured)
        self.assertEqual(rs, restored)

    def test_ret_settings_expenditure_reduction_frac_none_roundtrip(self):
        rs = create_ret_settings1()
        self.assertIsNone(rs.expenditure_reduction_frac)
        structured = rs.to_structured()
        self.assertNotIn("expenditure_reduction_frac", structured)
        restored = RetirementSettings.from_structured(structured)
        self.assertIsNone(restored.expenditure_reduction_frac)
        self.assertEqual(rs, restored)


if __name__ == "__main__":
    unittest.main()
