"""
Formatting of Table of Contents for documents
"""
from itertools import groupby

from .headings import toc_levels as heading_toc_levels, Heading
from .ref import Ref
from .tag import Tag
from . import exceptions
from ..formats import html_tag, tex_env, tex_cmd
from ..utils.string import strip_multi_newlines


class TocError(Exception):
    """An error was encountered while processing a table of contents tag."""
    pass


class TocRef(Ref):
    """A Ref tag for the TOC.

    This is a separate class so that the label_fmt may be different for TOC
    entries.
    """

    def tex_fmt(self, content=None, mathmode=False, level=1):
        # Add the pageref
        label = self.label
        tex_str = super().tex_fmt(content=content, mathmode=mathmode,
                                  level=level)

        if label is not None:
            return (tex_str + " " +
                    tex_cmd('hfill') + " " +
                    tex_cmd('pageref', attributes=label.id))
        else:
            return tex_str


class Toc(Tag):
    """Table of contents and listings.

    contents : str
        The contents are the label types to list. The following entries
        are supported:

        - document : list document labels
        - heading : list heading labels
        - figure : list figure labels
        - table : list table labels

        Additionally, the following modifiers have special meaning:
        - all : list labels from all documents
        - current : list labels from the current document (default)


        - expanded : pertains to 'all document' and 'all headings'.
                     Show all documents are including all headings.
        - abbreviated : pertains to 'all document' and 'all headings'.
                        show all documents but only show headings for the
                        current document
        - collapsed : pertains to 'all document' and 'all headings'.
                     show only the documents without headings. (default)
    """

    active = True
    toc_kind = None
    toc_elements = None
    header_tag = None

    process_typography = False

    _mtime = None
    ref_tags = None

    def __init__(self, name, content, attributes, context):
        super(Toc, self).__init__(name, content, attributes, context)

        # Get the TOC's kind from the tag's content
        content = self.content
        if isinstance(content, list) and len(content) > 0:
            content = content[0]
        if isinstance(content, str):
            self.toc_kind = content.split()
        elif isinstance(content, Tag):
            self.toc_kind = content.txt

        # If the TOC kind hasn't been assigned, the content could be parsed.
        # Raise and exception
        if self.toc_kind is None:
            msg = "The {} tag could not parse the tag contents: {}"
            raise exceptions.TagError(msg.format(self.name, content))

        # Setup the TOC header, if specified
        header = self.attributes.pop('header', None)

        if header is not None:
            self.header_tag = Heading(name='TOC', content='Table of Contents',
                                      attributes='nolabel', context=context)

    def get_labels(self):
        """Get the labels, ordering function and labeling type."""
        assert self.context.is_valid('label_manager')

        # If 'all' is specified in the toc_kind, then all documents should be
        # selected. This is done by having a doc_id of None with the
        # 'get_labels' method of the label manager. If 'all' is not
        # specified, then use this document's doc_id. This will return labels
        # only for this document and its context from the 'get_labels' method
        # of the label manager.
        context = self.context
        doc_id = context.get('doc_id') if 'all' not in self.toc_kind else None

        # Create a default function for order labels. This may be overwritten
        # below, depending on the type of TOC.
        def default_order_function(label):
            return 0

        default_return_value = [], default_order_function, ''

        if 'label_manager' in self.context:
            label_manager = self.context['label_manager']
        else:
            return default_return_value

        if 'heading' in self.toc_kind or 'headings' in self.toc_kind:
            # Retrieve heading labels, either for this document or all documents
            # (depending on the value of doc_id)
            labels = label_manager.get_labels(doc_id=doc_id,
                                              kinds='heading')

            last_heading_level = None
            current_toc_level = 0

            # Setup the ordering function. This ordering function is setup so
            # that the heading level only increases or decreases by 1 level at
            # a time. The is because the heading level may jump by 2 or more
            # levels (ex: heading -> subsubheading), and this can trip up
            # enumerate environments for targets like tex.
            def order_function(label):
                nonlocal last_heading_level
                nonlocal current_toc_level
                heading_level = heading_toc_levels.index(label.kind[-1])

                if last_heading_level is None:  # Start at base level
                    current_toc_level = 0
                elif heading_level > last_heading_level:  # Increase level
                    current_toc_level += 1
                elif heading_level < last_heading_level:  # Decrease level
                    current_toc_level -= 1
                last_heading_level = heading_level
                return current_toc_level

            return labels, order_function, 'heading'

        if 'document' in self.toc_kind or 'documents' in self.toc_kind:
            # Retrieve the labels for the documents and the headings. Either
            # for this document or all documents (depending on the value of
            # doc_id)
            document_labels = label_manager.get_labels(doc_id=doc_id,
                                                       kinds='document')
            heading_labels = label_manager.get_labels(doc_id=doc_id,
                                                      kinds='heading')

            # Reorganize the document and heading labels such that the headings
            # are between documents
            current_doc_id = self.context['doc_id']
            merged_labels = []
            for document_label in document_labels:
                merged_labels.append(document_label)

                # Add the headings either if this is an 'expanded' toc, or
                # it's an 'abbreviated' toc, but the document corresponds to the
                # current document
                if ('expanded' in self.toc_kind or
                   ('abbreviated' in self.toc_kind and
                    document_label.doc_id == current_doc_id)):

                    merged_labels += [l for l in heading_labels
                                      if l.doc_id == document_label.doc_id]

            # Get a toc_levels for the document, based on the document_labels
            doc_toc_levels = {l.kind[-1] for l in document_labels}
            doc_toc_levels = tuple(sorted(doc_toc_levels))
            merged_toc_levels = doc_toc_levels + heading_toc_levels

            last_doc_level = None
            current_toc_level = 0

            # Setup the ordering function. This ordering function is setup so
            # that the document and heading  level only increases or decreases
            # by 1 level at a time. The is because the document or heading
            # level may jump by 2 or more levels (ex: heading -> subsubheading),
            # and this can trip up enumerate environments for targets like tex.
            def order_function(label):
                nonlocal last_doc_level
                nonlocal current_toc_level
                specific_kind = label.kind[-1]
                doc_level = merged_toc_levels.index(specific_kind)

                if last_doc_level is None:  # Start at the base level
                    current_toc_level = 0
                elif doc_level > last_doc_level:  # Increase by 1 level
                    current_toc_level += 1
                elif doc_level < last_doc_level:  # Decrease by 1 level
                    current_toc_level -= 1
                last_doc_level = doc_level
                return current_toc_level

            return merged_labels, order_function, 'document'

        else:
            return default_return_value

    def update_tags(self):
        """Populate this tag's content by adding TocRef items.
        """
        # Get labels and determine their latest modification time (mtime).
        # We poll the fresh list of labels instead of the cached ref_tags
        # because the entries in the TOC may have changed since the ref_tags
        # were last loaded.
        labels, order_function, heading_type = self.get_labels()
        label_mtimes = [label.mtime for label in labels]
        latest_mtime = max(label_mtimes) if len(label_mtimes) > 0 else None

        # Determine whether the labels are up to date and whether tags have
        # already been prepared. If so, use those.
        if (self.ref_tags is not None and
            self._mtime is not None and
            latest_mtime is not None and
           self._mtime >= latest_mtime):
            return self.ref_tags

        # The labels have changed. Update the ref tags.
        # Collect the created tags.
        tags = []

        # Got through the labels and keep track of the heading levels
        max_level = 0
        for label in labels:
            try:
                level = order_function(label)
            except ValueError:
                level = 0

            if level > max_level:
                max_level = level

            # Create the tag and add it to the tags list
            tag_name = 'toc-' + label.kind[-1]
            tag = TocRef(name=tag_name, content=label.id,
                         attributes=self.attributes, context=self.context)

            # Add the tag to a flat list
            tags.append((level, tag))

        # Group the levels
        for level in reversed(range(0, max_level)):
            groups = [(k, list(g)) for k, g in
                      groupby(tags, lambda x: x[0] > level)]

            tags = []
            for above_level, g in groups:
                if above_level is False:
                    # These are smaller than the current level. Do not
                    # group these values and add them back to the list
                    tags += list(g)
                else:
                    # These are as large as the current level. Group them
                    # in their own sub-list
                    tags.append((level, [j[1] for j in g]))

        # Cache the ref tags and update the modification time for labels
        self.ref_tags = tags
        self._mtime = latest_mtime

    def html_fmt(self, content=None, listtype='ul', elements=None,
                 toc_level=1, level=1):
        """Convert the tag to an html listing.

        .. note:: The 'document' toc is special since it uses the documents
                  directly to construct the tree. All other toc types will
                  get the labels from the label_manager

        Parameters
        ----------
        content : Union[str, List[Union[str, list, :obj:`Tag \
            <disseminate.tags.Tag>`]], optional
            Specify an alternative content from the tag's content. It can
            either be a string, a tag or a list of strings, tags and lists.
        listtype : str, optional
            The type of list to render (ol, ul).
        elements : str, optional
            The reference tags.
        toc_level : int, optional
            The level of the toc.
        level : int, optional
            The level of the tag.

        Returns
        -------
        html : str or html element
            A string in HTML format or an HTML element (:obj:`lxml.builder.E`).
        """
        # Update the ref tags, if it's the root invocation--i.e. an elements
        # list hasn't been passed by this function to itself.
        if elements is None:
            self.update_tags()

        # Get the content. It should be a list of TocRef tags.
        content = content if content is not None else self.ref_tags
        elements = elements if elements is not None else content

        if elements is None:
            return ''

        if not hasattr(elements, '__iter__'):
            elements = [elements]

        returned_elements = []
        for e in elements:

            if isinstance(e, tuple) and len(e) == 2:
                # Unpack the element if it's a tuple with the order and the
                # element
                order, e = e

            if isinstance(e, list):
                # The element is a list of tags. Process this list as a group.
                returned_elements.append(self.html_fmt(content=None,
                                                       elements=e,
                                                       level=level + 1,
                                                       toc_level=toc_level + 1))
            else:
                # Otherwise it's a ref tag, get its html and wrap it in a list
                # item
                li = html_tag('li',
                              formatted_content=e.html_fmt(level=level + 1),
                              level=level + 1)
                returned_elements.append(li)

        # Create list tag
        list_tag = html_tag(listtype,
                            attributes='class=toc-level-{}'.format(toc_level),
                            formatted_content=returned_elements,
                            level=level)
        return list_tag

    def tex_fmt(self, content=None, elements=None, listtype='toclist',
                mathmode=False, level=1):
        """Convert the tag to a tex listing.

        .. note:: The 'document' toc is special since it uses the documents
                  directly to construct the tree. All other toc types will
                  get the labels from the label_manager

        Returns
        -------
        tex : str
            A string in TEX format
        """
        # Update the ref tags, if it's the root invocation--i.e. an elements
        # list hasn't been passed by this function to itself.
        if elements is None:
            self.update_tags()

        # Get the content. It should be a list of TocRef tags.
        content = content if content is not None else self.ref_tags
        elements = elements if elements is not None else content

        if elements is None:
            return ''

        if not hasattr(elements, '__iter__'):
            elements = [elements]

        returned_elements = []
        for e in elements:

            if isinstance(e, tuple) and len(e) == 2:
                # Unpack the element if it's a tuple with the order and the
                # element
                order, e = e

            if isinstance(e, list):
                # The element is a list of tags. Process this list as a group.
                returned_elements.append(self.tex_fmt(content=None,
                                                      elements=e,
                                                      level=level + 1))
            else:
                # Otherwise it's a ref tag, get its tex and wrap it in a list
                # item
                entry = (tex_cmd('item', indent=2) + " " +
                         e.tex_fmt(level=level + 1)) + "\n"
                returned_elements.append(entry)

        if len(returned_elements) > 0:
            returned_elements = strip_multi_newlines(''.join(returned_elements))
            return (tex_env(listtype, attributes='',
                    formatted_content=returned_elements,
                    indent=2 if level > 1 else 0))
        else:
            return ''
