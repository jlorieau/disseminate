"""
Test the proces_paragraphs function.
"""
from disseminate.tags.receivers.paragraphs import (
    group_paragraphs, clean_paragraphs, assign_paragraph_roles,
    process_paragraph_tags)
from disseminate.utils.string import replace_macros
from disseminate.tags import Tag
from disseminate.tags.text import P


test_paragraphs = """
This is my @b{first} paragraph.

This is my @i{second}. It has a multiple
lines.

This paragraph has a note. @note{

This note has multiple lines.

and multiple paragraphs.
}

This is the fourth paragraph

@section{A heading (no paragraph}

A fifth paragraph.

Here is a new one with @b{bolded} text as an example.
    @marginfig[offset=-1.0em]{
      @b{test}
    }

My final paragraph.
"""

test_paragraphs2 = """
  @section{A heading with leading spaces}
  
  This is my paragraph.
"""


def test_group_paragraphs():
    """Test the group_paragraphs function."""

    # 1. Test basic lists of items and strings with newlines
    group = group_paragraphs([1, 2, 'three', 'four\n\nfive', 6,
                              'seven\n\neight'])
    assert group == [[1, 2, 'three', 'four'], ['five', 6, 'seven'], ['eight']]

    # Running it again will not change the result
    group = group_paragraphs(group)
    assert group == [[1, 2, 'three', 'four'], ['five', 6, 'seven'], ['eight']]

    # 2. Test a basic string with newlines
    group = group_paragraphs("One, two\nthree\n\nFour, five\nSix\n\nSeven")
    assert group == [['One, two\nthree'], ['Four, five\nSix'], ['Seven']]

    group = group_paragraphs(group)
    assert group == [['One, two\nthree'], ['Four, five\nSix'], ['Seven']]

    group = group_paragraphs([1, 2, 'three', 'four\n\n\n\nfive', 6, '\n\n',
                              'seven\n\neight'])
    assert group == [[1, 2, 'three', 'four'], ['five', 6], ['seven'], ['eight']]

    # 3. Test string objects with 'include_paragraphs' attributes
    class AltInt(int):
        include_paragraphs = True

    group = group_paragraphs([AltInt(1), AltInt(2), 'three', 'four\n\nfive',
                              AltInt(6), 'seven\n\neight'])
    assert group == [[1, 2, 'three', 'four'], ['five', 6, 'seven'], ['eight']]

    group = group_paragraphs(group)
    assert group == [[1, 2, 'three', 'four'], ['five', 6, 'seven'], ['eight']]

    ast = [AltInt(1), AltInt(2), 'three', 'four\n\nfive', AltInt(6),
           'seven\n\neight']
    ast[0].include_paragraphs = False
    ast[1].include_paragraphs = False
    ast[4].include_paragraphs = False
    group = group_paragraphs(ast)
    assert group == [1, 2, ['three', 'four'], ['five'], 6, ['seven'], ['eight']]

    group = group_paragraphs(group)
    assert group == [1, 2, ['three', 'four'], ['five'], 6, ['seven'], ['eight']]


def test_group_paragraphs_with_tags(doc):
    """Test the group_paragraphs function with a tag."""

    # Get a context from a temp document that includes a label_manager, which
    # is needed by the section and marginfig tags
    context = doc.context

    # 1. Test with an ast object generated by process_ast
    root = Tag(name='root', content=test_paragraphs, attributes='',
               context=context)
    group = group_paragraphs(root.content)

    assert group[0][0] == '\nThis is my '
    assert group[0][1].name, group[0][1].content == ('b', 'first')
    assert group[0][2] == ' paragraph.'

    assert group[1][0] == 'This is my '
    assert group[1][1].name, group[1][1].content == ('i', 'second')
    assert group[1][2] == ". It has a multiple\nlines."

    assert group[2][0] == "This paragraph has a note. "
    assert group[2][1].name == 'note'
    assert group[2][1].content == ("\n\nThis note has multiple lines.\n\n"
                                   "and multiple paragraphs.\n")

    assert group[3][0] == "This is the fourth paragraph"

    assert group[4].name == 'section'
    assert group[4].content == 'A heading (no paragraph'

    assert group[5][0] == 'A fifth paragraph.'

    assert group[6][0] == 'Here is a new one with '
    assert group[6][1].name, group[6][1].content == ('b', 'bolded')
    assert group[6][2] == ' text as an example.\n    '

    assert group[7].name == 'marginfig'
    assert group[7].content[0] == '\n      '
    assert group[7].content[1].name == 'b'
    assert group[7].content[2] == '\n    '

    assert group[8][0] == 'My final paragraph.\n'

    # Test to make sure group_paragraphs can be run more than once
    group2 = group_paragraphs(group)

    assert group == group2


def test_clean_paragraphs():
    """Test the clean_paragraphs function."""

    # 1. Test a basic list of items and strings with newlines
    group = group_paragraphs([1, 2, 'three', 'four\n\nfive', 6,
                              'seven\n\neight'])
    group = clean_paragraphs(group)
    assert group == [[1, 2, 'three', 'four'], ['five', 6, 'seven'], ['eight']]

    # 2. Test a list of items with only newlines
    group = group_paragraphs([1, 2, 'three', 'four\n\n\n\nfive', 6, '\n\n',
                              'seven\n\neight'])
    group = clean_paragraphs(group)
    assert group == [[1, 2, 'three', 'four'], ['five', 6], ['seven'],
                     ['eight']]


def test_assign_paragraph_roles(context_cls):
    """Test the assign_paragraph_roles function."""

    context = context_cls()

    # 1. Test a basic list of items and strings with newlines
    tag1 = Tag(name='tag1', content='', attributes=tuple(), context=context)
    tag2 = Tag(name='tag2', content='', attributes=tuple(), context=context)
    tag3 = Tag(name='tag3', content='', attributes=tuple(), context=context)

    # Para 1: [tag1, tag2, 'three', 'four']
    # Para 2: ['five', tag3, 'seven']
    # Para 3: ['eight']
    group = group_paragraphs([tag1, tag2, 'three', 'four\n\nfive', tag3,
                              'seven\n\neight'])
    assert group[0][0].paragraph_role is None
    assert group[0][1].paragraph_role is None
    assert group[1][1].paragraph_role is None

    # Now assign the paragraph_roles
    assign_paragraph_roles(elements=group, tag_base_cls=Tag)
    assert group[0][0].paragraph_role == 'inline'
    assert group[0][1].paragraph_role == 'inline'
    assert group[1][1].paragraph_role == 'inline'

    # 2. Test an example with a block tag
    tag1 = Tag(name='tag1', content='', attributes=tuple(), context=context)
    tag2 = Tag(name='tag2', content='', attributes=tuple(), context=context)
    tag3 = Tag(name='tag3', content='', attributes=tuple(), context=context)

    group = group_paragraphs([tag1, tag2, 'three', 'four\n\n', tag3,
                              '\n\neight'])
    assert group[0][0].paragraph_role is None
    assert group[0][1].paragraph_role is None
    assert group[1][0].paragraph_role is None

    # Now assign the paragraph_roles
    assign_paragraph_roles(elements=group, tag_base_cls=Tag)
    assert group[0][0].paragraph_role == 'inline'
    assert group[0][1].paragraph_role == 'inline'
    assert group[1][0].paragraph_role == 'block'

    # 3. Test an example with empty strings
    tag1 = Tag(name='tag1', content='', attributes=tuple(), context=context)
    tag2 = Tag(name='tag2', content='', attributes=tuple(), context=context)
    tag3 = Tag(name='tag3', content='', attributes=tuple(), context=context)

    group = group_paragraphs(['\n  ', tag1, '  \n  '])
    assert len(group) == 1
    assert group[0][1].paragraph_role is None

    # Now assign the paragraph_roles
    assign_paragraph_roles(elements=group, tag_base_cls=Tag)
    assert group[0][1].paragraph_role == 'block'


def test_assign_paragraph_with_tags(doc):
    """Test the assign_paragraph_roles function with tags."""

    # Get a context from a temp document that includes a label_manager, which
    # is needed by the section and marginfig tags
    context = doc.context

    # 1. Test with an ast object generated by process_ast
    root = Tag(name='role', content=test_paragraphs, attributes='',
               context=context)
    group = group_paragraphs(root.content)
    assign_paragraph_roles(elements=group, tag_base_cls=Tag)

    assert group[0][1].paragraph_role == 'inline'
    assert group[1][1].paragraph_role == 'inline'
    assert group[2][1].paragraph_role == 'inline'
    assert group[4].paragraph_role is None  # Heading is not in a paragraph
    assert group[6][1].paragraph_role == 'inline'
    assert group[7].paragraph_role is None  # marginfig is not in a paragraph


def test_process_paragraph_tags(doc):
    """Test the process_paragraph_tags function"""

    # Get a context from a temp document that includes a label_manager, which
    # is needed by the section and marginfig tags
    context = doc.context

    root = Tag(name='root', content=test_paragraphs, attributes='',
               context=context)
    process_paragraph_tags(element=root, context=context, tag_base_cls=Tag,
                           p_cls=P)

    # Check the individual items of root.
    assert root.name == 'root'
    assert isinstance(root[0], P)
    assert root[0].content[0] == '\nThis is my '
    assert root[0].content[1].name == 'b'  # bolded
    assert root[0].content[2] == ' paragraph.'

    assert isinstance(root[1], P)
    assert root[1].content[0] == 'This is my '
    assert root[1].content[1].name == 'i'  # italics
    assert root[1].content[2] == '. It has a multiple\nlines.'

    assert isinstance(root[2], P)
    assert root[2].content[0] == 'This paragraph has a note. '
    assert root[2].content[1].name == 'note'  # note

    assert isinstance(root[3], P)
    assert root[3].content == 'This is the fourth paragraph'

    assert root[4].name == 'section'
    assert root[4].content == 'A heading (no paragraph'

    assert isinstance(root[5], P)
    assert root[5].content == 'A fifth paragraph.'

    assert isinstance(root[6], P)
    assert root[6].content[0] == 'Here is a new one with '
    assert root[6].content[1].name == 'b'  # bolded
    assert root[6].content[2] == ' text as an example.\n    '

    assert root[7].name == 'marginfig'  # margin tag

    assert isinstance(root[8], P)
    assert root[8].content == 'My final paragraph.\n'


def test_process_paragraph_tags_leading_spaces(doc):
    """Test the process_paragraph_tags function when trailing spaces are
    present.
    """
    # Get a context from a temp document that includes a label_manager, which
    # is needed by the section and marginfig tags
    context = doc.context

    root = Tag(name='root', content=test_paragraphs2, attributes='',
               context=context)
    process_paragraph_tags(element=root, context=context, tag_base_cls=Tag,
                           p_cls=P)

    assert root.name == 'root'
    assert root.content[0].name == 'section'
    assert root.content[0].content == 'A heading with leading spaces'
    assert root.content[1].name == 'p'
    assert root.content[1].content == 'This is my paragraph.\n'


def test_process_paragraph_tags_subtags(context_cls):
    """Test the process_paragraph_tags function with subtags."""

    # setup a test ast with a macro
    context = context_cls(**{'p90x': '90@deg@sub{x}'})

    root = Tag(name='root', content="My @p90x pulse.", attributes='',
               context=context)
    process_paragraph_tags(element=root, context=context, tag_base_cls=Tag,
                           p_cls=P)

    # Check the root tag
    assert root.name == 'root'

    # Get the p tag
    p = root.content
    assert p.name == 'p'
    assert p.content[0] == 'My '
    assert p.content[1].name == 'p90x'
    assert p.content[2] == ' pulse.'

    # Test paragraph processing with a macro and tag
    root = Tag(name='root', content="My @b{y = x} @1H pulse.", attributes='',
               context=context)
    process_paragraph_tags(element=root, context=context, tag_base_cls=Tag,
                           p_cls=P)

    # Check the root tag
    assert root.name == 'root'

    # Get the p tag
    p = root.content
    assert p.name == 'p'
    assert p.content[0] == 'My '
    assert p.content[1].name == 'b'
    assert p.content[2] == ' '
    assert p.content[3].name == '1H'
    assert p.content[4] == ' pulse.'


def test_process_paragraph_tags_newlines(context_cls):
    """Test the preservation of newlines in a parapgraph with macros."""

    text = """The purpose of the @abrv{INEPT} sequenceMorris1979 is to 
    transfer the large magnetization from high-@gamma nuclei, like @1H or
    @19F, to low-@gamma nuclei (labeled 'X'), like @13C and @15N."""

    context = context_cls(**{'@1H': '@sup{1}H',
                             '@13C': '@sup{13}C', '@15N': '@sup{15}N',
                             '@19F': '@sup{19}F', '@gamma': '@symbol{gamma}',
                             'src_filepath': '.',
                             'body': text})

    text = replace_macros(text, context)
    root = Tag(name='root', content=text, attributes='', context=context)
    process_paragraph_tags(element=root, context=context, tag_base_cls=Tag,
                           p_cls=P)

    root_html = root.html
    assert 'is to \n    transfer' in root_html
    assert '<sup>1</sup>H or\n' in root_html
    assert 'or\n    <sup>19</sup>F' in root_html


def test_process_paragraphs_in_context(doc):
    """Test the automatic processing of tags marked in the 'process_paragraphs'
    entry of the context."""

    # Get a context from a temp document that includes a label_manager, which
    # is needed by the section and marginfig tags
    context = doc.context

    # 1. Use the test_paragraphs as an example
    context['process_paragraphs'] = ['body']

    # Create the body tag
    tag = Tag(name='body', content=test_paragraphs, attributes='',
              context=context)

    assert tag.name == 'body'
    assert isinstance(tag[0], P)
    assert tag[0].content[0] == '\nThis is my '
    assert tag[0].content[1].name == 'b'  # bolded
    assert tag[0].content[2] == ' paragraph.'

    assert isinstance(tag[1], P)
    assert tag[1].content[0] == 'This is my '
    assert tag[1].content[1].name == 'i'  # italics
    assert tag[1].content[2] == '. It has a multiple\nlines.'

    assert isinstance(tag[2], P)
    assert tag[2].content[0] == 'This paragraph has a note. '
    assert tag[2].content[1].name == 'note'  # note

    assert isinstance(tag[3], P)
    assert tag[3].content == 'This is the fourth paragraph'

    assert tag[4].name == 'section'
    assert tag[4].content == 'A heading (no paragraph'

    assert isinstance(tag[5], P)
    assert tag[5].content == 'A fifth paragraph.'

    assert isinstance(tag[6], P)
    assert tag[6].content[0] == 'Here is a new one with '
    assert tag[6].content[1].name == 'b'  # bolded
    assert tag[6].content[2] == ' text as an example.\n    '

    assert tag[7].name == 'marginfig'  # margin tag

    assert isinstance(tag[8], P)
    assert tag[8].content == 'My final paragraph.\n'
    

