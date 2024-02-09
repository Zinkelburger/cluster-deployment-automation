from clustersConfig import ClustersConfig
import host
import coreosBuilder
from concurrent.futures import ThreadPoolExecutor
from k8sClient import K8sClient
from nfs import NFS
from concurrent.futures import Future
from typing import Dict
import sys
from logger import logger
from clustersConfig import ExtraConfigArgs

"""
The "ExtraConfigCX" is used to put the CX in a known good state. This is achieved by
1) Having a CoreOS Fedora image ready and mounted on NFS. This is needed for loading
a known good state on each of the workers.
2) The scripts will try to update the firmware of the CX with mlxup.
3) Then the worker node is cold booted. This will also cold boot the CX.
"""


def ExtraConfigCX(cc: ClustersConfig, _: ExtraConfigArgs, futures: Dict[str, Future[None]]) -> None:
    logger.info("Updating CX firmware on all workers")

    def helper(h: host.HostWithCX) -> None:
        def check(result: host.Result) -> None:
            if result.returncode != 0:
                logger.info(result)
                sys.exit(-1)

        check(h.cx_firmware_upgrade())
        h.cold_boot()

    executor = ThreadPoolExecutor(max_workers=len(cc.workers))
    # Assuming all workers have CX that need to update their firmware
    for e in cc.workers:
        h = host.HostWithCX(e.node)
        futures[e.name].result()
        f = executor.submit(helper, h)
        futures[e.name] = f
    logger.info("CX setup complete")
