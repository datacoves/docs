import json
from typing import NamedTuple

import questionary

from scripts.k8s_utils import kubectl, kubectl_output


class PV(NamedTuple):
    name: str
    phase: str
    volume_id: str
    volume_region: str
    pvc_namespace: str
    pvc_name: str

    @classmethod
    def fromk8s(cls, v):
        name = v["metadata"]["name"]
        phase = v.get("status", {}).get("phase")
        spec = v["spec"]
        volume_id = spec.get("awsElasticBlockStore", {}).get("volumeID", "")
        volume_region = (
            volume_id[len("aws://") :].split("/")[0]
            if volume_id.startswith("aws://")
            else ""
        )
        claim = spec.get("claimRef", {})
        pvc_namespace = claim.get("namespace")
        pvc_name = claim.get("name")
        return PV(
            name=name,
            phase=phase,
            volume_id=volume_id,
            volume_region=volume_region,
            pvc_name=pvc_name,
            pvc_namespace=pvc_namespace,
        )


def get_pvs_raw():
    return json.loads(kubectl_output("get pv -o json"))["items"]


def get_pvs():
    return [PV.fromk8s(v) for v in get_pvs_raw()]


def delete_released_pvs():
    pvs = get_pvs()
    for pv in pvs:
        if pv.phase == "Released":
            print(pv)
            if questionary.confirm("Delete PV?").ask():
                kubectl("delete pv", pv.name)
