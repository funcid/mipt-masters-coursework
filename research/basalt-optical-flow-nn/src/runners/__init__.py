"""Optical flow method runners (classical, neural, Basalt stub)."""

from .base import FlowResult, OpticalFlowRunner, RunnerRegistry
from .opencv_farneback import OpenCVFarnebackRunner
from .opencv_lk import OpenCVLucasKanadeRunner
from .opencv_dis import OpenCVDISRunner
from .raft import RaftRunner
from .sea_raft import SeaRaftRunner
from .gmflow_runner import GMFlowRunner
from .raft_stub import RaftStubRunner
from .basalt_se2 import BasaltSE2Runner

__all__ = [
    "FlowResult",
    "OpticalFlowRunner",
    "RunnerRegistry",
    "OpenCVFarnebackRunner",
    "OpenCVLucasKanadeRunner",
    "OpenCVDISRunner",
    "RaftRunner",
    "SeaRaftRunner",
    "GMFlowRunner",
    "RaftStubRunner",
    "BasaltSE2Runner",
]


def build_default_registry() -> RunnerRegistry:
    registry = RunnerRegistry()
    registry.register("opencv_lk", OpenCVLucasKanadeRunner)
    registry.register("opencv_farneback", OpenCVFarnebackRunner)
    registry.register("opencv_dis", OpenCVDISRunner)
    registry.register("raft", RaftRunner)
    registry.register("sea_raft", SeaRaftRunner)
    registry.register("gmflow", GMFlowRunner)
    registry.register("flowformer", RaftStubRunner)
    registry.register("liteflownet", RaftStubRunner)
    registry.register("fastflownet", RaftStubRunner)
    registry.register("basalt_se2", BasaltSE2Runner)
    return registry
