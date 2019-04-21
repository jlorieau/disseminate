"""
Utilities for formatting tex strings and text.
"""
from ..exceptions import TagError
from ...attributes import Attributes
from ...utils.string import space_indent
from ... import settings


def tex_cmd(cmd, attributes='', formatted_content=None, indent=None):
    """Format a tex command.

    Parameters
    ----------
    com : str, optional
        The name of the LaTeX command to format.
    attributes : :obj:`Attributes <diseeminate.attributes.Attributes>` or str
        The attributes of the tag.
    formatted_content : str, optional
        The contents of the tex environment formatted as a string in LaTeX.
        If not specified, the tex_str will not be used as a LaTeX parameter
    indent : int, optional
        If specified, indent lines by the given number of spaces.

    Returns
    -------
    tex_env : str
        The LaTeX environment string

    Raises
    ------
    TagError
        A TagError is raised if:

        - an non-allowed environment is used
    """
    # Make sure the environment is permitted
    if cmd not in settings.tex_cmd_arguments:
        msg = "Cannot use the LaTeX command '{}'"
        raise TagError(msg.format(cmd))

    # Format the attributes
    attributes = (Attributes(attributes) if isinstance(attributes, str) else
                  attributes)

    # Get the required arguments
    reqs = attributes.filter(attrs=settings.tex_cmd_arguments[cmd],
                             target='tex')

    # Make sure the correct number of required arguments were found
    if len(reqs) != len(settings.tex_cmd_arguments[cmd]):
        msg = ("The LaTeX environment '{}' did not receive the correct "
               "required arguments. Required arguments received: {}")
        raise TagError(msg.format(cmd, reqs))

    # Get optional arguments
    if cmd in settings.tex_cmd_optionals:
        opts = attributes.filter(attrs=settings.tex_cmd_optionals[cmd],
                                 target='tex')
        opts_str = opts.tex_optionals
    else:
        opts_str = ''

    # Wrap the formatted_content in curly braces, if a formatted_content was specified
    if isinstance(formatted_content, str):
        formatted_content = ("{" + formatted_content + "}"
                             if formatted_content else "{}")
    else:
        formatted_content = ''

    # format the tex command
    tex_text = "\\" + cmd + reqs.tex_arguments + opts_str + formatted_content

    # Indent the text block, if specified
    if indent is not None:
        tex_text = space_indent(tex_text, number=indent)

    return tex_text


def tex_env(env, attributes, formatted_content, min_newlines=False,
            indent=None):
    """Format a tex environment.

    Parameters
    ----------
    env : str
        The name of the LaTeX environment to format.
    attributes : :obj:`Attributes <diseeminate.attributes.Attributes>` or str
        The attributes of the tag.
    formatted_content : str
        The contents of the tex environment formatted as a string in LaTeX.
    min_newlines : bool, optional
        If True, extra new lines before, after and in the environment will not
        be included.
    indent : int, optional
        If specified, indent lines by the given number of spaces.

    Returns
    -------
    tex_env : str
        The LaTeX environment string

    Raises
    ------
    TagError
        A TagError is raised if:

        - an non-allowed environment is used
    """
    # Make sure the environment is permitted
    if env not in settings.tex_env_arguments:
        msg = "Cannot use the LaTeX environment '{}'"
        raise TagError(msg.format(env))

    # Format the attributes
    attributes = (Attributes(attributes) if isinstance(attributes, str) else
                  attributes)

    # Get the required arguments
    reqs = attributes.filter(attrs=settings.tex_env_arguments[env],
                             target='tex',
                             sort_by_attrs=True)

    # Make sure the correct number of required arguments were found
    if len(reqs) != len(settings.tex_env_arguments[env]):
        msg = ("The LaTeX environment '{}' did not receive the correct "
               "required arguments. Required arguments received: {}")
        raise TagError(msg.format(env, reqs))

    # Get optional arguments
    if env in settings.tex_env_optionals:
        opts = attributes.filter(attrs=settings.tex_env_optionals[env],
                                 target='tex',
                                 sort_by_attrs=True)
        opts_str = opts.tex_optionals
    else:
        opts_str = ''

    # Add a leading and trailing new line to the formatted_content,
    # if there isn't one
    formatted_content = ('\n' + formatted_content
                         if not formatted_content.startswith('\n') else
                         formatted_content)
    formatted_content = (formatted_content + '\n'
                         if not formatted_content.endswith('\n') else
                         formatted_content)

    # format the tex environment
    tex_text = ("\\begin" + '{' + env + '}' +
                reqs.tex_arguments +
                opts_str +
                (' %' if min_newlines else '') +
                formatted_content +
                "\\end{" + env + "}")

    # Indent the text block, if specified
    if indent is not None:
        tex_text = space_indent(tex_text, number=indent)

    # Add new_lines on the two ends of the block, if not min_newlines
    if not min_newlines:
        tex_text = "\n" + tex_text + "\n"

    return tex_text
