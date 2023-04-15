from typing import Dict, Iterable
import unittest

from retcalc import *
from test.test_rettypes import create_asset_allocs


def sum_asset_allocs(assets: Iterable[AssetAllocation]) -> float:
    return sum([a.asset.value for a in assets])


class RetCalcTest(unittest.TestCase):
    def test_rebalance_assets_basic(self):
        assets = create_asset_allocs()

        rebalanced_assets = [aa.copy() for aa in assets]
        rebalance_assets(rebalanced_assets)

        self.assertEqual(len(assets), len(rebalanced_assets))
        self.assertAlmostEqual(sum_asset_allocs(assets), 
                               sum_asset_allocs(rebalanced_assets))
        
    def test_rebalance_assets_complex(self):
        assets = [
            AssetAllocation(Asset("Asset1", 0.1, 0, 0), 0, 10.1, 0),
            AssetAllocation(Asset("Asset2", 0, 0, 0), 0, 8, 0),
            AssetAllocation(Asset("Asset3", 3.2, 0, 0), 0, 0, 0),
            AssetAllocation(Asset("Asset4", 7, 0, 0), 1, 0, 0),
            AssetAllocation(Asset("Asset5", 28, 0, 0), 1, 0, 0),
        ]

        rebalanced_assets = [aa.copy() for aa in assets]
        rebalance_assets(rebalanced_assets)
        
        self.assertEqual(len(assets), len(rebalanced_assets))
        self.assertAlmostEqual(sum_asset_allocs(assets),
                               sum_asset_allocs(rebalanced_assets))
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
                assets_by_priority[assets[i].priority] = {assets[i].asset.name: assets[i]}
            try:
                rebalanced_assets_by_priority[rebalanced_assets[i].priority]\
                    [rebalanced_assets[i].asset.name] = rebalanced_assets[i]
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
