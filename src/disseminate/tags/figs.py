"""
Tags for figure environments.
"""
from .tag import Tag
from .caption import Caption
from .utils import format_attribute_width
from ..utils.string import strip_multi_newlines
from ..utils.types import StringPositionalValue


class BaseFigure(Tag):
    """A base class for a figure tag.

    The BaseFigure initializes figures by adding 'id' attributes to labels in
    the label manager and reorganizing captions to the bottom of the figure.
    """

    def __init__(self, name, content, attributes, context):
        super().__init__(name=name, content=content, attributes=attributes,
                         context=context)

        # Transfer the label id ('id') to the caption, if available. First,
        # find the caption tag, if available
        captions = [tag for tag in self.flatten(filter_tags=True)
                    if isinstance(tag, Caption)]

        for caption in captions:
            # Transfer the 'id' to the caption (but only the first)
            caption.label_id = self.attributes.pop('id', None)

            # Set the label kind for the caption as a figure caption
            caption.kind = ('caption', 'figure')

            # Create the label in the label_manager
            caption.create_label()


class Marginfig(BaseFigure):
    """The @marginfig tag"""

    html_name = 'marginfig'
    tex_env = 'marginfigure'
    active = True


class Figure(BaseFigure):
    """The @figure/@fig tag"""

    aliases = ('fig',)
    html_name = 'figure'
    tex_env = 'figure'
    active = True


class FullFigure(BaseFigure):
    """The @fullfigure/@ffig tag"""

    aliases = ('ffig', 'fullfig')
    html_name = 'fullfigure'
    tex_env = 'figure*'
    active = True


class Panel(Tag):
    """A panel (sub-figure) for a figure."""

    active = True
    html_name = 'panel'
    tex_env = 'panel'

    def tex_fmt(self, content=None, attributes=None, mathmode=False, level=1):
        attrs = self.attributes.copy() if attributes is None else attributes

        # Format the width
        attrs = format_attribute_width(attrs, target='.tex')

        # Convert the width attribute to a StringPositional, which is needed
        # by the panel environment
        # ex: \begin{panel}{0.5\textwidth} \end{panel}
        width = attrs.get('width', target='.tex')
        if width is not None:
            attrs[width] = StringPositionalValue

        # Raises an error if a width is not present. Strip multiple newlines
        # as these break up side-by-side figures
        env = super().tex_fmt(content=content, attributes=attrs,
                              mathmode=mathmode, level=level)
        return strip_multi_newlines(env).strip()

    def html_fmt(self, content=None, attributes=None, level=1):
        attrs = self.attributes.copy() if attributes is None else attributes

        # Format the width
        attrs = format_attribute_width(attrs, target='.html')
        attrs['class'] = 'panel'

        return super().html_fmt(content=content, attributes=attrs, level=level)
