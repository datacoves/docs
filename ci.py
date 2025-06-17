#!/usr/bin/env python3

import os
import sys

from lib import cmd
from scripts import installer, k8s_utils, setup_core, setup_operator

CLUSTER_DOMAIN = "datacoveslocal.com"


def install():
    """Install datacoves in a cluster."""
    os.environ["CI_RUNNING"] = "true"
    k8s_utils.set_context("kind-datacoves-cluster")
    setup_operator.setup_operator(CLUSTER_DOMAIN)
    setup_core.setup_core(CLUSTER_DOMAIN)
    installer.retry_helm_charts(prompt=False)


if __name__ == "__main__":
    program_name, *args = sys.argv

    # Run from the directory that contains this script.
    os.chdir(os.path.dirname(program_name))
    cmd.main()
