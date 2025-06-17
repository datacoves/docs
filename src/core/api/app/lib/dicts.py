from copy import deepcopy


def deep_merge(new_values, default_values):
    """Merge new values into default values dict, overrding existing values"""

    def merge(source, destination):
        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination.setdefault(key, {})
                merge(value, node)
            else:
                destination[key] = value
        return destination

    default = deepcopy(default_values)
    return merge(new_values, default)


def pick_fields(model_class, data):
    from django.core.exceptions import FieldDoesNotExist

    d = {}
    for k, v in data.items():
        try:
            model_class._meta.get_field(k)
            d[k] = v
        except FieldDoesNotExist:
            pass
    return d


def set_in(d, path, val):
    """
    Given a dict, path and value, modifies the dict and creates the needed
    dicts based on path to set the value properly
    """
    for i in range(len(path) - 1):
        d = d.setdefault(path[i], {})
    d[path[-1]] = val


def pick_dict(src, subset):
    """Make a dictionary with keys from subset and values from src, or subset."""
    return {k: src.get(k, default) for k, default in subset.items()}
