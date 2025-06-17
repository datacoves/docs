def dockerfile_to_python(filename):
    with open(filename, "r") as f:
        lines = (l.strip() for l in f.readlines())
        lines = [l for l in lines if l]
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("#"):
                print("    " + line)
                i += 1
                continue
            directive = []
            while line.endswith("\\"):
                directive.append(line[:-1])
                i += 1
                line = lines[i]
            directive.append(line)
            op, directive[0] = directive[0].split(maxsplit=1)
            args = map(repr, directive)
            args = map(lambda x: x if len(x) + 8 < 120 else f"{x}  #noqa E501", args)
            argstr = "\n        ".join(args)
            print(f"    d.{op}({argstr})")
            i += 1
