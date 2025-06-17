import re
import subprocess

from lib import cmd

kube_context = None


def set_context(ctx):
    global kube_context
    assert type(ctx) is str
    kube_context = ctx


def get_context():
    assert kube_context is not None
    return kube_context


def make_kcmd(cmd_func, exec, ctx_flag):
    def kcmd(command, *args, **kwargs):
        assert kube_context, "k8s_utils.set_context not called"
        if isinstance(command, str):
            return cmd_func(
                f"{exec} {ctx_flag} {kube_context} {command}", *args, **kwargs
            )
        else:
            _cmd = [exec, ctx_flag, kube_context] + command
            return cmd_func(_cmd, *args, **kwargs)

    return kcmd


kubectl = make_kcmd(cmd.run, "kubectl", "--context")
helm = make_kcmd(cmd.run, "helm", "--kube-context")
kubectl_output = make_kcmd(cmd.output, "kubectl", "--context")
helm_output = make_kcmd(cmd.output, "helm", "--kube-context")


def exists_resource(ns, resource, name) -> bool:
    try:
        kubectl_output(f"get -n {ns} {resource} {name}")
        return True
    except subprocess.CalledProcessError:
        return False


def exists_namespace(ns) -> bool:
    try:
        kubectl_output(f"get namespace {ns}")
        return True
    except subprocess.CalledProcessError:
        return False


def create_namespace(ns):
    if not exists_namespace(ns=ns):
        kubectl(f"create namespace {ns}")


def wait_for_deployment(ns, deployment):
    kubectl(f"-n {ns} rollout status deployment/{deployment}")


def wait_for_statefulset(ns, statefulset):
    kubectl(f"-n {ns} rollout status statefulset/{statefulset}")


def pod_for_deployment(ns, deployment):
    return pod_by_label(ns=ns, label=f"app={deployment}")


def pod_by_label(ns, label):
    o = kubectl_output(f"-n {ns} get pods -l {label}")
    lines = o.split("\n")[1:]
    for l in lines:
        cols = l.split()
        if len(cols) < 2:
            continue
        status = cols[2]
        name = cols[0]
        if status != "Running":
            continue
        return name
    return None


def get_deployments(ns):
    o = kubectl_output(f"-n {ns} get deployments")
    lines = o.split("\n")[1:]
    deploys = []
    for l in lines:
        if l:
            cols = l.split()
            deploys.append(cols[0])  # name

    return deploys


def get_hpas(ns):
    o = kubectl_output(f"-n {ns} get hpa")
    lines = o.split("\n")[1:]
    hpas = []
    for l in lines:
        if l:
            cols = l.split()
            hpas.append(cols[0])  # name

    return hpas


def namespace_release(ns):
    "Returns current datacoves release of a namespace (either core or an environment)"
    o = kubectl_output(f"describe ns {ns}")
    release = re.search(r"k8s\.datacoves\.com\/release=([\w\.\-]+)", o)
    if release:
        return release.group(1)
    return None


def get_env_namespaces():
    "Returns current datacoves release of a namespace (either core or an environment)"
    o = kubectl_output("get ns --selector=k8s.datacoves.com/environment-type")
    return re.findall(r"(dcw\-\w+)", o)


def cmd_runner_in_pod(ns, pod, container=None, capture_output=False):
    def run(command, *args, **kwargs):
        container_cmd = f"--container {container}" if container else ""
        if isinstance(command, str):
            _cmd = f"-n {ns} exec -it {pod} {container_cmd} -- {command}"
        else:
            _cmd = ["-n", ns, "exec", "-it", pod, "--"] + command

        if capture_output:
            return kubectl_output(_cmd, *args, **kwargs)
        return kubectl(_cmd, *args, **kwargs)

    return run


def service_port(port=80, target_port=80, protocol="TCP"):
    return {"protocol": protocol, "port": port, "targetPort": target_port}


def gen_service(name, ports=None, port=80, target_port=80, protocol="TCP"):
    if not ports:
        ports = [service_port(port=port, target_port=target_port, protocol=protocol)]
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-svc",
        },
        "spec": {
            "selector": {
                "app": name,
            },
            "ports": ports,
        },
    }


def k8s_env(env):
    return [{"name": name, "value": value} for name, value in env.items()]


def k8s_env_from_config_map(config_map_name, vars):
    if isinstance(vars, dict):
        return [
            {
                "name": k,
                "valueFrom": {"configMapKeyRef": {"key": v, "name": config_map_name}},
            }
            for k, v in vars.items()
        ]
    else:
        return [
            {
                "name": v,
                "valueFrom": {"configMapKeyRef": {"key": v, "name": config_map_name}},
            }
            for v in vars
        ]


def k8s_env_from_secret(secret_name, vars):
    if isinstance(vars, dict):
        return [
            {
                "name": k,
                "valueFrom": {"secretKeyRef": {"key": v, "name": secret_name}},
            }
            for k, v in vars.items()
        ]
    else:
        return [
            {
                "name": v,
                "valueFrom": {"secretKeyRef": {"key": v, "name": secret_name}},
            }
            for v in vars
        ]
