"""
Image tags
"""
import pathlib

from .tag import Tag, TagError
from .utils import format_attribute_width
from ..paths.utils import find_files
from ..formats import tex_cmd


class ImgFileNotFound(TagError):
    """The image file was not found."""
    pass


class Img(Tag):
    """The img tag for inserting images.

    When rendering to a target document format, this tag may use a converter,
    the attributes and context of this tag to convert the infile to an outfile
    in a needed format.

    Attributes
    ----------
    active : bool
        If True, the Tag can be used by the TagFactory.
    html_name : str
        If specified, use this name when rendering the tag to html. Otherwise,
        use name.
    in_ext : Optional[str]
        Used to correctly identify the builder to add if the contents need
        to be rendered first.
    img_filepath : str
        The path for the (source) image.
    """

    active = True

    process_content = False
    process_typography = False

    html_name = 'img'
    in_ext = None
    _infilepath = None
    _outfilepaths = None

    def __init__(self, name, content, attributes, context):
        super().__init__(name=name, content=content, attributes=attributes,
                         context=context)
        self._outfilepaths = dict()

    def content_as_filepath(self, content=None, context=None):
        """Returns a filepath from the content, if it's a valid filepath,
        or returns None if it isn't.

        Parameters
        ----------
        content : Optional[Union[str, List[Union[str, list, :obj:`Tag \
            <.tag.Tag>`], :obj:`Tag <.tag.Tag>`]]
            The contents of the tag. It can either be a string, a tag or a list
            of strings, tags and lists.
        context : Optional[:obj:`Type[BaseContext] <.BaseContext>`]
            The context with values for the document.

        Returns
        -------
        filepath : Union[:obj:`pathlib.Path`. None]
            The filepath, if found, or None if a valid filepath was not found.
        """
        content = content or self.content
        context = context or self.context

        # Move the contents to the infilepath attribute
        if isinstance(content, pathlib.Path) and content.is_file():
            return content
        elif isinstance(content, str):
            # Get the infilepath for the file
            filepaths = find_files(content, context)
            return filepaths[0] if filepaths else None

        return None

    def add_file(self, target, content=None, attributes=None, context=None):
        """Convert and add the file dependency for the specified document
        target.

        Parameters
        ----------
        target : str
            The document target format. ex: '.html', '.tex'
        content : Optional[Union[str, List[Union[str, list, :obj:`Tag \
            <.tag.Tag>`], :obj:`Tag <.tag.Tag>`]]
            The contents of the tag. It can either be a string, a tag or a list
            of strings, tags and lists.
        attributes : Optional[Union[str, \
            :obj:`Attributes <.attributes.Attributes>`]]
            The attributes of the tag.
        context : Optional[:obj:`Type[BaseContext] <.BaseContext>`]
            The context with values for the document.

        Returns
        -------
        outfilepath : :obj:`.paths.TargetPath`
            The filepath for the file in the target document directory.

        Raises
        ------
        ImgFileNotFound
            Raises an ImgFileNotFound exception if a filepath couldn't be
            found in the tag contents.
        BuildError
            If a builder could not be found for the builder
        """
        # See if a cached path exists already. This can only be done if the
        # content, attributes and context aren't specified because the
        # values of this tag will be used for these parameters.
        if all(i is None for i in (content, attributes, context)):
            if target in self._outfilepaths:
                return self._outfilepaths[target]
            else:
                can_cache = True
        else:
            can_cache = False

        # If not get the outfilepath for the given document target
        assert self.context.is_valid('builders')

        # Retrieve the unspecified arguments
        target = target if target.startswith('.') else '.' + target
        content = content or self.content
        attrs = attributes or self.attributes
        context = context or self.context

        # Retrieve builder
        target_builder = self.context.get('builders', dict()).get(target)
        assert target_builder, ("A target builder for '{}' is needed in the "
                                "document context")

        # Prepare the parameters. Either their a filepath of the contents
        # or the contents themselves.
        content = (self.content_as_filepath(content=content, context=context)
                   or content)
        parameters = ([content] + list(attrs.filter(target=target).totuple()))
        build = target_builder.add_build(parameters=parameters,
                                         context=context,
                                         in_ext=self.in_ext,
                                         target=target,
                                         use_cache=False)
        outfilepath = build.outfilepath

        # Cache the outfilepath, if possible
        if can_cache:
            self._outfilepaths[target] = outfilepath

        return outfilepath

    def tex_fmt(self, content=None, attributes=None, context=None,
                mathmode=False, level=1):
        # Add the file dependency
        outfilepath = self.add_file(target='.tex', content=content,
                                    context=context, attributes=attributes)

        # Format the width
        attributes = attributes or self.attributes
        attrs = format_attribute_width(attributes, target='.tex')

        # Get the filename for the file. Wrap this filename in curly braces
        # in case the filename includes special characters
        base = outfilepath.with_suffix('')
        suffix = outfilepath.suffix
        dest_filepath = "{{{base}}}{suffix}".format(base=base, suffix=suffix)

        return tex_cmd(cmd='includegraphics', attributes=attrs,
                       formatted_content=str(dest_filepath))

    def html_fmt(self, content=None, attributes=None, context=None, level=1):
        # Add the file dependency
        outfilepath = self.add_file(target='.html', content=content,
                                    context=context, attributes=attributes)
        url = outfilepath.get_url(context=self.context)

        # Format the width and attributes
        attrs = self.attributes.copy() if attributes is None else attributes
        attrs = format_attribute_width(attrs, target='.html')
        attrs['src'] = url

        return super().html_fmt(attributes=attrs, level=level)
