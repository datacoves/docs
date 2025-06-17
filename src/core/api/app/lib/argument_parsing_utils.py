# Argument parsing utils


def parse_release(release):
    return remove_suffix(remove_prefix_dir(release, "releases/"), ".yaml")


def parse_cluster_domain(cluster_domain):
    return remove_suffix(remove_prefix_dir(cluster_domain, "config/"), "/")


def parse_image_path(image_path):
    return remove_suffix(remove_prefix_dir(image_path, "src/"), "/")


def remove_prefix_dir(s, prefix_dir):
    return remove_prefix(remove_prefix(s, "./"), prefix_dir)


def remove_prefix(s, prefix):
    if s.startswith(prefix):
        s = s[len(prefix) :]
    return s


def remove_suffix(s, suffix):
    if s.endswith(suffix):
        s = s[: -len(suffix)]
    return s
