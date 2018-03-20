"""
Test the caption and reg tags.
"""
import pytest

from disseminate import Document
from disseminate.tags.caption import Caption
from disseminate.ast import process_ast
from disseminate.labels import LabelManager, LabelNotFound


def test_naked_caption():
    """Tests the parsing of naked captions (i.e. those not nested in a figure
    or table)."""
    # Create a label manager
    label_man = LabelManager()

    # Create a mock local_context and global_context
    local_context = dict()
    global_context = {'_label_manager': label_man}

    # Generate the markup without an id
    src = "@caption{This is my caption}"

    # Generate a tag and compare the generated tex to the answer key
    root = process_ast(src, global_context=global_context)

    caption = root.content
    assert caption.name == 'caption'
    assert caption.attributes == tuple()
    assert caption.content == 'This is my caption'

    # Naked captions do not register labels
    assert len(label_man.labels) == 0


def test_figure_caption_no_id():
    """Tests the parsing of captions in figure tags when no id is specified."""
    # Create a label manager
    label_man = LabelManager()

    # Create a mock local_context and global_context
    doc = Document(src_filepath='src/main.dm',
                   targets={'.html': 'html/main.html',
                            '.tex': 'tex/main.tex'})
    local_context = {'_document': doc,
                     'figure': "Fig. {number}"}
    global_context = {'_label_manager': label_man}

    # Generate the markup without an id
    src = "@marginfig{@caption{This is my caption}}"

    # Generate a tag and compare the generated tex to the answer key
    root = process_ast(src, local_context=local_context,
                       global_context=global_context)

    fig = root.content
    assert fig.name == 'marginfig'
    assert fig.attributes == tuple()

    # Get the caption
    assert isinstance(fig.content, list)
    caption = [i for i in fig.content if isinstance(i, Caption)][0]

    assert caption.name == 'caption'
    assert caption.attributes == tuple()
    assert caption.default() == 'Fig. .1. This is my caption'

    # A label should have been registered
    assert len(label_man.labels) == 1
    label = list(label_man.labels)[0]
    assert label.id == None
    assert label.kind == ('figure',)
    assert label.local_order == (1,)
    assert label.global_order == (1,)


def test_figure_caption_no_id_html():
    """Tests the html generation of captions in figure tags when no id is
    specified."""
    # Create a label manager
    label_man = LabelManager()

    # Create a mock local_context and global_context
    doc = Document(src_filepath='src/main.dm',
                   targets={'.html': 'html/main.html',
                            '.tex': 'tex/main.tex'})
    doc.local_context.update({'_document': doc,
                              'figure_label': "Fig. {number}"})
    doc.global_context.update({'_label_manager': label_man})

    # Generate the markup without an id
    src = "@marginfig{@caption{This is my caption}}"

    # Generate a tag and compare the generated tex to the answer key
    root = process_ast(src, local_context=doc.local_context,
                       global_context=doc.global_context)

    # Test the caption's html
    # The following root tags have to be stripped for the html strings
    root_start = '<span class="root">\n  '
    root_end = '\n</span>\n'

    root_html = root.html()

    # Remove the root tag
    root_html = root_html[len(root_start):]  # strip the start
    root_html = root_html[:(len(root_html) - len(root_end))]  # strip end

    key = """<span class="marginfig">
    <span class="caption">
      <span class="figure-label">Fig. 1</span>
      <span class="caption-text">This is my caption</span>
    </span>
  </span>"""
    assert root_html == key


def test_figure_caption_no_id_tex():
    """Tests the tex generation of captions in figure tags when no id is
    specified."""
    # Create a label manager
    label_man = LabelManager()

    # Create a mock local_context and global_context
    doc = Document(src_filepath='src/main.dm',
                   targets={'.html': 'html/main.html',
                            '.tex': 'tex/main.tex'})
    doc.local_context.update({'_document': doc,
                              'figure_label': "Fig. {number}"})
    doc.global_context.update({'_label_manager': label_man})

    # Generate the markup without an id
    src = "@marginfig{@caption{This is my caption}}"

    # Generate a tag and compare the generated tex to the answer key
    root = process_ast(src, local_context=doc.local_context,
                       global_context=doc.global_context)
    root_tex = root.tex()
    key = """
\\begin{marginfigure}
Fig. 1 \\caption{This is my caption}
\\end{marginfigure}
"""
    assert root_tex == key


def test_figure_caption_with_id():
    """Tests the parsing of captions in figure tags when an id is specified."""
    # Test two cases: one in which the id is in the figure tag, and one in which
    # the id is in the caption tag
    for src in ("@marginfig[id=fig-1]{@caption{This is my caption}}",
                "@marginfig{@caption[id=fig-1]{This is my caption}}"):

        # Create a label manager
        label_man = LabelManager()

        # Create a mock local_context and global_context
        doc = Document(src_filepath='src/main.dm',
                       targets={'.html': 'html/main.html',
                                '.tex': 'tex/main.tex'})
        doc.local_context.update({'_document': doc,
                                  'figure_label': "Fig. {number}"})
        doc.global_context.update({'_label_manager': label_man})

        # Generate a tag and compare the generated tex to the answer key
        root = process_ast(src, local_context=doc.local_context,
                           global_context=doc.global_context)

        fig = root.content
        assert fig.name == 'marginfig'

        # Get the caption
        assert isinstance(fig.content, list)
        caption = [i for i in fig.content if isinstance(i, Caption)][0]

        assert caption.name == 'caption'
        assert caption.content == 'This is my caption'

        # A label should have been registered
        assert len(label_man.labels) == 1
        label = list(label_man.labels)[0]
        assert label.id == 'fig-1'
        assert label.kind == ('figure',)
        assert label.local_order == (1,)
        assert label.global_order == (1,)


def test_figure_caption_with_id_html():
    """Tests the html generation of captions in figure tags when an id is
    specified."""
    # Test two cases: one in which the id is in the figure tag, and one in which
    # the id is in the caption tag
    srcs = ("@marginfig[id=fig-1]{@caption{This is my caption}}",
            "@marginfig{@caption[id=fig-1]{This is my caption}}")
    for count, src in enumerate(srcs):
        # Create a label manager
        label_man = LabelManager()

        # Create a mock local_context and global_context
        doc = Document(src_filepath='src/main.dm',
                       targets={'.html': 'html/main.html',
                                '.tex': 'tex/main.tex'})
        doc.local_context.update({'_document': doc,
                                  'figure_label': "Fig. {number}"})
        doc.global_context.update({'_label_manager': label_man})

        # Generate a tag and compare the generated tex to the answer key
        root = process_ast(src, local_context=doc.local_context,
                           global_context=doc.global_context)

        # Test the caption's html
        # The following root tags have to be stripped for the html strings
        root_start = '<span class="root">'
        root_end = '</span>\n'

        root_html = root.html()
        # Remove the root tag
        root_html = root_html[len(root_start):]  # strip the start
        root_html = root_html[:(len(root_html) - len(root_end))]  # strip end
        assert root_html == ('\n  <span class="marginfig">\n'
                             '    <span class="caption">\n'
                             '      <span id="fig-1" class="figure-label">'
                             'Fig. 1</span>\n'
                             '      <span class="caption-text">This is my '
                             'caption</span>\n'
                             '    </span>\n'
                             '  </span>\n')


def test_figure_caption_with_id_tex():
    """Tests the tex generation of captions in figure tags when an id is
    specified."""
    # Test two cases: one in which the id is in the figure tag, and one in which
    # the id is in the caption tag
    srcs = ("@marginfig[id=fig-1]{@caption{This is my caption}}",
            "@marginfig{@caption[id=fig-1]{This is my caption}}")
    for count, src in enumerate(srcs):
        # Create a label manager
        label_man = LabelManager()

        # Create a mock local_context and global_context
        doc = Document(src_filepath='src/main.dm',
                       targets={'.html': 'html/main.html',
                                '.tex': 'tex/main.tex'})
        doc.local_context.update({'_document': doc,
                                  'figure_label': "Fig. {number}"})
        doc.global_context.update({'_label_manager': label_man})

        # Generate a tag and compare the generated tex to the answer key
        root = process_ast(src, local_context=doc.local_context,
                           global_context=doc.global_context)

        root_tex = root.tex()
        print(root_tex)
        assert root_tex == ('\n\\begin{marginfigure}\n'
                            'Fig. 1 \\caption{This is my caption}\n'
                            '\\end{marginfigure}\n')


def test_ref_missing():
    """Test the ref tag for a missing caption"""
    # Create a label manager
    label_man = LabelManager()

    # Create a mock local_context and global_context
    doc = Document(src_filepath='src/main.dm',
                   targets={'.html': 'html/main.html',
                            '.tex': 'tex/main.tex'})
    doc.local_context.update({'_document': doc,
                              'figure_label': "Fig. {number}"})
    doc.global_context.update({'_label_manager': label_man})

    # Generate the markup without an id
    src = "@ref{test} @caption{This is my caption}"

    # Generate a tag and compare the generated tex to the answer key
    root = process_ast(src, local_context=doc.local_context,
                       global_context=doc.global_context)

    # Trying to convert the root ast to a target type, like html, will raise
    # an LabelNotFound error
    with pytest.raises(LabelNotFound):
        root.html()

    # Naked captions do not register labels
    assert len(label_man.labels) == 0


def test_ref_html():
    """Test the ref tag for a present caption in the html format"""
    # Create a label manager
    label_man = LabelManager()

    # Create a mock local_context and global_context
    doc = Document(src_filepath='src/main.dm',
                   targets={'.html': 'html/main.html',
                            '.tex': 'tex/main.tex'})
    doc.local_context.update({'_document': doc,
                              '_src_filepath': doc.src_filepath,
                              'figure_label': "Fig. {number}",
                              'figure_ref': "Fig. {number}",})
    doc.global_context.update({'_label_manager': label_man})

    # Generate the markup with an id. The marginfig tag is needed to
    # set the kind of the label.
    src = "@ref{test} @marginfig{@caption[id=test]{This is my caption}}"

    # Generate a tag and compare the generated tex to the answer key
    root = process_ast(src, local_context=doc.local_context,
                       global_context=doc.global_context)

    #  Test the ref's html
    root_html = root.html()

    # The following root tags have to be stripped for the html strings
    root_start = '<span class="root">'
    root_end = '</span>\n'

    # Remove the root tag
    root_html = root_html[len(root_start):]  # strip the start
    root_html = root_html[:(len(root_html) - len(root_end))]  # strip end

    assert ('<a class="figure-ref" href="/html/main.html#test">'
            'Fig. 1</a>') in root_html


def test_ref_tex():
    """Test the ref tag for a present caption in the texformat"""
    # Create a label manager
    label_man = LabelManager()

    # Create a mock local_context and global_context
    doc = Document(src_filepath='src/main.dm',
                   targets={'.html': 'html/main.html',
                            '.tex': 'tex/main.tex'})
    doc.local_context.update({'_document': doc,
                              'figure_label': "Fig. {number}",
                              'figure_ref': "Fig. {number}"})
    doc.global_context.update({'_label_manager': label_man})

    # Generate the markup with an id. The marginfig tag is needed to
    # set the kind of the label.
    src = "@ref{test} @marginfig{@caption[id=test]{This is my caption}}"

    # Generate a tag and compare the generated tex to the answer key
    root = process_ast(src, local_context=doc.local_context,
                       global_context=doc.global_context)

    #  Test the ref's html
    root_tex = root.tex()
    assert root_tex.startswith('Fig. 1')
