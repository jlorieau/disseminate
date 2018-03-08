"""
Tags for headings.
"""
from .core import Tag


class Heading(Tag):
    """A heading tag."""
    html_name = None
    tex_name = None
    active = True
    include_paragraphs = False

    def tex(self, level=1, mathmode=False):
        # Add newlines around headings
        tex = super(Heading, self).tex(level, mathmode)
        return "\n" + tex + "\n\n"


class Section(Heading):
    """A section heading tag."""
    aliases = ("h2", )
    html_name = "h2"
    tex_name = "section"
    active = True
    include_paragraphs = False


class SubSection(Heading):
    """A subsection heading tag."""
    aliases = ("h3",)
    html_name = "h3"
    tex_name = "subsection"
    active = True
    include_paragraphs = False


class SubSubSection(Heading):
    """A subsubsection heading tag."""
    aliases = ("h4",)
    html_name = "h4"
    tex_name = "subsubsection"
    active = True
    include_paragraphs = False


class Para(Tag):
    """A paragraph heading tag."""
    aliases = ("h5",)

    html_name = "paragraph-heading"
    tex_name = "paragraph"
    active = True
    include_paragraphs = False
