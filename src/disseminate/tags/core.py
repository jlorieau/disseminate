"""
Core classes and functions for tags.
"""
from lxml.builder import E
from lxml import etree

from disseminate.attributes import set_attribute, kwargs_attributes
from . import settings


class TagError(Exception): pass


def _all_subclasses(cls):
    """Retrieve all subclasses, sub-subclasses and so on for a class"""
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in _all_subclasses(s)]

class TagFactory(object):
    """Generates the appropriate tag for a given tag type.
    """

    allowed_tags = None
    tag_types = None

    def __init__(self, allowed_tags=None):
        self.allowed_tags = allowed_tags

        # Initialize the tag types dict.
        self.tag_types = dict()
        for scls in  _all_subclasses(Tag):
            aliases = (list(scls.aliases) if scls.aliases is not None else
                       list())
            names = [scls.__name__.lower(),] + aliases

            for name in names:
                # duplicate or overwritten tag names are not allowed
                assert name not in self.tag_types
                self.tag_types[name] = scls

    def tag(self, tag_name, tag_content, tag_attributes,
                  local_context, global_context):
        """Return the approriate tag, give a tag_type and tag_content"""
        # Just return the content if it's an unallowed tag type
        if (isinstance(self.allowed_tags, list)
           and tag_name not in self.allowed_tags):
            return tag_content

        # Try to find the appropriate subclass
        small_tag_type = tag_name.lower()
        if small_tag_type in self.tag_types:
            cls = self.tag_types[small_tag_type]
        else:
            cls = Tag

        return cls(name=tag_name, content=tag_content,
                   attributes=tag_attributes,
                   local_context=local_context, global_context=global_context)


class Tag(object):
    """A tag to format text in the markup document.

    .. note:: Tags are created asynchroneously, so the creation of a tag
              should not read and depend on the `local_context` or
              `global_context`. These will only be partially populated at
              creation time. Only the target specific methods (html, tex, ...)
              should return new tags that depend on these contexts.

    Attributes
    ----------
    name : str
        The name of the tag as used in the disseminate source. (ex: 'body')
    content : None or str or list
        The contents of the tag. It can either be None, a string, or a list
        of tags and strings. (i.e. a sub-ast)
    attributes : list of tuples
        The attributes of the tag.
    aliases : list of str
        A list of strs for other names a tag goes by
    local_context : dict
        The context with values for the current document. The values in this
        dict do not depend on values from other documents. (local)
    global_context : dict
        The context with values for all documents in a project. The
        `global_context` is constructed with the `src_filepath` as a key and
        the `local_context` as a value.
    """

    name = None
    content = None
    attributes = None
    aliases = None

    html_name = None
    tex_name = None

    local_context = None
    global_context = None

    process_ast = None # takes target, returns a tag or list of tags.

    html_required_attributes = None

    def __init__(self, name, content, attributes, local_context,
                 global_context):
        self.name = name
        self.attributes = attributes
        if isinstance(content, list) and len(content) == 1:
            self.content = content[0]
        else:
            self.content = content
        self.local_context = local_context
        self.global_context = global_context

    def __repr__(self):
        return "{type}{{{content}}}".format(type=self.name,
                                            content=self.content)

    def __getitem__(self, item):
        """Index accession."""
        if not isinstance(self.content, list):
            msg = ("Cannot access sub-tree for tag {} because "
                   "tag contents are not a list")
            raise TagError(msg.format(self.__repr__()))
        return self.content[item]

    def default(self):
        """Convert the tag to a text string.

        Strips the tag information and simply return the content of the tag.

        Returns
        -------
        text_string : str
            A text string with the tags stripped.
        """
        if isinstance(self.content, list):
            items = [i.default() if hasattr(i, 'default') else i
                            for i in self.content]
            items = filter(bool, items)
            return "".join(items)
        else:
            return self.content

    def tex(self, level=1):
        # Collect the content elements
        if isinstance(self.content, list):
            elements = ''.join([i.tex(level + 1) if hasattr(i, 'tex') else i
                                for i in self.content])
        elif isinstance(self.content, str):
            elements = self.content
        else:
            elements = None

        # Construct the tag name
        if level > 1:
            name = (self.tex_name if self.tex_name is not None else
                    self.name.lower())
        else:
            name = ''

        # Format the tag. It's either a macro or environment
        if name in settings.tex_macros:
            return "\\" + name + '{' + elements + '}'  # ex: \section{First}
        elif name in settings.tex_commands:
            return "\\" + name + ' ' + elements + "\n"  # ex: \item
        elif name in settings.tex_environments:
            return ("\n\\begin{" + name + "}\n" +  # ex: \begin{align}
                    elements +
                    "\\end{" + name + "}\n")
        else:
            return elements

    def html(self, level=1):
        """Convert the tag to an html string or html element.

        Returns
        -------
        html : str or html element
            A string in HTML format or an HTML element (:obj:`lxml.builder.E`).
        """
        # Collect the content elements
        if isinstance(self.content, list):
            elements = [i.html(level + 1) if hasattr(i, 'html') else i
                        for i in self.content]
        elif isinstance(self.content, str):
            elements = self.content
        else:
            elements = None

        # Construct the tag name
        if level > 1:
            name = (self.html_name if self.html_name is not None else
                    self.name.lower())
        else:
            name = settings.html_root_tag

        if (settings.html_valid_tags and
           name in settings.html_valid_tags):

            kwargs = (kwargs_attributes(self.attributes) if self.attributes
                      else dict())
            e = (E(name, *elements, **kwargs) if elements else
                 E(name, **kwargs))
        else:
            # Create a span element if it not an allowed element
            # Add the tag type to the class attribute
            attrs = self.attributes if self.attributes else ()
            attrs = set_attribute(attrs, ('class', self.name), 'a')
            kwargs = kwargs_attributes(attrs)
            e = (E('span', *elements, **kwargs) if elements else
                 E('span', **kwargs))

        # Render the root tag if this is the first level
        if level == 1:
            return (etree
                    .tostring(e, pretty_print=settings.html_pretty)
                    .decode("utf-8"))
        else:
            return e
