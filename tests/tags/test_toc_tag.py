"""
Test the TOC tag.
"""
from disseminate import Document, SourcePath, TargetPath
from disseminate.tags.toc import Toc
from disseminate.utils.tests import strip_leading_space


def test_toc_changes(tmpdir):
    """Test the generation of tocs when the label manager changes."""
    # Setup a test document
    src_path = SourcePath(project_root=tmpdir, subpath='src')
    src_path.mkdir()
    src_filepath = SourcePath(project_root=src_path, subpath='test.dm')
    target_root = TargetPath(tmpdir)

    markup = """
    ---
    title: my first file
    relative_links: False
    ---
    @section[id=heading1]{My first heading}
    """
    src_filepath.write_text(strip_leading_space(markup))

    # Create the document and render
    doc = Document(src_filepath=src_filepath, target_root=target_root)
    doc.render()

    # Make sure the 'base_url' entry matches a basic format.
    doc.context['base_url'] = '/{target}/{subpath}'

    # Match the abbreviated toc
    toc = Toc(name='toc', content='all documents abbreviated',
              attributes=tuple(),
              context=doc.context)
    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/test.html">my first file</a>
    </span>
  </li>
  <ul class="toc-level-2">
    <li>
      <span class="ref">
        <a href="/html/test.html#heading1"><span class="number">1.</span> My first heading</a>
      </span>
    </li>
  </ul>
</ul>
"""
    assert toc.html == key

    # Change the document
    markup = """
    ---
    title: my first file
    relative_links: False
    ---
    @section[id=heading1]{My first heading}
    @subsection[id=subheading1]{My first sub-heading}
    """
    src_filepath.write_text(strip_leading_space(markup))
    doc.render()

    # Match the abbreviated toc
    toc = Toc(name='toc', content='all documents abbreviated',
              attributes=tuple(),
              context=doc.context)
    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/test.html">my first file</a>
    </span>
  </li>
  <ul class="toc-level-2">
    <li>
      <span class="ref">
        <a href="/html/test.html#heading1"><span class="number">1.</span> My first heading</a>
      </span>
    </li>
    <ul class="toc-level-3">
      <li>
        <span class="ref">
          <a href="/html/test.html#subheading1"><span class="number">1.1.</span> My first sub-heading</a>
        </span>
      </li>
    </ul>
  </ul>
</ul>
"""
    assert toc.html == key


# html tests

def test_toc_heading_html(tmpdir):
    """Test the generation of tocs from headings for html"""
    # The 'tests/tags/toc_example1' directory contains one markup in the root
    # directory, file1.dm, and two files, file21.dm and file22.dm, in the
    # 'sub' sub-directory. file1.dm includes file21.dm and file22.dm
    # Setup paths
    src_filepath = SourcePath(project_root='tests/tags/toc_example1',
                              subpath='file1.dm')
    target_root = TargetPath(tmpdir)

    doc = Document(src_filepath, target_root)

    # Make sure the 'base_url' entry matches a basic format.
    doc.context['base_url'] = '/{target}/{subpath}'
    doc.context['relative_links'] = False

    # Create a toc for all headings
    toc = Toc(name='toc', content='all headings', attributes=tuple(),
              context=doc.context)

    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/file1.html#sec:file1-dm-heading-1"><span class="number">1.</span> Heading 1</a>
    </span>
  </li>
  <li>
    <span class="ref">
      <a href="/html/file1.html#sec:file1-dm-heading-2"><span class="number">2.</span> Heading 2</a>
    </span>
  </li>
  <ul class="toc-level-2">
    <li>
      <span class="ref">
        <a href="/html/file1.html#subsec:file1-dm-sub-heading-2-1"><span class="number">2.1.</span> sub-Heading 2.1</a>
      </span>
    </li>
    <li>
      <span class="ref">
        <a href="/html/file1.html#subsec:file1-dm-sub-heading-2-2"><span class="number">2.2.</span> sub-Heading 2.2</a>
      </span>
    </li>
    <ul class="toc-level-3">
      <li>
        <span class="ref">
          <a href="/html/file1.html#subsubsec:file1-dm-sub-sub-header-2-2-1"><span class="number">2.2.1.</span> sub-sub-Header 2.2.1</a>
        </span>
      </li>
    </ul>
    <li>
      <span class="ref">
        <a href="/html/file1.html#subsec:file1-dm-sub-heading-2-3"><span class="number">2.3.</span> sub-Heading 2.3</a>
      </span>
    </li>
  </ul>
  <li>
    <span class="ref">
      <a href="/html/file1.html#sec:file1-dm-heading-3"><span class="number">3.</span> Heading 3</a>
    </span>
  </li>
  <ul class="toc-level-2">
    <li>
      <span class="ref">
        <a href="/html/file1.html#subsubsec:file1-dm-sub-sub-header-3-1-1"><span class="number">3.1.</span> sub-sub-header 3.1.1</a>
      </span>
    </li>
  </ul>
  <li>
    <span class="ref">
      <a href="/html/file1.html#sec:file1-dm-heading-4"><span class="number">4.</span> Heading 4</a>
    </span>
  </li>
</ul>
"""
    assert toc.html == key

    # The 'tests/tags/toc_example2' directory contains three markup files:
    # file1.dm, file2.dm and file3.dm. The 'file1.dm' includes 'file2.dm' and
    # 'file3.dm' The 'file2.dm' has a header and a sub-header.
    # This test has headers with id anchors specified.
    src_filepath = SourcePath(project_root='tests/tags/toc_example2',
                              subpath='file1.dm')
    doc = Document(src_filepath, target_root)

    # Make sure the 'base_url' entry matches a basic format.
    doc.context['base_url'] = '/{target}/{subpath}'
    doc.context['relative_links'] = False

    # Create a toc for all headings
    toc = Toc(name='toc', content='all headings', attributes=tuple(),
              context=doc.context)

    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/file1.html#heading-1"><span class="number">1.</span> Heading 1</a>
    </span>
  </li>
  <li>
    <span class="ref">
      <a href="/html/file2.html#heading-2"><span class="number">2.</span> Heading 2</a>
    </span>
  </li>
  <ul class="toc-level-2">
    <li>
      <span class="ref">
        <a href="/html/file2.html#subheading-2"><span class="number">2.1.</span> sub-Heading 2</a>
      </span>
    </li>
  </ul>
  <li>
    <span class="ref">
      <a href="/html/file3.html#heading-3"><span class="number">3.</span> Heading 3</a>
    </span>
  </li>
</ul>
"""
    assert toc.html == key

    # Create a toc for the root document, file1.dm, only.
    toc = Toc(name='toc', content='headings', attributes=tuple(),
              context=doc.context)

    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/file1.html#heading-1"><span class="number">1.</span> Heading 1</a>
    </span>
  </li>
</ul>
"""
    assert toc.html == key


def test_toc_header_html(tmpdir):
    """Test the creation of a chapter header for TOCs in html."""

    # The 'tests/tags/toc_example2' directory contains three markup files:
    # file1.dm, file2.dm and file3.dm. The 'file1.dm' includes 'file2.dm' and
    # 'file3.dm' The 'file2.dm' has a header and a sub-header.
    # This test has headers with id anchors specified.
    # Setup paths
    src_filepath = SourcePath(project_root='tests/tags/toc_example2',
                              subpath='file1.dm')
    target_root = TargetPath(tmpdir)
    doc = Document(src_filepath, target_root)

    # Make sure the 'base_url' entry matches a basic format.
    doc.context['base_url'] = '/{target}/{subpath}'
    doc.context['relative_links'] = False

    # Create a toc for the root document, file1.dm, only.
    toc = Toc(name='toc', content='headings', attributes=tuple(),
              context=doc.context)

    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/file1.html#heading-1"><span class="number">1.</span> Heading 1</a>
    </span>
  </li>
</ul>
"""
    assert toc.html == key

    # Now try adding the header
    toc = Toc(name='toc', content='headings', attributes=('header',),
              context=doc.context)

    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/file1.html#heading-1"><span class="number">1.</span> Heading 1</a>
    </span>
  </li>
</ul>
"""
    assert  toc.html == key

    # Make sure a label was not created for the heading
    label_manager = doc.context['label_manager']
    assert len(label_manager.get_labels(kinds='chapter')) == 0


def test_toc_document_html(tmpdir):
    """Test the generation of tocs for documents in html."""
    # The 'tests/tags/toc_example1' directory contains three markup files:
    # file1.dm, in the root folder, and file21.dm and file2.dm in the 'sub'
    # folder. The 'file1.dm' includes 'file21.dm' and 'file22.dm'.
    # Setup the paths
    src_filepath = SourcePath(project_root='tests/tags/toc_example1',
                              subpath='file1.dm')
    target_root = TargetPath(tmpdir)
    doc = Document(src_filepath, target_root)

    # Make sure the 'base_url' entry matches a basic format.
    doc.context['base_url'] = '/{target}/{subpath}'
    doc.context['relative_links'] = False

    # Create the tag for document2
    toc = Toc(name='toc', content='all documents', attributes=tuple(),
              context=doc.context)

    # Match the default toc (format: 'collapsed')
    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/file1.html">file1</a>
    </span>
  </li>
  <ul class="toc-level-2">
    <li>
      <span class="ref">
        <a href="/html/sub/file21.html">sub/file21</a>
      </span>
    </li>
    <li>
      <span class="ref">
        <a href="/html/sub/file22.html">sub/file22</a>
      </span>
    </li>
  </ul>
</ul>
"""
    assert toc.html == key

    # Match the collapsed toc
    toc = Toc(name='toc', content='all documents collapsed', attributes=tuple(),
              context=doc.context)
    assert key == toc.html

    # Match the expanded toc
    toc = Toc(name='toc', content='all documents expanded', attributes=tuple(),
              context=doc.context)
    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/file1.html">file1</a>
    </span>
  </li>
  <ul class="toc-level-2">
    <li>
      <span class="ref">
        <a href="/html/file1.html#sec:file1-dm-heading-1"><span class="number">1.</span> Heading 1</a>
      </span>
    </li>
    <li>
      <span class="ref">
        <a href="/html/file1.html#sec:file1-dm-heading-2"><span class="number">2.</span> Heading 2</a>
      </span>
    </li>
    <ul class="toc-level-3">
      <li>
        <span class="ref">
          <a href="/html/file1.html#subsec:file1-dm-sub-heading-2-1"><span class="number">2.1.</span> sub-Heading 2.1</a>
        </span>
      </li>
      <li>
        <span class="ref">
          <a href="/html/file1.html#subsec:file1-dm-sub-heading-2-2"><span class="number">2.2.</span> sub-Heading 2.2</a>
        </span>
      </li>
      <ul class="toc-level-4">
        <li>
          <span class="ref">
            <a href="/html/file1.html#subsubsec:file1-dm-sub-sub-header-2-2-1"><span class="number">2.2.1.</span> sub-sub-Header 2.2.1</a>
          </span>
        </li>
      </ul>
      <li>
        <span class="ref">
          <a href="/html/file1.html#subsec:file1-dm-sub-heading-2-3"><span class="number">2.3.</span> sub-Heading 2.3</a>
        </span>
      </li>
    </ul>
    <li>
      <span class="ref">
        <a href="/html/file1.html#sec:file1-dm-heading-3"><span class="number">3.</span> Heading 3</a>
      </span>
    </li>
    <ul class="toc-level-3">
      <li>
        <span class="ref">
          <a href="/html/file1.html#subsubsec:file1-dm-sub-sub-header-3-1-1"><span class="number">3.1.</span> sub-sub-header 3.1.1</a>
        </span>
      </li>
    </ul>
    <li>
      <span class="ref">
        <a href="/html/file1.html#sec:file1-dm-heading-4"><span class="number">4.</span> Heading 4</a>
      </span>
    </li>
  </ul>
  <li>
    <span class="ref">
      <a href="/html/sub/file21.html">sub/file21</a>
    </span>
  </li>
  <li>
    <span class="ref">
      <a href="/html/sub/file22.html">sub/file22</a>
    </span>
  </li>
</ul>
"""
    assert toc.html == key

    # Match the abbreviated toc
    toc = Toc(name='toc', content='all documents abbreviated',
              attributes=tuple(),
              context=doc.context)
    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/file1.html">file1</a>
    </span>
  </li>
  <ul class="toc-level-2">
    <li>
      <span class="ref">
        <a href="/html/file1.html#sec:file1-dm-heading-1"><span class="number">1.</span> Heading 1</a>
      </span>
    </li>
    <li>
      <span class="ref">
        <a href="/html/file1.html#sec:file1-dm-heading-2"><span class="number">2.</span> Heading 2</a>
      </span>
    </li>
    <ul class="toc-level-3">
      <li>
        <span class="ref">
          <a href="/html/file1.html#subsec:file1-dm-sub-heading-2-1"><span class="number">2.1.</span> sub-Heading 2.1</a>
        </span>
      </li>
      <li>
        <span class="ref">
          <a href="/html/file1.html#subsec:file1-dm-sub-heading-2-2"><span class="number">2.2.</span> sub-Heading 2.2</a>
        </span>
      </li>
      <ul class="toc-level-4">
        <li>
          <span class="ref">
            <a href="/html/file1.html#subsubsec:file1-dm-sub-sub-header-2-2-1"><span class="number">2.2.1.</span> sub-sub-Header 2.2.1</a>
          </span>
        </li>
      </ul>
      <li>
        <span class="ref">
          <a href="/html/file1.html#subsec:file1-dm-sub-heading-2-3"><span class="number">2.3.</span> sub-Heading 2.3</a>
        </span>
      </li>
    </ul>
    <li>
      <span class="ref">
        <a href="/html/file1.html#sec:file1-dm-heading-3"><span class="number">3.</span> Heading 3</a>
      </span>
    </li>
    <ul class="toc-level-3">
      <li>
        <span class="ref">
          <a href="/html/file1.html#subsubsec:file1-dm-sub-sub-header-3-1-1"><span class="number">3.1.</span> sub-sub-header 3.1.1</a>
        </span>
      </li>
    </ul>
    <li>
      <span class="ref">
        <a href="/html/file1.html#sec:file1-dm-heading-4"><span class="number">4.</span> Heading 4</a>
      </span>
    </li>
  </ul>
  <li>
    <span class="ref">
      <a href="/html/sub/file21.html">sub/file21</a>
    </span>
  </li>
  <li>
    <span class="ref">
      <a href="/html/sub/file22.html">sub/file22</a>
    </span>
  </li>
</ul>
"""
    assert toc.html == key

    # Test the collapsed toc for only the root document
    toc = Toc(name='toc', content='documents', attributes=tuple(),
              context=doc.context)

    # Match the default toc (collapsed)
    key = """<ul class="toc-level-1">
  <li>
    <span class="ref">
      <a href="/html/file1.html">file1</a>
    </span>
  </li>
</ul>
"""
    assert toc.html == key


def test_toc_relative_links_html(tmpdir):
    """Test the generation of tocs with relative links for html"""
    # The 'tests/tags/toc_example1' directory contains three markup files:
    # file1.dm, in the root folder, and file21.dm and file2.dm in the 'sub'
    # folder. The 'file1.dm' includes 'file21.dm' and 'file22.dm'.
    # Setup the paths
    src_filepath = SourcePath(project_root='tests/tags/toc_example1',
                              subpath='file1.dm')
    target_root = TargetPath(tmpdir)
    doc = Document(src_filepath, target_root)

    # Make sure the 'base_url' entry matches a basic format.
    doc.context['base_url'] = '/{target}/{subpath}'
    doc.context['relative_links'] = True

    # Create the tag for document2
    toc = Toc(name='toc', content='all documents', attributes=tuple(),
              context=doc.context)

    # Match the default toc (format: 'collapsed')
    key = """<ul class="toc-level-1">
      <li>
        <span class="ref">
          <a href="file1.html">file1</a>
        </span>
      </li>
      <ul class="toc-level-2">
        <li>
          <span class="ref">
            <a href="sub/file21.html">sub/file21</a>
          </span>
        </li>
        <li>
          <span class="ref">
            <a href="sub/file22.html">sub/file22</a>
          </span>
        </li>
      </ul>
    </ul>
    """
    assert toc.html == strip_leading_space(key)


# tex tests

def test_toc_heading_tex(tmpdir):
    """Test the generation of tocs from headings for tex"""
    # The 'tests/tags/toc_example1' directory contains one markup in the root
    # directory, file1.dm, and two files, file21.dm and file22.dm, in the
    # 'sub' sub-directory. file1.dm includes file21.dm and file22.dm
    # None of these files have explicit header ids, so generic ones are created.
    # Setup paths
    src_filepaths = SourcePath(project_root='tests/tags/toc_example1',
                               subpath='file1.dm')
    target_root = TargetPath(tmpdir)
    doc = Document(src_filepaths, target_root)

    # Create a toc for all headings
    toc = Toc(name='toc', content='all headings', attributes=tuple(),
              context=doc.context)

    key = """\\begin{toclist}
  \\item \\hyperref[sec:file1-dm-heading-1]{1. Heading 1} \\hfill \\pageref{sec:file1-dm-heading-1}
  \\item \\hyperref[sec:file1-dm-heading-2]{2. Heading 2} \\hfill \\pageref{sec:file1-dm-heading-2}
  \\begin{toclist}
    \\item \\hyperref[subsec:file1-dm-sub-heading-2-1]{2.1. sub-Heading 2.1} \\hfill \\pageref{subsec:file1-dm-sub-heading-2-1}
    \\item \\hyperref[subsec:file1-dm-sub-heading-2-2]{2.2. sub-Heading 2.2} \\hfill \\pageref{subsec:file1-dm-sub-heading-2-2}
    \\begin{toclist}
      \\item \\hyperref[subsubsec:file1-dm-sub-sub-header-2-2-1]{2.2.1. sub-sub-Header 2.2.1} \\hfill \\pageref{subsubsec:file1-dm-sub-sub-header-2-2-1}
    \\end{toclist}
    \\item \\hyperref[subsec:file1-dm-sub-heading-2-3]{2.3. sub-Heading 2.3} \\hfill \\pageref{subsec:file1-dm-sub-heading-2-3}
  \\end{toclist}
  \\item \\hyperref[sec:file1-dm-heading-3]{3. Heading 3} \\hfill \\pageref{sec:file1-dm-heading-3}
  \\begin{toclist}
    \\item \\hyperref[subsubsec:file1-dm-sub-sub-header-3-1-1]{3.1. sub-sub-header 3.1.1} \\hfill \\pageref{subsubsec:file1-dm-sub-sub-header-3-1-1}
  \\end{toclist}
  \\item \\hyperref[sec:file1-dm-heading-4]{4. Heading 4} \\hfill \\pageref{sec:file1-dm-heading-4}
\\end{toclist}
"""
    assert key == toc.tex

    # The 'tests/tags/toc_example2' directory contains three markup files:
    # file1.dm, file2.dm and file3.dm. The 'file1.dm' includes 'file2.dm' and
    # 'file3.dm' The 'file2.dm' has a header and a sub-header.
    # This test has headers with id anchors specified.
    # Setup paths
    src_filepaths = SourcePath(project_root='tests/tags/toc_example2',
                               subpath='file1.dm')
    doc = Document(src_filepaths, target_root)

    # Create a toc for all headings
    toc = Toc(name='toc', content='all headings', attributes=tuple(),
              context=doc.context)

    key = """\\begin{toclist}
  \\item \\hyperref[heading-1]{1. Heading 1} \\hfill \\pageref{heading-1}
  \\item \\hyperref[heading-2]{2. Heading 2} \\hfill \\pageref{heading-2}
  \\begin{toclist}
    \\item \\hyperref[subheading-2]{2.1. sub-Heading 2} \\hfill \\pageref{subheading-2}
  \\end{toclist}
  \\item \\hyperref[heading-3]{3. Heading 3} \\hfill \\pageref{heading-3}
\\end{toclist}
"""
    assert key == toc.tex

    # Create a toc for the headings of file1.dm only.
    toc = Toc(name='toc', content='headings', attributes=tuple(),
              context=doc.context)

    key = """\\begin{toclist}
  \\item \\hyperref[heading-1]{1. Heading 1} \\hfill \\pageref{heading-1}
\\end{toclist}
"""
    assert key == toc.tex


def test_toc_header_tex(tmpdir):
    """Test the creation of a chapter header for TOCs in tex."""
    # The 'tests/tags/toc_example2' directory contains three markup files:
    # file1.dm, file2.dm and file3.dm. The 'file1.dm' includes 'file2.dm' and
    # 'file3.dm' The 'file2.dm' has a header and a sub-header.
    # This test has headers with id anchors specified.
    # Setup paths
    src_filepath = SourcePath(project_root='tests/tags/toc_example2',
                              subpath='file1.dm')
    target_root = TargetPath(tmpdir)
    doc = Document(src_filepath, target_root)

    # Create a toc for the root document, file1.dm, only.
    toc = Toc(name='toc', content='headings', attributes=tuple(),
              context=doc.context)

    key = """\\begin{toclist}
  \\item \\hyperref[heading-1]{1. Heading 1} \\hfill \\pageref{heading-1}
\\end{toclist}
"""
    tex = toc.tex
    assert key == tex

    # Now try adding the header
    toc = Toc(name='toc', content='headings', attributes=('header'),
              context=doc.context)

    key = """\\begin{toclist}
  \\item \\hyperref[heading-1]{1. Heading 1} \\hfill \\pageref{heading-1}
\\end{toclist}
"""
    tex = toc.tex
    assert key == tex

    # Make sure a label was not created for the heading
    label_manager = doc.context['label_manager']
    assert len(label_manager.get_labels(kinds='chapter')) == 0


def test_toc_document_tex(tmpdir):
    """Test the generation of tocs for documents in latex."""
    # The 'tests/tags/toc_example1' directory contains three markup files:
    # file1.dm, in the root folder, and file21.dm and file2.dm in the 'sub'
    # folder. The 'file1.dm' includes 'file21.dm' and 'file22.dm'.
    # Setup paths
    src_filepath = SourcePath(project_root='tests/tags/toc_example1',
                              subpath='file1.dm')
    target_root = TargetPath(tmpdir)
    doc = Document(src_filepath, target_root)

    # Create the tag for document2
    toc = Toc(name='toc', content='all documents', attributes=tuple(),
              context=doc.context)

    key = """\\begin{toclist}
  \\item \\hyperref[doc:file1.dm]{file1} \\hfill \\pageref{doc:file1.dm}
  \\begin{toclist}
    \\item \\hyperref[doc:sub/file21.dm]{sub/file21} \\hfill \\pageref{doc:sub/file21.dm}
    \\item \\hyperref[doc:sub/file22.dm]{sub/file22} \\hfill \\pageref{doc:sub/file22.dm}
  \\end{toclist}
\\end{toclist}
"""
    assert key == toc.tex
