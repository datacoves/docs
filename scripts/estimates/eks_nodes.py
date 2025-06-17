import json

# INSTANCE SPECS ###############################################################

max_eks_nodes_per_cluster = 2000
max_volume_attachments = 26
max_attachments = 28


# aws ec2 describe-instance-types --filters "Name=instance-type,Values=*" --query "InstanceTypes[]" --output json > ec2-instance-types.json  # noqa
with open("scripts/data/ec2-instance-types.json", "r") as f:
    instance_types = json.load(f)


def max_eni(instance_type):
    return instance_type["NetworkInfo"]["MaximumNetworkInterfaces"]


def max_ips(instance_type):
    return instance_type["NetworkInfo"]["Ipv4AddressesPerInterface"]


def memory_megabytes(instance_type):
    return instance_type["MemoryInfo"]["SizeInMiB"]


# REQUIREMENTS #################################################################


# reqs_per_project = {
#     "airbyte": {
#         "memory_megabytes": 0,
#     },
#     "airflow": {
#         "memory_megabytes": 0,
#     },
#     "workbench": {
#         "memory_megabytes": 0,
#     },
#     "pomerium": {
#         "memory_megabytes": 0,
#     },
#     "superset": {
#         "memory_megabytes": 0,
#     },
#     "prod_dbt_docs": {
#         "memory_megabytes": 0,
#         "elb_volumes": 1,
#     },
# }


reqs_per_user = {
    "code_server": {  # includes dbt_docs in the same pod
        "memory_megabytes": 2048,
        "elb_volumes": 1,
    },
}


def user_pods_per_node(instance_type):
    req_memory = reqs_per_user["code_server"]["memory_megabytes"]
    req_volumes = reqs_per_user["code_server"]["elb_volumes"]
    memory = memory_megabytes(instance_type)
    limit_from_memory = memory // req_memory

    # Not sure if all these attachments are always used, and if I'm interpreting
    # the data and docs correctly. This should be the worst case analysis.
    instance_storage_attachments = sum(
        disk["Count"]
        for disk in instance_type.get("InstanceStorageInfo", {}).get("Disks", [])
    )
    eni_attachments = max_eni(instance_type)

    limit_from_volumes = (
        min(
            max_volume_attachments,
            max_attachments - instance_storage_attachments - eni_attachments,
        )
        // req_volumes
    )

    pods = min(limit_from_memory, limit_from_volumes)

    return pods, limit_from_volumes, limit_from_memory, memory


def eks_instance_type_candidates():
    candidates = []
    for t in instance_types:
        it = t["InstanceType"]

        # filter by prefix for "general purpose" types
        # Alleged prefix naming convention: https://stackoverflow.com/a/60512622
        if it[0].lower() not in ("m", "t"):
            continue
        if it[2] != ".":
            continue
        n, lv, lm, mem = user_pods_per_node(t)
        memory_waste_in_pods = 1
        if n > 0 and (lv <= lm and lm <= lv + memory_waste_in_pods or lm <= lv):
            candidates.append((n, it, lv, lm, mem))
    candidates.sort()
    return candidates
