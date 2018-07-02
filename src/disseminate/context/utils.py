"""
Utilities for managing context dicts.
"""
import os.path


def context_targets(context):
    """Retrieve a list of targets from the 'targets' or 'target' entry of the
    context.

    Parameters
    ----------
    context : dict
        The context of a document containing all of the parameters needed
        to render the document

    Returns
    -------
    target_list : list or str
        A list of targets specified in the context.

    Examples
    --------
    >>> context_targets({'targets': 'html, pdf'})
    ['.html', '.pdf']
    >>> context_targets({'target': 'txt'})
    ['.txt']
    >>> context_targets({'target': ' '})
    []
    >>> context_targets({})
    []
    """
    # Get the targets from the context.
    # In the default context, this is set as the 'targets' entry, which
    # may be over-written by the user. However, a 'target' entry could be
    # used as well (for convenience), and it should be checked first, since
    # it overrides the default 'targets' entry.
    if 'target' in context:
        targets = context['target']
    elif 'targets' in context:
        targets = context['targets']
    else:
        targets = ''

    # Convert to a list, if needed
    target_list = (targets.split(',') if isinstance(targets, str) else
    targets)

    if len(target_list) == 1:
        target_list = [t.strip() for t in target_list[0].split(" ")]
    else:
        target_list = [t.strip() for t in target_list]

    if 'none' in target_list:
        return []

    # Remove empty entries
    target_list = list(filter(bool, target_list))

    # Add trailing period to extensions in target_list
    return [t if t.startswith('.') else '.' + t for t in target_list]


def context_includes(context, render_paths=True):
    """Retrieve a list of included subdocuments from from the 'include' entry
    of the context.

    Parameters
    ----------
    context : dict
        The context of a document containing all of the parameters needed
        to render the document
    render_paths : bool, optional
        If True and the document's 'src_filepath' entry is included, the
        returned paths will include the src_filepath's path and produce
        render paths--i.e. paths relative to the current path or absolute paths.

    Returns
    -------
    include_list : list of str
        A list of the paths for the included subdocuments..

    Examples
    --------
    >>> context_includes({'include': "  sub/file1.dm\\n  sub/file2.dm"})
    ['sub/file1.dm', 'sub/file2.dm']
    >>> context_includes({'include': "  sub/file 1.dm\\n  sub/file 2.dm"})
    ['sub/file 1.dm', 'sub/file 2.dm']
    >>> context_includes({'include': "  sub/file 1.dm\\n  \\nsub/file 2.dm"})
    ['sub/file 1.dm', 'sub/file 2.dm']
    >>> context_includes({'include': "  sub/file1.dm\\n  sub/file2.dm",
    ...                  'src_filepath': 'src/main.dm'})
    ['src/sub/file1.dm', 'src/sub/file2.dm']
    >>> context_includes({'include': "  sub/file1.dm\\n  sub/file2.dm",
    ...                  'src_filepath': 'src/main.dm'}, render_paths=False)
    ['sub/file1.dm', 'sub/file2.dm']
    >>> context_includes({})
    []
    """
    # Retrieve the include entry
    if 'include' in context:
        includes = context['include']
    elif 'includes' in context:
        includes = context['includes']
    else:
        includes = None

    # Make sure it's properly formatted as a string for further processing
    if not isinstance(includes, str):
        return []

    # Get the included subdocument paths. Strip extra space on the ends of
    # entries on each line and remove empty entries.
    includes = [path.strip() for path in includes.split('\n')
                if not path.isspace()]

    # Set the includes as render paths, if specified.
    if render_paths and 'src_filepath' in context:
        src_filepath = context['src_filepath']
        src_path = os.path.split(src_filepath)[0]
        includes = [os.path.join(src_path, path) for path in includes]

    return includes
