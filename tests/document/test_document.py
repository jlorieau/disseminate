"""
Tests for Document classes and functions.
"""
import pytest
from shutil import copyfile

from disseminate.document import Document, DocumentError
from disseminate.dependency_manager import DependencyManager, MissingDependency
from disseminate.labels import LabelManager


def test_basic_conversion_html(tmpdir):
    """Tests the conversion of a basic html file."""
    # Get a path to a temporary file
    temp_file = str(tmpdir.join("html")) + '/dummy.html'

    # Load the document and render it with no template
    doc = Document("tests/document/example1/dummy.dm",
                   str(tmpdir))
    doc.render()
    # Make sure the output matches the answer key
    with open(temp_file, 'r') as f, \
         open("tests/document/example1/test_basic_conversion_html.html") as g:
        assert f.read() == g.read()

    # An invalid file raises an error
    with pytest.raises(DocumentError):
        doc = Document("tests/document/missing.dm")


def test_ast_caching(tmpdir):
    """Tests the caching of the AST based on file modification times."""
    # Get a path to a temporary file
    temp_file = str(tmpdir.join("html")) + '/dummy.html'

    # Load the document and render it with no template. Opening the document
    # loads the ast.
    doc = Document("tests/document/example1/dummy.dm",
                   str(tmpdir))

    ast = doc._ast
    mtime = doc._mtime
    assert ast is not None
    assert mtime is not None

    # Try loading the AST again. At this point, it shouldn't be different
    doc.get_ast()
    assert ast == doc._ast
    assert mtime == doc._mtime


def test_target_filepath():
    """Test the target_filepath method."""
    doc = Document("tests/document/example1/dummy.dm")

    assert (doc.target_filepath('.html', render_path=True) ==
            "tests/document/html/dummy.html")
    assert (doc.target_filepath('.html', render_path=False) ==
            "dummy.html")
    assert (doc.target_filepath('.tex', render_path=True) ==
            "tests/document/tex/dummy.tex")
    assert (doc.target_filepath('.tex', render_path=False) ==
            "dummy.tex")


def test_custom_template(tmpdir):
    """Tests the loading of custom templates from the yaml header."""
    # Write a temporary file. We'll use the tree.html template, which contains
    # the text "Disseminate Project Index"
    tmpdir.mkdir('src')
    in_file = tmpdir.join('src').join("index.dm")
    out_file = tmpdir.join('html').join("index.html")
    input = ["---",
             "template: tree",
             "targets: html",
             "---",
             ""]
    in_file.write('\n'.join(input))

    # Make document
    doc = Document(str(in_file))
    doc.render()
    assert "Disseminate Project Index" in out_file.read()

    # Write to the file again, but don't include the template. This time it
    # shouldn't contain the text "Disseminate Project Index"
    in_file.write("test")
    doc.render()
    assert "Disseminate Project Index" not in out_file.read()


def test_local_context_update(tmpdir):
    """Tests that the context is properly updated in subsequent renders."""
    # First load a file with a header
    doc = Document("tests/document/example2/withheader.dm", str(tmpdir))
    doc.get_ast()

    # Check the contents  of the local_context
    assert 'title' in doc.context
    assert doc.context['title'] == 'My first title'

    assert 'author' in doc.context
    assert doc.context['author'] == 'Justin L Lorieau'

    assert 'macros' in doc.context

    # Get the local_context id to make sure it stays the same
    context_id = id(doc.context)

    # Now switch to a file without a header and make sure the header values
    # are removed
    doc.src_filepath = "tests/document/example2/noheader.dm"
    doc.get_ast(reload=True)

    # Check the contents  of the local_context
    assert 'title' not in doc.context
    assert 'author' not in doc.context
    assert 'macros' not in doc.context

    assert id(doc.context) == context_id


def test_local_macros(tmpdir):
    """Tests that macros defined in the header of a document are properly
    processed."""
    temp_file = tmpdir.join('html').join('withheader.html')

    # First load a file with a header
    doc = Document("tests/document/example2/withheader.dm",
                   str(tmpdir))
    doc.render()

    # See if the macro was properly replaced
    rendered_html = temp_file.read()

    assert '@macro' not in rendered_html
    assert '<i>example</i>' in rendered_html


def test_dependencies_img(tmpdir):
    """Tests that the image dependencies are correctly reset when the AST is
    reprocessed."""
    # Setup the project_root in a temp directory
    project_root = tmpdir.join('src')
    project_root.mkdir()
    target_root = str(tmpdir)

    # Copy a dependency image file to this directory
    img_path = str(project_root.join('sample.png'))
    copyfile('tests/document/example3/sample.png',
             img_path)

    # Make a document source file
    markup = """
---
targets: html
---
@img{sample.png}"""

    src_filepath = project_root.join('test.dm')
    src_filepath.write(markup)

    # Create a document
    doc = Document(str(src_filepath), tmpdir)

    # Check that the document and dependency manager paths are correct
    assert doc.project_root == str(project_root)
    assert doc.target_root == str(target_root)

    dep = doc.context['dependency_manager']
    assert dep.project_root == str(project_root)
    assert dep.target_root == str(target_root)

    # Render the document
    doc.render()

    # The img file should be a dependency in the '.html' target
    d = dep.get_dependency(target='.html', src_filepath=img_path)
    assert d.dep_filepath == 'sample.png'

    # Rewrite the document source file without the dependency
    markup = ""
    src_filepath.write(markup)

    # Render the document and the dependency should have been removed.
    doc.render()

    # A missing dependency raises a MissingDependency exception
    with pytest.raises(MissingDependency):
        d = dep.get_dependency(target='.html', src_filepath=img_path)


def test_document_labels(tmpdir):
    """Test the correct assignment of labels for a document."""

    # Setup the project_root in a temp directory
    project_root = tmpdir.join('src')
    project_root.mkdir()
    target_root = tmpdir

    # Make a document source file
    src_filepath = project_root.join('test.dm')
    src_filepath.ensure(file=True)  # touch the file

    # Create a document
    doc = Document(str(src_filepath), str(target_root))

    # 1. Test the label when the '_project_root' value is not assigned in the
    #    global_context. In this case, the label is identified by the document's
    #    src_filepath

    # The label should have been created on document creation and calling the
    # get_ast method
    man = doc.context['label_manager']
    assert len(man.labels) == 1
    label = man.get_label(id="doc:test.dm")
    assert label.id == "doc:test.dm"
    assert label.kind == ('document', 'document-level-1')


def test_document_tree(tmpdir):
    """Test the loading of trees from a document."""

    # Setup the project_root in a temp directory
    project_root = tmpdir.join('src').mkdir()

    # Populate some files
    file1 = project_root.join('main.dm')
    file1.write("""---
include:
  sub/file2.dm
  sub/file3.dm
targets: txt, tex
---
""")
    file2 = project_root.join('sub').join('file2.dm').ensure(file=True)
    file3 = project_root.join('sub').join('file3.dm').ensure(file=True)

    for text, f in (('file2', file2), ('file3', file3)):
        f.write(text)

    # Create the root document
    doc = Document(src_filepath=str(file1))

    # Test the paths
    assert len(doc.sub_documents) == 2
    assert doc.src_filepath == str(file1)

    keys = list(doc.sub_documents.keys())
    assert doc.sub_documents[keys[0]].src_filepath == str(file2)
    assert doc.sub_documents[keys[1]].src_filepath == str(file3)

