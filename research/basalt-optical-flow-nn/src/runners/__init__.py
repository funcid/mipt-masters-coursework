"""Optical flow method runners (classical, neural stubs, Basalt)."""

from .base import FlowResult, OpticalFlowRunner, RunnerRegistry
from .opencv_farneback import OpenCVFarnebackRunner
from .opencv_lk import OpenCVLucasKanadeRunner
from .raft import RaftRunner
from .raft_stub import RaftStubRunner
from .basalt_stub import BasaltSE2StubRunner

__all__ = [
    "FlowResult",
    "OpticalFlowRunner",
    "RunnerRegistry",
    "OpenCVFarnebackRunner",
    "OpenCVLucasKanadeRunner",
    "RaftRunner",
    "RaftStubRunner",
    "BasaltSE2StubRunner",
]


def build_default_registry() -> RunnerRegistry:
    registry = RunnerRegistry()
    registry.register("opencv_lk", OpenCVLucasKanadeRunner)
    registry.register("opencv_farneback", OpenCVFarnebackRunner)
    registry.register("raft", RaftRunner)
    registry.register("sea_raft", RaftStubRunner)
    registry.register("gmflow", RaftStubRunner)
    registry.register("flowformer", RaftStubRunner)
    registry.register("liteflownet", RaftStubRunner)
    registry.register("fastflownet", RaftStubRunner)
    registry.register("basalt_se2", BasaltSE2StubRunner)
    return registry
