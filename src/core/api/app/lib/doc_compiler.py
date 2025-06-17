"""
The purpose of this is to 'compile' a set of docsify-laid out pages into
a static HTML version.  This script takes two parameters; an input and an
output.  The input should be the root directory path of the docsify project.
The output will be a directory path where we will output the completed files.
"""

import os
import re
import shutil
import xml.etree.ElementTree as etree

import markdown
from bs4 import BeautifulSoup
from markdown.blockprocessors import BlockQuoteProcessor
from markdown.extensions import Extension
from markdown.extensions.codehilite import CodeHiliteExtension
from pygments.formatters import HtmlFormatter

DATACOVES_DOCS_URL = "https://docs.datacoves.com"


class BlockQuoteWithAttributes(BlockQuoteProcessor):
    """This adds the [!TIP], [!WARNING], etc. support to blockquotes"""

    # For alert types
    RE_ALERTS = re.compile(r"^\[!(TIP|WARNING|NOTE|ATTENTION)\]")

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        block = blocks.pop(0)
        m = self.RE.search(block)

        # We need an 'alert_type' variable in here for alert support
        # It can be tip, note, warning, or attention (or blank)
        alert_type = ""

        if m:
            before = block[: m.start()]  # Lines before blockquote

            # Pass lines before blockquote in recursively for parsing first.
            self.parser.parseBlocks(parent, [before])

            # Remove `> ` from beginning of each line.
            block = "\n".join(
                [self.clean(line) for line in block[m.start() :].split("\n")]
            )

            type_match = self.RE_ALERTS.search(block)

            if type_match:
                alert_type = type_match.group(1).lower()
                block = block[len(type_match.group(0)) :]

        sibling = self.lastChild(parent)

        if sibling is not None and sibling.tag == "blockquote":
            # Previous block was a blockquote so set that as this blocks parent
            quote = sibling

        else:
            # Add attributes as needed
            attributes = {}

            if alert_type:
                attributes["class"] = "alert callout " + alert_type

            # This is a new blockquote. Create a new parent element.
            quote = etree.SubElement(parent, "blockquote", attrib=attributes)

            # Add our <p> title tag if we need it
            if alert_type:
                title = etree.SubElement(
                    quote,
                    "p",
                    attrib={
                        "class": "title",
                    },
                )

                # add our little span
                span = etree.SubElement(
                    title, "span", attrib={"class": f"icon icon-{alert_type}"}
                )

                span.tail = alert_type[0].upper() + alert_type[1:]

        # Recursively parse block with blockquote as parent.
        # change parser state so blockquotes embedded in lists use `p` tags
        self.parser.state.set("blockquote")
        self.parser.parseChunk(quote, block)
        self.parser.state.reset()


class DocsifyMarkdownExtension(Extension):
    """To make an extension for markdown"""

    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(
            BlockQuoteWithAttributes(md.parser), "quote", 100
        )


class DocsifyCodeCustomFormatter(HtmlFormatter):
    """This makes Python Markdown's code blocks conform to the layout that
    docsify uses (and thus the CSS wants)"""

    def __init__(self, lang_str="", **options):
        super().__init__(**options)

        # lang_str has the value {lang_prefix}{lang}
        # specified by the CodeHilite's options
        self.lang_str = lang_str

    def _wrap_code(self, source):
        yield 0, f'<code class="{self.lang_str}">'
        yield from source
        yield 0, "</code>"


class DocsifyTemplate:
    """A basic class to handle a docsify template"""

    def __init__(self, base_dir: str, template_name: str = "index.template.html"):
        """Read in a template from a given base directory and set it up
        as a compiled Docsify Template
        """

        self.base_dir = base_dir
        self.template_body = ""

        with open(f"{base_dir}/{template_name}", "rt") as input:
            self.template_body = input.read()

        self.template_body = self.handle_injects(self.template_body)

    def load_and_parse_md(self, md_file: str) -> str:
        """Load a markdown file and convert it to HTML.  Return the HTML."""

        with open(f"{md_file}", "rt") as input:
            return markdown.markdown(
                input.read(),
                tab_length=2,
                extensions=[
                    "extra",
                    DocsifyMarkdownExtension(),
                    CodeHiliteExtension(pygments_formatter=DocsifyCodeCustomFormatter),
                ],
            )

    def handle_injects(self, template: str) -> str:
        """Handles @inject(filename) style tokens)"""

        next_pieces = None
        pieces = template.split("@inject(", 1)
        ret = pieces[0]

        while len(pieces) > 1:
            next_pieces = pieces[1].split(")", 1)

            if len(next_pieces) != 2:
                raise RuntimeError("Unmatched paren with an @inject tag")

            # next_pieces 0 will be the file to load, next_pieces 1 is
            # the remainder of the file

            # Inject it
            ret += self.load_and_parse_md(f"{self.base_dir}/{next_pieces[0]}")

            # Find our next inject
            pieces = next_pieces[1].split("@inject(", 1)
            ret += pieces[0]

        return ret

    def render(self, md_file: str) -> str:
        """Renders a markdown file 'md_file' in the template, which replaces
        the @content tag
        """

        content = self.load_and_parse_md(md_file)
        content = self.template_body.replace("@content", content)

        # Turn '@datacoves.com' into links
        matches = re.findall(r"\w+@datacoves.com", content)
        already_replaced = set()

        for email in matches:
            if email not in already_replaced:
                content = content.replace(
                    email, f'<a href="mailto:{email}">{email}</a>'
                )

                already_replaced.add(email)

        # Do manipulations in beautifulsoup
        html = BeautifulSoup(content, "html.parser")

        # Fix any links that start with / and end in .md
        for link in html.find_all("a"):
            # Start things with / that need to be started with /
            #
            # Only alter local links -- things that start with http://
            # or https:// we will assume go to logical places and should
            # not be touched.
            if (
                "href" in link.attrs
                and not link["href"].startswith("http://")
                and not link["href"].startswith("https://")
                and not link["href"].startswith("mailto:")
            ):
                # I guess we have an empty URL somewhere
                if not len(link["href"]):
                    continue

                # make it start with /
                if link["href"][0] != "/":
                    link["href"] = "/" + link["href"]

                # Split off the '#' if we have it
                url_and_hash = link["href"].split("#", 1)

                # Convert .md to .html
                if url_and_hash[0].endswith(".md"):
                    url_and_hash[0] = url_and_hash[0][:-2] + "html"

                # Make sure there's an extension if there is nothing
                if url_and_hash[0][-1:] != "/" and "." not in url_and_hash[0]:
                    url_and_hash[0] = url_and_hash[0] + ".html"

                link["href"] = "#".join(url_and_hash)

        # Fix h1, h2, h3, h4, h5, h6 to have names
        for x in range(1, 7):
            for tag in html.find_all(f"h{x}"):
                anchor = html.new_tag("a")
                anchor["name"] = re.sub(
                    r"[^\w\d]+", "-", tag.text.strip().lower()
                ).strip("-")
                tag.insert_before(anchor)

        # Fix pre tag
        for parent_div in html.find_all("div", class_="codehilite"):
            inner_pre = parent_div.find("pre")
            inner_code = inner_pre.find("code")
            inner_pre["class"] = inner_code.attrs.get("class", []) + ["codehilite"]
            inner_pre["data-lang"] = [
                inner_code.attrs.get("class", ["language-"])[0][9:]
            ]

            parent_div.replace_with(inner_pre)

        return html.prettify()


def recursive_process_dirs(
    template: DocsifyTemplate, base_in: str, base_out: str, static_collector: list
):
    """For each file in directory base_in, process in the following fashion:
    * Files starting with _ are ignored
    * Files not ending in .md are ignored
    * README.md becomes index.html

    Directories are created in base_out if needed, then entered and
    iterated over.
    """

    for filename in os.listdir(base_in):
        fullpath_in = f"{base_in}/{filename}"
        fullpath_out = f"{base_out}/{filename}"

        if os.path.isdir(fullpath_in):
            if not os.path.isdir(fullpath_out):
                os.makedirs(fullpath_out)

            recursive_process_dirs(
                template, fullpath_in, fullpath_out, static_collector
            )

        elif filename[0] != "_" and filename[-3:] == ".md":
            # If filename is README.md, the destination becomes index.html
            # instead.
            if filename == "README.md":
                fullpath_out = f"{base_out}/index.html"
            else:
                # replace .md with .html
                fullpath_out = fullpath_out[:-2] + "html"

            with open(fullpath_out, "wt") as output:
                output.write(template.render(fullpath_in))
            static_collector.append(fullpath_out)
        elif "assets" in fullpath_in:
            # Copy assets over
            shutil.copyfile(fullpath_in, fullpath_out)


def generate_sitemap_txt(out_dir: str, statics_generated: list[str]):
    """
    Generate a sitemap.txt with all the static pages generated
    Place it in output/robots.txt file
    """
    sitemap_path = f"{out_dir}/sitemap.txt"
    with open(sitemap_path, "w") as sitemap:
        for static in statics_generated:
            sitemap.write(f"{static.replace(out_dir, DATACOVES_DOCS_URL)}\n")
    with open(f"{out_dir}/robots.txt", "w") as robots:
        robots.write(f"Sitemap: {sitemap_path.replace(out_dir, DATACOVES_DOCS_URL)}")


def main(input_base, output_base):
    # Process index.template.html into a template
    template = DocsifyTemplate(input_base)

    # Iterate over directories.
    statics_collector = []
    recursive_process_dirs(template, input_base, output_base, statics_collector)

    generate_sitemap_txt(output_base, statics_collector)
