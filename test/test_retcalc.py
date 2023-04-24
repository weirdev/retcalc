from typing import Dict, Iterable, List
import unittest

from retcalc import *


SIMPLE_ASSET_ALLOCATIONS = [
    AssetAllocation(Asset("Asset1", 0.1, 0.01, 0.001), 0, 10.1, 0.1),
    AssetAllocation(
        Asset("Asset2", 0.0, 10000, 0.0), 0, 0, 0),
    AssetAllocation(Asset("Asset1", 0.01, 0.1, 0.001), 1, 0.1, 0.2)]


COMPLEX_ASSET_ALLOCATIONS = [
    AssetAllocation(Asset("Asset1", 0.1, 0, 0), 0, 10.1, 0.2),
    AssetAllocation(Asset("Asset2", 0, 0, 0), 0, 8, 0.1),
    AssetAllocation(Asset("Asset3", 3.2, 0, 0), 0, 0, 0),
    AssetAllocation(Asset("Asset4", 7, 0, 0), 1, 0, 0),
    AssetAllocation(Asset("Asset5", 28, 0, 0), 1, 0, 0),
]


def sum_asset_allocs(assets: Iterable[AssetAllocation]) -> float:
    return sum([a.asset.value for a in assets])


def asset_allocs_with_cleared_min_values(
        assets: Iterable[AssetAllocation]) -> List[AssetAllocation]:
    cleared = []
    for asset in assets:
        asset = asset.copy()
        asset.minimum_value = 0
        cleared.append(asset)
    return cleared


def asset_allocs_with_cleared_fractions(
        assets: Iterable[AssetAllocation]) -> List[AssetAllocation]:
    cleared = []
    for asset in assets:
        asset = asset.copy()
        asset.desired_fraction_of_total_assets = 0
        cleared.append(asset)
    return cleared


def rebalance_assets_and_sanity_test(case: unittest.TestCase,
                                     assets: List[AssetAllocation]) -> List[AssetAllocation]:
    rebalanced_assets = [aa.copy() for aa in assets]
    rebalance_assets(rebalanced_assets)

    case.assertEqual(len(assets), len(rebalanced_assets))
    case.assertAlmostEqual(sum_asset_allocs(assets),
                           sum_asset_allocs(rebalanced_assets))
    return rebalanced_assets


class RetCalcTest(unittest.TestCase):
    def test_rebalance_assets_basic_min_value(self):
        assets = asset_allocs_with_cleared_fractions(SIMPLE_ASSET_ALLOCATIONS)

        rebalance_assets_and_sanity_test(self, assets)

    def test_rebalance_assets_complex_min_value(self):
        assets = asset_allocs_with_cleared_fractions(COMPLEX_ASSET_ALLOCATIONS)

        rebalanced_assets = rebalance_assets_and_sanity_test(self, assets)

        assets_by_priority: Dict[int, Dict[str, AssetAllocation]] = {}
        rebalanced_assets_by_priority = {}
        for i in range(len(assets)):
            self.assertEqual(assets[i].asset.name,
                             rebalanced_assets[i].asset.name)
            self.assertEqual(assets[i].minimum_value,
                             rebalanced_assets[i].minimum_value)
            try:
                assets_by_priority[assets[i].priority][assets[i].asset.name] = assets[i]
            except KeyError:
                assets_by_priority[assets[i].priority] = {
                    assets[i].asset.name: assets[i]}
            try:
                rebalanced_assets_by_priority[rebalanced_assets[i].priority][
                    rebalanced_assets[i].asset.name] = rebalanced_assets[i]
            except KeyError:
                rebalanced_assets_by_priority[rebalanced_assets[i].priority] = \
                    {rebalanced_assets[i].asset.name: rebalanced_assets[i]}

        self.assertEqual(len(assets_by_priority[0]),
                         len(rebalanced_assets_by_priority[0]))
        # Highest priority assets should be at their minimum values
        self.assertAlmostEqual(
            sum_asset_allocs(rebalanced_assets_by_priority[0].values()),
            18.1)
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[0]["Asset1"].asset.value,
            10.1)
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[0]["Asset2"].asset.value,
            8)
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[0]["Asset3"].asset.value,
            0)

        self.assertEqual(len(assets_by_priority[1]),
                         len(rebalanced_assets_by_priority[1]))
        # Lower priority assets should have received the remainder
        self.assertAlmostEqual(
            sum_asset_allocs(rebalanced_assets_by_priority[1].values()),
            20.2)
        # No minimum value specified, so should be split evenly
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[1]["Asset4"].asset.value,
            10.1)
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[1]["Asset5"].asset.value,
            10.1)

    def test_rebalance_assets_basic_fraction(self):
        assets = asset_allocs_with_cleared_min_values(SIMPLE_ASSET_ALLOCATIONS)

        rebalance_assets_and_sanity_test(self, assets)

    def test_rebalance_assets_complex_fraction(self):
        assets = asset_allocs_with_cleared_min_values(
            COMPLEX_ASSET_ALLOCATIONS)

        rebalanced_assets = rebalance_assets_and_sanity_test(self, assets)

        assets_by_priority: Dict[int, Dict[str, AssetAllocation]] = {}
        rebalanced_assets_by_priority = {}
        for i, asset in enumerate(assets):
            rebalanced_asset = rebalanced_assets[i]
            self.assertEqual(asset.asset.name,
                             rebalanced_asset.asset.name)
            self.assertAlmostEqual(
                asset.desired_fraction_of_total_assets,
                rebalanced_asset.desired_fraction_of_total_assets)
            try:
                assets_by_priority[asset.priority][asset.asset.name] = assets[i]
            except KeyError:
                assets_by_priority[asset.priority] = {
                    asset.asset.name: asset}
            try:
                rebalanced_assets_by_priority[
                    rebalanced_asset.priority][
                    rebalanced_asset.asset.name] = rebalanced_asset
            except KeyError:
                rebalanced_assets_by_priority[rebalanced_asset.priority] = \
                    {rebalanced_asset.asset.name: rebalanced_asset}
        asset_total = sum_asset_allocs(assets)

        self.assertEqual(len(assets_by_priority[0]),
                         len(rebalanced_assets_by_priority[0]))
        # Highest priority assets should be at their minimum values
        self.assertAlmostEqual(
            sum_asset_allocs(rebalanced_assets_by_priority[0].values()),
            asset_total * 0.3)
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[0]["Asset1"].asset.value,
            asset_total * 0.2)
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[0]["Asset2"].asset.value,
            asset_total * 0.1)
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[0]["Asset3"].asset.value,
            0)

        self.assertEqual(len(assets_by_priority[1]),
                         len(rebalanced_assets_by_priority[1]))
        # Lower priority assets should have received the remainder
        self.assertAlmostEqual(
            sum_asset_allocs(rebalanced_assets_by_priority[1].values()),
            asset_total * 0.7)
        # No minimum value specified, so should be split evenly
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[1]["Asset4"].asset.value,
            asset_total * 0.35)
        self.assertAlmostEqual(
            rebalanced_assets_by_priority[1]["Asset5"].asset.value,
            asset_total * 0.35)

    def test_rebalance_assets_basic_min_values_and_fraction(self):
        assets = SIMPLE_ASSET_ALLOCATIONS

        rebalance_assets_and_sanity_test(self, assets)

    def test_rebalance_assets_complex_min_values_and_fraction(self):
        assets = COMPLEX_ASSET_ALLOCATIONS

        rebalance_assets_and_sanity_test(self, assets)
