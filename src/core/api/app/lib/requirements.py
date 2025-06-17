# Why do we need to do this ourselves? I tried to find a library that would do it
# and pypa/packaging comes close but can't tell when two requirements are incompatible.
# We'd like to do that check before trying to run pip, to tell the user right away.
# https://github.com/pypa/packaging/issues/598
from math import inf, isfinite

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet


def merge_requirement_lines(a, b):
    if not a and not b:
        return []
    if not a:
        return b
    if not b:
        return a
    return map(str, merge_requirement_lists(map(Requirement, a), map(Requirement, b)))


def merge_requirement_lists(a, b):
    merged = {r.name: r for r in a}
    for r in b:
        merged[r.name] = (
            merge_requirements(merged[r.name], r) if r.name in merged else r
        )
    return merged.values()


def merge_requirements(a: Requirement, b: Requirement):
    assert a.name == b.name, "cannot merge requirements with different names"
    merged = Requirement(str(a))
    try:
        merged.specifier = merge_specifier_sets(a.specifier, b.specifier)
    except NotImplementedError:
        merged.specifier = a.specifier & b.specifier
    merged.extras = a.extras | b.extras
    assert not (a.url and b.url and a.url != b.url), "cannot merge urls"
    merged.url = a.url or b.url
    if a.marker and b.marker:
        merged.marker = Marker(f"{a.marker} and {b.marker}")
    else:
        merged.marker = a.marker or b.marker
    return merged


def merge_specifier_sets(a: SpecifierSet, b: SpecifierSet):
    # https://peps.python.org/pep-0440/#version-specifiers
    # TODO: What are prereleases? Do we need the fallback or can we handle them too?
    if any(s.prereleases for s in a) or any(s.prereleases for s in b):
        raise NotImplementedError()
    intervals = list(map(specifier_to_interval, a)) + list(
        map(specifier_to_interval, b)
    )
    if not intervals:
        return a  # There are no constraints, return one of the inputs, must be empty.
    merged_interval = ((-inf,), (inf,))
    for interval in intervals:
        merged_interval, interval = promote_intervals(merged_interval, interval)
        merged_interval = interval_intersection(merged_interval, interval)
        assert merged_interval, "cannot merge version specifiers"
    return SpecifierSet(interval_to_specifier_str(merged_interval))


def interval_to_specifier_str(interval):
    a, b = interval
    if a == b:
        return f"=={version_tuple_to_version_str(a)}"
    elif is_top(b):
        return f">={version_tuple_to_version_str(a)}"
    elif is_bottom(a):
        return f"<{version_tuple_to_version_str(b)}"
    elif not is_finite(a):
        raise NotImplementedError()
    elif is_finite(b):
        return f">={version_tuple_to_version_str(a)},<{version_tuple_to_version_str(b)}"
    else:  # a is finite, b is not
        b = _remove_infs(b)
        if len(a) >= 2:
            major, minor, *_ = a
            if b == (major, minor):
                return f"~={version_tuple_to_version_str(a)}"
        b = next_version(b)
        return f">={version_tuple_to_version_str(a)},<{version_tuple_to_version_str(b)}"


def _remove_infs(b):
    b = list(b)
    while len(b) > 0 and b[-1] == inf:
        b.pop()
    return tuple(b)


def is_finite(a):
    return all(map(isfinite, a))


def is_bottom(a):
    return a[0] == -inf


def is_top(b):
    return b[0] == inf


def version_tuple_to_version_str(v):
    return ".".join([str(i) for i in v if i not in (-inf, inf)])


def specifier_to_interval(s):
    """Convert a version specifier to an interval [a, b), represented as a tuple."""
    try:
        version = version_str_to_tuple(s.version)
    except ValueError:
        raise NotImplementedError()

    l = len(version)
    a, b = promote_min_version((-inf,), l), promote_max_version((inf,), l)

    if s.operator == "==":
        a = version
        b = version
    elif s.operator == ">=":
        a = version
    elif s.operator == ">":
        a = next_version(version)
    elif s.operator == "<":
        b = version
    elif s.operator == "<=":
        b = next_version(version)
    elif s.operator == "~=":
        a = version
        major, minor, *_ = version
        b = promote_max_version((major, minor), len(a))
    else:
        raise NotImplementedError()  # unsupported operators: "!=", "==="

    assert len(a) == len(b)
    return (a, b)


def version_str_to_tuple(version: str):
    v = tuple(map(int, version.split(".")))
    for i in v:
        if i < 0:
            raise ValueError()
    return v


def next_version(version):
    version = list(version)
    version[-1] += 1
    return tuple(version)


def promote_min_version(a, l):
    return tuple(list(a) + [-inf] * (l - len(a)))


def promote_max_version(b, l):
    return tuple(list(b) + [inf] * (l - len(b)))


def promote_intervals(x, y):
    l = max(len(x[0]), len(y[0]))
    return promote_interval(x, l), promote_interval(y, l)


def promote_interval(x, l):
    xa, xb = x
    if len(xa) == l and len(xb) == l:
        return x
    return (promote_min_version(xa, l), promote_max_version(xb, l))


def interval_intersection(x, y):
    assert len(x) == len(y)
    xa, xb = x
    ya, yb = y
    if xb < ya or yb < xa:
        return tuple()
    return (max(xa, ya), min(xb, yb))


def write_requirements(dir, reqs):
    with open(dir / "requirements.txt", "w+") as f:
        f.write("\n".join(map(str, reqs)))
