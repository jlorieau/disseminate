"""
Test the PdfBuilder
"""
import pathlib
from collections import namedtuple

from disseminate.builders.target_builders.pdf_builder import PdfBuilder
from disseminate.paths import TargetPath


def test_pdf_builder_setup_pdf_in_targets(env):
    """Test the setup of a PdfBuilder when 'pdf' is listed as a target
    in the context['targets']"""
    context = env.context
    src_filepath = context['src_filepath']
    target_root = context['target_root']

    # 1. Setup the builder without an outfilepath.  In this case, 'tex' is not
    #    listed in the targets but 'pdf is, so the outfilepath will *not*
    #    be in the cache directory
    context['targets'] -= {'tex'}
    context['targets'] |= {'pdf'}
    target_tex_filepath = TargetPath(target_root=target_root / '.cache',
                                     target='tex', subpath='test.tex')
    target_pdf_filepath = TargetPath(target_root=target_root,
                                     target='pdf', subpath='test.pdf')
    builder = PdfBuilder(env, context=context)

    # check the build
    assert not target_pdf_filepath.exists()
    assert len(builder.subbuilders) == 2

    tex_builder = builder.subbuilders[0]
    assert tex_builder.__class__.__name__ == 'TexBuilder'
    assert tex_builder.target == 'tex'
    assert len(tex_builder.subbuilders[1].infilepaths) > 0
    assert tex_builder.subbuilders[1].outfilepath == target_tex_filepath
    assert tex_builder.infilepaths == [src_filepath]
    assert tex_builder.outfilepath == target_tex_filepath

    pdf_builder = builder.subbuilders[1]
    assert pdf_builder.__class__.__name__ == 'Pdflatex'
    assert pdf_builder.target == 'pdf'
    assert pdf_builder.infilepaths == [target_tex_filepath]
    assert pdf_builder.outfilepath == target_pdf_filepath

    assert builder.outfilepath == target_pdf_filepath

    assert builder.build_needed()
    assert builder.status == 'ready'


def test_pdf_builder_setup_pdf_tex_in_targets(env):
    """Test the setup of a PdfBuilder when 'pdf' and 'tex' are listed as a
    target in the context['targets']"""
    context = env.context
    src_filepath = context['src_filepath']
    target_root = context['target_root']

    # 2. Setup the builder without an outfilepath.  In this case, 'tex' and
    #    'pdf' are listed in the targets , so the outfilepaths will *not*
    #    be in the cache directory
    context['targets'] |= {'tex'}
    context['targets'] |= {'pdf'}

    target_tex_filepath = TargetPath(target_root=target_root,
                                     target='tex', subpath='test.tex')
    target_pdf_filepath = TargetPath(target_root=target_root,
                                     target='pdf', subpath='test.pdf')
    builder = PdfBuilder(env, context=context)

    # check the build
    assert not target_pdf_filepath.exists()
    assert len(builder.subbuilders) == 2

    assert builder.subbuilders[0].__class__.__name__ == 'TexBuilder'
    assert builder.subbuilders[0].target == 'tex'
    assert builder.subbuilders[0].infilepaths == [src_filepath]
    assert builder.subbuilders[0].outfilepath == target_tex_filepath

    assert builder.subbuilders[1].__class__.__name__ == 'Pdflatex'
    assert builder.subbuilders[1].target == 'pdf'
    assert builder.subbuilders[1].infilepaths == [target_tex_filepath]
    assert builder.subbuilders[1].outfilepath == target_pdf_filepath

    assert builder.outfilepath == target_pdf_filepath

    assert builder.build_needed()
    assert builder.status == 'ready'

    # 3. Setup the builder with an outfilepath
    target_pdf_filepath = TargetPath(target_root=target_root,
                                     target='pdf', subpath='final.pdf')
    builder = PdfBuilder(env, context=context, outfilepath=target_pdf_filepath)

    # check the build
    assert not target_pdf_filepath.exists()
    assert len(builder.subbuilders) == 2

    assert builder.subbuilders[0].__class__.__name__ == 'TexBuilder'
    assert builder.subbuilders[0].target == 'tex'
    assert builder.subbuilders[0].infilepaths == [src_filepath]
    assert builder.subbuilders[0].outfilepath == target_tex_filepath

    assert builder.subbuilders[1].__class__.__name__ == 'Pdflatex'
    assert builder.subbuilders[1].target == 'pdf'
    assert builder.subbuilders[1].infilepaths == [target_tex_filepath]
    assert builder.subbuilders[1].outfilepath == target_pdf_filepath

    assert builder.outfilepath == target_pdf_filepath

    assert builder.build_needed()
    assert builder.status == 'ready'


def test_pdf_builder_setup_not_in_targets(env):
    """Test setuop of a PdfBuilder when 'tex' and 'pdf' are not listed as a
    target in the context['targets'] """
    context = env.context
    src_filepath = context['src_filepath']
    target_root = context['target_root']

    # 1. Setup the builder without an outfilepath
    context['targets'] -= {'pdf'}
    target_tex_filepath = TargetPath(target_root=target_root / '.cache',
                                     target='tex', subpath='test.tex')
    target_pdf_filepath = TargetPath(target_root=target_root / '.cache',
                                     target='pdf', subpath='test.pdf')
    builder = PdfBuilder(env, context=context)

    # check the build
    assert not target_pdf_filepath.exists()
    assert len(builder.subbuilders) == 2

    assert builder.subbuilders[0].__class__.__name__ == 'TexBuilder'
    assert builder.subbuilders[0].target == 'tex'
    assert builder.subbuilders[0].infilepaths == [src_filepath]
    assert builder.subbuilders[0].outfilepath == target_tex_filepath

    assert builder.subbuilders[1].__class__.__name__ == 'Pdflatex'
    assert builder.subbuilders[1].target == 'pdf'
    assert builder.subbuilders[1].infilepaths == [target_tex_filepath]
    assert builder.subbuilders[1].outfilepath == target_pdf_filepath

    assert builder.outfilepath == target_pdf_filepath

    assert builder.build_needed()
    assert builder.status == 'ready'


def test_pdf_builder_simple(env):
    """Test a simple build with the PdfBuilder """
    context = env.context
    tmpdir = context['target_root']

    # 1. Setup the builder without an outfilepath
    target_filepath = TargetPath(target_root=tmpdir / '.cache', target='pdf',
                                 subpath='test.pdf')
    tag = namedtuple('tag', 'tex')
    context['body'] = tag(tex="My body")  # expects {{ body.tex }}

    builder = PdfBuilder(env, context=context)

    # check the build
    assert builder.build_needed()
    assert builder.status == 'ready'
    assert not target_filepath.exists()
    assert len(builder.subbuilders) == 2

    # Try the build
    assert builder.build(complete=True) == 'done'
    assert builder.status == 'done'
    assert target_filepath.exists()

    # New builders don't need to rebuild.
    builder = PdfBuilder(env, context=context)
    assert builder.status == 'done'
