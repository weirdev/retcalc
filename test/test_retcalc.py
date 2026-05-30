import os
import random
import tempfile
from typing import Dict, Iterable, List
import unittest
from unittest.mock import patch

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

    def test_rebalance_assets_single_asset(self):
        assets = [AssetAllocation(Asset("Only", 100, 0, 0), 0, 0, 0)]
        rebalanced = rebalance_assets_and_sanity_test(self, assets)
        self.assertAlmostEqual(rebalanced[0].asset.value, 100)

    def test_rebalance_assets_all_zero(self):
        assets = [
            AssetAllocation(Asset("A", 0, 0, 0), 0, 0, 0),
            AssetAllocation(Asset("B", 0, 0, 0), 0, 0, 0),
        ]
        rebalanced = rebalance_assets_and_sanity_test(self, assets)
        for aa in rebalanced:
            self.assertAlmostEqual(aa.asset.value, 0)

    def test_rebalance_assets_single_priority_class_fractions(self):
        assets = [
            AssetAllocation(Asset("A", 60, 0, 0), 0, 0, 0.5),
            AssetAllocation(Asset("B", 30, 0, 0), 0, 0, 0.3),
            AssetAllocation(Asset("C", 10, 0, 0), 0, 0, 0.2),
        ]
        rebalanced = rebalance_assets_and_sanity_test(self, assets)
        total = sum_asset_allocs(assets)
        self.assertAlmostEqual(rebalanced[0].asset.value, total * 0.5)
        self.assertAlmostEqual(rebalanced[1].asset.value, total * 0.3)
        self.assertAlmostEqual(rebalanced[2].asset.value, total * 0.2)


class RetirementValueTest(unittest.TestCase):
    def test_single_step_deterministic(self):
        random.seed(42)
        inflation_s = random.gauss(0.02, 0.005)
        asset_return = random.gauss(0.05, 0.01)

        random.seed(42)
        asset = Asset("Stock", 1000, 0.05, 0.01)
        alloc = AssetAllocation(asset, 0, 0, 0)
        rs = RetirementSettings(50, (0.02, 0.005), 1, 0,
                                AssetDistribution([alloc]), None)
        result = retirement_value(rs)

        expected_value = (1000 - 50) * (1 + asset_return)
        expected_expenditure = 50 * (1 + inflation_s)

        self.assertEqual(result.t, 0)
        self.assertAlmostEqual(
            result.asset_distribution.asset_allocations[0].asset.value,
            expected_value)
        self.assertAlmostEqual(result.expenditure, expected_expenditure)

    def test_original_not_modified(self):
        random.seed(42)
        asset = Asset("Stock", 1000, 0.05, 0.01)
        alloc = AssetAllocation(asset, 0, 0, 0)
        rs = RetirementSettings(50, (0.02, 0.005), 5, 0,
                                AssetDistribution([alloc]), None)
        original_value = rs.current_value()
        original_t = rs.t
        retirement_value(rs)
        self.assertAlmostEqual(rs.current_value(), original_value)
        self.assertEqual(rs.t, original_t)

    def test_hit_zero(self):
        with patch('random.gauss', side_effect=[0.02]):
            asset = Asset("Stock", 50, 0.05, 0.01)
            alloc = AssetAllocation(asset, 0, 0, 0)
            rs = RetirementSettings(100, (0.02, 0.0), 1, 0,
                                    AssetDistribution([alloc]), None)
            result = retirement_value(rs)

        self.assertEqual(result.t, 0)
        self.assertAlmostEqual(
            result.asset_distribution.asset_allocations[0].asset.value,
            -50)

    def test_expenditure_reduction(self):
        gauss_values = [0.02, 0.05, 0.02, 0.10]

        asset_no = Asset("Stock", 1000, 0.10, 0.01)
        alloc_no = AssetAllocation(asset_no, 0, 0, 0)
        rs_no = RetirementSettings(100, (0.02, 0.0), 2, 0,
                                   AssetDistribution([alloc_no]), None)
        with patch('random.gauss', side_effect=list(gauss_values)):
            result_no = retirement_value(rs_no)

        asset_yes = Asset("Stock", 1000, 0.10, 0.01)
        alloc_yes = AssetAllocation(asset_yes, 0, 0, 0)
        rs_yes = RetirementSettings(100, (0.02, 0.0), 2, 0,
                                    AssetDistribution([alloc_yes]), 0.5)
        with patch('random.gauss', side_effect=list(gauss_values)):
            result_yes = retirement_value(rs_yes)

        self.assertGreater(result_yes.current_value(),
                           result_no.current_value())

    @staticmethod
    def _two_asset_rs(frac):
        # Equal-weight, equal-mean assets so the portfolio mean is 0.10.
        return RetirementSettings(
            100, (0.02, 0.0), 2, 0,
            AssetDistribution([
                AssetAllocation(Asset("First", 1000, 0.10, 0.01), 0, 0, 0),
                AssetAllocation(Asset("Last", 1000, 0.10, 0.01), 0, 0, 0),
            ]), frac)

    def test_expenditure_reduction_portfolio_underperforms(self):
        # Both assets return below their mean, so the portfolio underperforms
        # and next year's expenditure is reduced.
        # gauss order per year: inflation, First_return, Last_return.
        gauss_values = [
            0.02, 0.05, 0.08,  # year 1: portfolio under 0.10
            0.02, 0.12, 0.12,  # year 2
        ]
        with patch('random.gauss', side_effect=list(gauss_values)):
            result_no = retirement_value(self._two_asset_rs(None))
        with patch('random.gauss', side_effect=list(gauss_values)):
            result_yes = retirement_value(self._two_asset_rs(0.5))

        self.assertGreater(result_yes.current_value(),
                           result_no.current_value())

    def test_expenditure_reduction_portfolio_outperforms(self):
        # One asset underperforms but the other more than compensates, so the
        # overall portfolio beats its mean and no reduction is triggered.
        gauss_values = [
            0.02, 0.05, 0.20,  # year 1: First under, Last over -> portfolio over
            0.02, 0.12, 0.12,  # year 2
        ]
        with patch('random.gauss', side_effect=list(gauss_values)):
            result_no = retirement_value(self._two_asset_rs(None))
        with patch('random.gauss', side_effect=list(gauss_values)):
            result_yes = retirement_value(self._two_asset_rs(0.5))

        # No reduction means the two runs are identical.
        self.assertAlmostEqual(result_yes.current_value(),
                               result_no.current_value())

    def test_negative_expenditure_skips_reduction(self):
        gauss_values = [0.02, 0.05, 0.02, 0.10]

        asset = Asset("Stock", 1000, 0.10, 0.01)
        alloc = AssetAllocation(asset, 0, 0, 0)
        rs = RetirementSettings(-100, (0.02, 0.0), 2, 0,
                                AssetDistribution([alloc]), 0.5)
        with patch('random.gauss', side_effect=list(gauss_values)):
            result = retirement_value(rs)

        self.assertEqual(result.t, 0)


class SimulationTest(unittest.TestCase):
    def test_simulate_count(self):
        random.seed(42)
        asset = Asset("Stock", 1000, 0.05, 0.01)
        alloc = AssetAllocation(asset, 0, 0, 0)
        rs = RetirementSettings(50, (0.02, 0.005), 1, 0,
                                AssetDistribution([alloc]), None)
        results = simulate(rs, 50)
        self.assertEqual(len(results), 50)
        for r in results:
            self.assertIsInstance(r, RetirementSettings)
            self.assertEqual(r.t, 0)

    def test_simulate_varies(self):
        random.seed(42)
        asset = Asset("Stock", 1000, 0.05, 0.01)
        alloc = AssetAllocation(asset, 0, 0, 0)
        rs = RetirementSettings(50, (0.02, 0.005), 5, 0,
                                AssetDistribution([alloc]), None)
        results = simulate(rs, 100)
        values = [r.current_value() for r in results]
        self.assertGreater(len(set(values)), 1)

    def test_worst_case(self):
        def make_rs(value):
            return RetirementSettings(
                0, (0, 0), 0, 0,
                AssetDistribution([
                    AssetAllocation(Asset("A", value, 0, 0), 0, 0, 0)
                ]), None)

        runs = [make_rs(v) for v in [500, 100, 300, 200, 400]]

        result = worst_case(runs, 0.0)
        self.assertAlmostEqual(result.current_value(), 100)

        result = worst_case(runs, 0.2)
        self.assertAlmostEqual(result.current_value(), 200)

        result = worst_case(runs, 0.5)
        self.assertAlmostEqual(result.current_value(), 300)

    def test_worst_case_sorted_input(self):
        def make_rs(value):
            return RetirementSettings(
                0, (0, 0), 0, 0,
                AssetDistribution([
                    AssetAllocation(Asset("A", value, 0, 0), 0, 0, 0)
                ]), None)

        runs = [make_rs(v) for v in [100, 200, 300]]
        result = worst_case(runs, 0.0)
        self.assertAlmostEqual(result.current_value(), 100)


class InflationTest(unittest.TestCase):
    def test_inflated_val_basic(self):
        self.assertAlmostEqual(
            inflated_val(100, 0.05, 10), 100 * (1.05 ** 10))

    def test_inflated_val_zero_rate(self):
        self.assertAlmostEqual(inflated_val(100, 0, 10), 100)

    def test_inflated_val_zero_time(self):
        self.assertAlmostEqual(inflated_val(100, 0.05, 0), 100)

    def test_inflated_payments_zero_rate(self):
        self.assertAlmostEqual(inflated_payments(100, 0, 5), 500)

    def test_inflated_payments_zero_time(self):
        self.assertAlmostEqual(inflated_payments(100, 0.05, 0), 0)

    def test_inflated_payments_known_value(self):
        expected = sum(100 * (1.05 ** i) for i in range(3))
        self.assertAlmostEqual(inflated_payments(100, 0.05, 3), expected)


class InsertAllocTest(unittest.TestCase):
    def test_empty_list(self):
        allocs = []
        new = AssetAllocation(Asset("A", 100, 0, 0), 0, 0, 0)
        insert_alloc_set_priority(new, 0, allocs)
        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs[0].asset.name, "A")
        self.assertEqual(allocs[0].priority, 0)

    def test_same_priority(self):
        allocs = [AssetAllocation(Asset("B", 100, 0, 0), 0, 0, 0)]
        new = AssetAllocation(Asset("A", 100, 0, 0), 0, 0, 0)
        insert_alloc_set_priority(new, 0, allocs)
        self.assertEqual(len(allocs), 2)
        self.assertEqual(allocs[0].asset.name, "B")
        self.assertEqual(allocs[1].asset.name, "A")
        self.assertEqual(allocs[0].priority, 0)
        self.assertEqual(allocs[1].priority, 0)

    def test_before_integer_priority(self):
        allocs = [AssetAllocation(Asset("B", 100, 0, 0), 1, 0, 0)]
        new = AssetAllocation(Asset("A", 100, 0, 0), 0, 0, 0)
        insert_alloc_set_priority(new, 0, allocs)
        self.assertEqual(len(allocs), 2)
        self.assertEqual(allocs[0].asset.name, "A")
        self.assertEqual(allocs[1].asset.name, "B")
        self.assertEqual(allocs[0].priority, 0)
        self.assertEqual(allocs[1].priority, 1)

    def test_before_fractional_priority(self):
        allocs = [AssetAllocation(Asset("B", 100, 0, 0), 1, 0, 0)]
        new = AssetAllocation(Asset("A", 100, 0, 0), 0, 0, 0)
        insert_alloc_set_priority(new, 0.5, allocs)
        self.assertEqual(len(allocs), 2)
        self.assertEqual(allocs[0].asset.name, "A")
        self.assertEqual(allocs[1].asset.name, "B")
        self.assertEqual(allocs[0].priority, 1)
        self.assertEqual(allocs[1].priority, 2)

    def test_between_fractional_priority(self):
        allocs = [
            AssetAllocation(Asset("A", 100, 0, 0), 0, 0, 0),
            AssetAllocation(Asset("C", 100, 0, 0), 2, 0, 0),
        ]
        new = AssetAllocation(Asset("B", 100, 0, 0), 0, 0, 0)
        insert_alloc_set_priority(new, 1.5, allocs)
        self.assertEqual(len(allocs), 3)
        self.assertEqual(allocs[0].asset.name, "A")
        self.assertEqual(allocs[1].asset.name, "B")
        self.assertEqual(allocs[2].asset.name, "C")
        self.assertEqual(allocs[0].priority, 0)
        self.assertEqual(allocs[1].priority, 2)
        self.assertEqual(allocs[2].priority, 3)


class YAMLRoundTripTest(unittest.TestCase):
    def test_save_load_roundtrip(self):
        asset = Asset("Stock", 1000, 0.05, 0.01)
        alloc = AssetAllocation(asset, 0, 100, 0.5)
        rs = RetirementSettings(50000, (0.03, 0.01), 30, 10000,
                                AssetDistribution([alloc]), 0.15)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_scenario.yaml")
            save_retirement_settings(rs, filepath)
            loaded = load_retirement_settings(filepath)
            self.assertEqual(rs, loaded)

    def test_save_load_roundtrip_no_reduction(self):
        asset = Asset("Stock", 500, 0.08, 0.02)
        alloc = AssetAllocation(asset, 0, 0, 0)
        rs = RetirementSettings(25000, (0.02, 0.005), 20, 5000,
                                AssetDistribution([alloc]), None)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_scenario.yaml")
            save_retirement_settings(rs, filepath)
            loaded = load_retirement_settings(filepath)
            self.assertEqual(rs, loaded)
            self.assertIsNone(loaded.expenditure_reduction_frac)
