from enum import Enum
from typing import Any, Callable, List, Optional, Tuple


class AssetSetting(Enum):
    NAME = 1
    VALUE = 2
    MEAN_RETURN = 3
    RETURN_STDEV = 4


class Asset:
    def __init__(self, name: str, value: float, mean_return: float,
                 return_stdev: float):
        self.name: str = name
        self.value: float = value
        self.mean_return: float = mean_return
        self.return_stdev: float = return_stdev

    def copy(self) -> 'Asset':
        return Asset(self.name, self.value, self.mean_return, self.return_stdev)

    def update_val(self, asset_setting: AssetSetting, op: Callable[[Any], Any]):
        if asset_setting == AssetSetting.NAME:
            self.name = op(self.name)
        elif asset_setting == AssetSetting.VALUE:
            self.value = op(self.value)
        elif asset_setting == AssetSetting.MEAN_RETURN:
            self.mean_return = op(self.mean_return)
        elif asset_setting == AssetSetting.RETURN_STDEV:
            self.return_stdev = op(self.return_stdev)

    @staticmethod
    def from_structured(assetObj: dict) -> 'Asset':
        name = assetObj["name"]
        value = assetObj["value"]
        mean_return = assetObj["mean_return"]
        return_stdev = assetObj["return_stdev"]
        return Asset(name, value, mean_return, return_stdev)

    def to_structured(self) -> dict:
        assetObj = {}
        assetObj["name"] = self.name
        assetObj["value"] = self.value
        assetObj["mean_return"] = self.mean_return
        assetObj["return_stdev"] = self.return_stdev
        return assetObj

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Asset) and
                self.name == other.name and
                self.value == other.value and
                self.mean_return == other.mean_return and
                self.return_stdev == other.return_stdev)

    def __hash__(self) -> int:
        return hash((self.name,
                     self.value,
                     self.mean_return,
                     self.return_stdev))


class AllocationSetting(Enum):
    ASSET = 1
    PRIORITY = 2
    MINIMUM_VALUE = 3
    DESIRED_FRACTION_OF_TOTAL_ASSETS = 4


class AllocationValue:
    def __init__(self, allocation_setting, asset_setting=Optional[AssetSetting]):
        self.allocation_setting = allocation_setting
        self.asset_setting = asset_setting


class AssetAllocation:
    def __init__(self, asset: Asset, priority: int, minimum_value: float,
                 desired_fraction_of_total_assets: float):
        self.asset = asset
        # Lower priority numbers have greater priority
        self.priority = priority
        self.minimum_value = minimum_value
        assert 0 <= desired_fraction_of_total_assets <= 1
        self.desired_fraction_of_total_assets = \
            desired_fraction_of_total_assets

    def copy(self) -> 'AssetAllocation':
        return AssetAllocation(self.asset.copy(), self.priority, self.minimum_value,
                               self.desired_fraction_of_total_assets)

    def update_val(self, avalue: AllocationValue, op: Callable[[Any], Any]):
        asetting = avalue.allocation_setting
        if asetting == AllocationSetting.ASSET:
            if avalue.asset_setting is None:
                self.asset = op(self.asset)
            else:
                self.asset.update_val(avalue.asset_setting, op)  # type: ignore
        elif asetting == AllocationSetting.PRIORITY:
            self.priority = op(self.priority)
        elif asetting == AllocationSetting.MINIMUM_VALUE:
            self.minimum_value = op(self.minimum_value)
        elif asetting == AllocationSetting.DESIRED_FRACTION_OF_TOTAL_ASSETS:
            self.desired_fraction_of_total_assets = op(
                self.desired_fraction_of_total_assets)

    @staticmethod
    def from_structured(alloc_obj: dict) -> 'AssetAllocation':
        asset = Asset.from_structured(alloc_obj["asset"])
        priority = alloc_obj["priority"]
        minimum_value = alloc_obj["minimum_value"]
        if "desired_fraction_of_total_assets" in alloc_obj:
            desired_fraction_of_total_assets = alloc_obj["desired_fraction_of_total_assets"]
        else:
            desired_fraction_of_total_assets = alloc_obj["preferred_fraction_of_priority_class"]
        return AssetAllocation(asset, priority, minimum_value, desired_fraction_of_total_assets)

    def to_structured(self) -> dict:
        alloc_obj = {}
        alloc_obj["asset"] = self.asset.to_structured()
        alloc_obj["priority"] = self.priority
        alloc_obj["minimum_value"] = self.minimum_value
        alloc_obj["desired_fraction_of_total_assets"] = \
            self.desired_fraction_of_total_assets
        return alloc_obj

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, AssetAllocation) and
                self.asset == other.asset and
                self.priority == other.priority and
                self.minimum_value == other.minimum_value and
                self.desired_fraction_of_total_assets ==
                    other.desired_fraction_of_total_assets)

    def __hash__(self) -> int:
        return hash((self.asset,
                     self.priority,
                     self.minimum_value,
                     self.desired_fraction_of_total_assets))


class DistributionSetting(Enum):
    ASSET_ALLOCATIONS = 1


class DistributionValue:
    def __init__(self, distribution_setting: DistributionSetting, allocation_value: Optional[Tuple[int, AllocationValue]] = None):
        self.distribution_setting = distribution_setting
        self.allocation_value = allocation_value


class AssetDistribution:
    def __init__(self, asset_allocations: List[AssetAllocation]):
        asset_allocations.sort(key=lambda a: a.priority)
        self.asset_allocations = asset_allocations

    def update_val(self, dvalue: DistributionValue, op: Callable[[Any], Any]):
        dsetting = dvalue.distribution_setting
        if dsetting == DistributionSetting.ASSET_ALLOCATIONS:
            if dvalue.allocation_value is None:
                self.asset_allocations = op(self.asset_allocations)
            else:
                index, avalue = dvalue.allocation_value
                self.asset_allocations[index].update_val(avalue, op)

    def copy(self) -> 'AssetDistribution':
        return AssetDistribution([aa.copy() for aa in self.asset_allocations])

    @staticmethod
    def from_structured(distribution_obj: dict) -> 'AssetDistribution':
        asset_allocations = [AssetAllocation.from_structured(
            aa) for aa in distribution_obj["asset_allocations"]]
        return AssetDistribution(asset_allocations)

    def to_structured(self) -> dict:
        distribution_obj = {}
        distribution_obj["asset_allocations"] = [
            aa.to_structured() for aa in self.asset_allocations]
        return distribution_obj

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, AssetDistribution) and
                set(self.asset_allocations) == set(other.asset_allocations))

    def __hash__(self) -> int:
        return hash(frozenset(self.asset_allocations))

    def current_value(self) -> float:
        return sum([aa.asset.value for aa in self.asset_allocations])


class RSetting(Enum):
    EXPENDATURE = 1
    INFLATION = 5
    T = 7
    EMERGENCY_MIN = 8
    ASSET_DISTRIBUTION = 9


class RValue:
    def __init__(self, rsetting: RSetting, dvalue: Optional[DistributionValue] = None):
        self.rsetting = rsetting
        self.dvalue = dvalue


class RetirementSettings:
    def __init__(self, expendature: float, inflation: Tuple[float, float],
                 t: int, emergency_min: float,
                 asset_distribution: AssetDistribution):
        self.expendature = expendature
        self.inflation = inflation
        self.t = t
        self.emergency_min = emergency_min
        self.asset_distribution = asset_distribution

    def update_val(self, rvalue: RValue, op: Callable[[Any], Any]) -> None:
        rsetting = rvalue.rsetting
        if rsetting == RSetting.EXPENDATURE:
            self.expendature = op(self.expendature)
        elif rsetting == RSetting.INFLATION:
            self.inflation = op(self.inflation)
        elif rsetting == RSetting.T:
            self.t = op(self.t)
        elif rsetting == RSetting.EMERGENCY_MIN:
            self.emergency_min = op(self.emergency_min)
        elif rsetting == RSetting.ASSET_DISTRIBUTION:
            if rvalue.dvalue is None:
                self.asset_distribution = op(self.asset_distribution)
            else:
                self.asset_distribution.update_val(rvalue.dvalue, op)

    def get_val(self, rsetting: RSetting) -> Any:
        if rsetting == RSetting.EXPENDATURE:
            return self.expendature
        elif rsetting == RSetting.INFLATION:
            return self.inflation
        elif rsetting == RSetting.T:
            return self.t
        elif rsetting == RSetting.EMERGENCY_MIN:
            return self.emergency_min
        elif rsetting == RSetting.ASSET_DISTRIBUTION:
            return self.asset_distribution

    def current_value(self) -> float:
        return self.asset_distribution.current_value()

    def copy(self) -> 'RetirementSettings':
        return RetirementSettings(self.expendature, self.inflation, self.t,
                                  self.emergency_min,
                                  self.asset_distribution.copy())

    @staticmethod
    def from_structured(ret_obj: dict) -> 'RetirementSettings':
        expendature = ret_obj["expendature"]
        inflation = tuple(ret_obj["inflation"])
        t = ret_obj["t"]
        emergency_min = ret_obj["emergency_min"]
        if "asset_distribution" in ret_obj:
            asset_distribution = AssetDistribution.from_structured(
                ret_obj["asset_distribution"])
        else:  # legacy
            asset_allocations = [AssetAllocation.from_structured(aa)
                                 for aa in ret_obj["asset_allocations"]]
            asset_distribution = AssetDistribution(asset_allocations)
        return RetirementSettings(
            expendature, inflation, t, emergency_min, asset_distribution)

    def to_structured(self) -> dict:
        ret_obj = {}
        ret_obj["expendature"] = self.expendature
        ret_obj["inflation"] = list(self.inflation)
        ret_obj["t"] = self.t
        ret_obj["emergency_min"] = self.emergency_min
        ret_obj["asset_distribution"] = self.asset_distribution.to_structured()
        return ret_obj

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, RetirementSettings) and
                self.expendature == other.expendature and
                self.inflation == other.inflation and
                self.t == other.t and
                self.emergency_min == other.emergency_min and
                self.asset_distribution == other.asset_distribution)

    def __hash__(self) -> int:
        return hash((self.expendature,
                     self.inflation,
                     self.t,
                     self.emergency_min,
                     self.asset_distribution))
