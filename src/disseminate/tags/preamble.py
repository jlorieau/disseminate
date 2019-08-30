"""
Tags for document preambles.
"""
from .tag import Tag
from ..formats import html_tag
from ..utils.string import str_to_list


class Authors(Tag):
    """A tag for listing the author or authors."""

    aliases = ('author',)
    active = True

    def __init__(self, name, content, attributes, context):
        super(Authors, self).__init__(name, content, attributes, context)

        # Use the specified author list in the content, if specified, otherwise
        # try to get it from the context.
        if (isinstance(self.content, str) and self.content.strip() == "" or
           self.content is None):

            author = (context.get('author', '') if 'author' in context else
                      context.get('authors', ''))
            self.content = author

        # Convert the author string to a list
        if isinstance(self.content, str):
            self.content = str_to_list(self.content)

    def author_string(self):
        """Generate a formatted string listing the authors."""
        # Convert to a list of strings
        if isinstance(self.content, str):
            author_lst = str_to_list(self.content)
        elif isinstance(self.content, list):
            author_lst = self.content
        else:
            return ''

        # Convert to a list of authors
        if len(author_lst) == 0:
            return ''
        elif len(author_lst) == 1:
            return author_lst[0]
        else:
            last_two = author_lst[-2:]
            others = author_lst[:-2]

            if len(author_lst) == 2:
                return ', '.join(others) + ' and '.join(last_two)
            else:
                return ', '.join(others) + ', ' + ' and '.join(last_two)

    def html_fmt(self, level=1, content=None):
        return html_tag('div', attributes='class=authors',
                        formatted_content=self.author_string(), level=level)

    def tex_fmt(self, level=1, mathmode=False, content=None):
        return self.author_string()


class Titlepage(Tag):
    """A titlepage tag."""

    authors_tag = None
    active = True

    def __init__(self, name, content, attributes, context):
        super(Titlepage, self).__init__(name, content, attributes, context)

        # Setup the author tag
        self.authors_tag = Authors(name='authors', content='',
                                   attributes=tuple(), context=context)

    @property
    def title(self):
        """The title of the project"""
        return self.context.get('title', '')

    @property
    def authors(self):
        """The authors of the document"""
        if 'document' in self.context:
            doc = self.context['document']
            if hasattr(doc, 'author'):
                return doc.author
        if 'author' in self.context:
            return self.context['author']

    def html_fmt(self, content=None, level=1):
        title_tag = html_tag('h1', attributes='class=title',
                             formatted_content=self.title, level=level + 1)
        author_tag = self.authors_tag.html_fmt(content=content, level=level + 1)
        return html_tag('div', attributes='class=title-page',
                        formatted_content=[title_tag, author_tag], level=level)

    def tex_fmt(self, content=None, mathmode=False, level=1):
        return "\n\\maketitle\n\n"
