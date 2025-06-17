"""
Simple python metaprogramming by convention.

You write:
    {module_name}_generator.py  (a program that generates {module_name}.py)
    {module_name}_template.py   (optional, input code to the generator)

Running {module_name}_generator.py generates {module_name}.py.

Generator scaffold:

```python
from lib import gen

def generate():
    # A dict mapping fragment names to strings that will be spliced into {module_name}_template.py
    fragments = {}

    # YOUR CODE HERE.

    return fragments

if __name__ == "__main__":
    gen.render(gen.output_path(__file__), generate())
```

Where the template has comments of the form `# gen: {fragment_name}` gen.render
will insert the strings in the fragments dictionary.
"""

GENERATOR_SUFFIX = "_generator.py"
TEMPLATE_SUFFIX = "_template.py"


def prefix(file):
    if file.endswith(GENERATOR_SUFFIX):
        return file[: -len(GENERATOR_SUFFIX)]
    elif file.endswith(TEMPLATE_SUFFIX):
        return file[: -len(TEMPLATE_SUFFIX)]
    elif file.endswith(".py"):
        return file[: -len(".py")]
    else:
        return file


def generator_path(file):
    return prefix(file) + GENERATOR_SUFFIX


def template_path(file):
    return prefix(file) + TEMPLATE_SUFFIX


def output_path(file):
    return prefix(file) + ".py"


def render(file, fragments):
    path_out = output_path(file)
    path_templ = template_path(file)
    template = ""
    with open(path_templ, "r") as template_file:
        template = template_file.read()
    if template.startswith("raise"):
        template = template[template.index("\n") + 1 :]
    # NOTE: quick and dirty...
    for fragment_name, fragment in sorted(fragments.items()):
        template = template.replace(f"# gen: {fragment_name}", fragment)
    with open(path_out, "w+") as output_file:
        print(template, file=output_file)


def emitter(fragments, fragment_name):
    """Returns a print like function that prints to fragments[fragment_name]."""
    fragments[fragment_name] = ""

    def emit(*args, end="\n"):
        fragments[fragment_name] += " ".join(args) + end

    return emit
