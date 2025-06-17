"""Compiles a "merged" release notes file further down into basic notes
for end users with grouped sections.

Arguments: input file, output file

Can be used as a library or as a command line.
"""

import re
import sys


def merge_notes(inputfile: str, outputfile: str):
    """Takes an input file and writes it to output file.  The input file
    looks for release notes in a format such as:

    **Header**

    - Some
    - Notes
    - Like
    - This
    * OR
    * With
    * Stars

    **Another Header**

    - more
    - notes

    It merges headers and notes and provides a combined file.  It is
    smart enough that the capitalization of the headers doesn't matter.

    It removes lines that start with '# Release' and '**Full Changelog**'
    and also cleans out a lot of blank lines.

    Any text found before the first header (asside from the filtered text
    above) is included at the top of the file.  Any text found between
    sections will probably wind up injected in one of the sections in a
    slightly undetermined behavior.
    """

    notes = None

    with open(inputfile, "rt") as input:
        notes = input.read()

    # Matcher for sections:
    section_re = re.compile(r"^[*][*]([\w\d\s]+)[*][*][\s]*$")  # noqa

    # Section groups
    #
    # Blank section is for lines that will appear at the top of the file.
    sections = {"": []}

    # What section are we in
    current_section = ""

    for line in notes.split("\n"):
        # Skip changelog lines and release lines
        if line.lower().startswith("**full changelog**") or line.startswith(
            "# Release"
        ):
            continue

        matches = section_re.match(line)
        if matches:
            current_section = matches.group(1).lower().title()

            if current_section not in sections:
                sections[current_section] = []

        elif line:
            # Standardize on - vs *
            if line[0] == "-":
                line = f"*{line[1:]}"

            sections[current_section].append(line)

    # Write output
    with open(outputfile, "wt") as output:
        for line in sections[""]:
            output.write(line)
            output.write("\n")

        # Get rid of the blank section after writing it out, so that we
        # don't write it out again.
        del sections[""]

        for section, lines in sections.items():
            output.write("\n")
            output.write(f"**{section}**")
            output.write("\n\n")

            for line in lines:
                output.write(line)
                output.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Syntax: inputfile outputfile")
        sys.exit(-1)

    merge_notes(sys.argv[1], sys.argv[2])
