from projects.models import Environment


def create_filesystem(env: Environment):
    provisioner = env.cluster.efs_provisioner
    global_efs = provisioner.get("global")
    if not global_efs:
        raise NotImplementedError(
            "Dynamic creation of EFS filesystems not implemented yet."
        )
    return global_efs
