import regex


class TagAttributeError(Exception): pass


re_attrs = regex.compile(r'((?P<key>[\w\.]+)'
                         r'\s*=\s*'
                         r'(?P<value>("[^"]*"'
                         r'|\'[^\']*\''
                         r'|\w+))'
                         r'|(?P<position>\w+))')


def parse_attributes(s):
    """Parses an attribute string into an OrderedDict of attributes.

    Parameters
    ----------
    s: str
        Input string of attributes of the form: "key1 = value1 key2 = value2"

    Returns
    -------
    attrs: tuple
        A tuple of attributes comprising either 2-ple strings (key, value) or
        strings (positional arguments)

    Examples
    --------
    >>> parse_attributes("data=one red=two")
    (('data', 'one'), ('red', 'two'))
    >>> parse_attributes(" class='base bttnred' style= media red")
    (('class', 'base bttnred'), ('style', 'media'), 'red')
    >>> parse_attributes("class='base btn' skip")
    (('class', 'base btn'), 'skip')
    """
    attrs = []

    for m in re_attrs.finditer(s):
        d = m.groupdict()
        if d.get('key', None) and d.get('value', None):
            attrs.append((d['key'], d['value'].strip('"').strip("'")))
        elif d.get('position', None):
            attrs.append(d['position'].strip("'").strip('"'))

    return tuple(attrs)


def set_attribute(attrs, attribute, method='r'):
    """Set an attribute in an attributes list.

    Parameters
    ----------
    attrs: tuple
        A tuple of attributes comprising either 2-ple strings (key, value) or
        strings (positional arguments)
    attribute: 2-ple or str
        An attribute to set. It's either a 2 item tuple (attribute name, attribute value) or
        a positional attribute string.
    method: char
        'r': replace (default)
        'a': append

    Returns
    -------
    attrs: tuple
        A typle of attributes comprising either 2-ple strings (key, value) or
        strings (positional arguments)

    Examples
    --------
    >>> set_attribute([('class', 'base bttnred'), ('style', 'media'), 'red'],
    ...                ('class', 'standard'), method='r')
    (('class', 'standard'), ('style', 'media'), 'red')
    >>> set_attribute([('class', 'base bttnred'), ('style', 'media'), 'red'],
    ...                ('class', 'standard'), method='a')
    (('class', 'base bttnred'), ('style', 'media'), 'red', ('class', 'standard'))
    >>> set_attribute([('class', 'base bttnred'), ('style', 'media'), 'red'],
    ...                'red', method='r')
    (('class', 'base bttnred'), ('style', 'media'), 'red')
    >>> set_attribute([('class', 'base bttnred'), ('style', 'media'), 'red'],
    ...                'red', method='a')
    (('class', 'base bttnred'), ('style', 'media'), 'red', 'red')
    """
    attrs = tuple if attrs is None else attrs

    if method == 'a':
        new_attrs = list(attrs)
        new_attrs.append(attribute)
        return tuple(new_attrs)
    else:
        if hasattr(attribute, '__iter__') and len(attribute) == 2:
            name, value = attribute
            new_attrs = []
            attr_found = False

            for attr in attrs:
                if (hasattr(attr, '__iter__')
                   and len(attr) == 2
                   and attr[0] == name):

                    attr_found = True
                    new_attrs.append((name, value))
                else:
                    new_attrs.append(attr)
            if not attr_found:
                new_attrs.append((name, value))
            return tuple(new_attrs)
        else:
            new_attrs = list(attrs)
            if attribute not in new_attrs:
                new_attrs.append(attribute)
            return tuple(new_attrs)


def filter_attributes(attrs, attribute_names=None, target=None,
                      raise_error=False):
    """Filter a tuple of attributes (attrs) to only include those that match
    names (or positional attributes) in the given list.

    Parameters
    ----------
    attrs: tuple
        A tuple of attributes comprising either 2-ple strings (key, value) or
        strings (positional arguments)
    attribute_names: list of str, optional
        A list of attribute names and positional arguments to include in the
        returned result. Matches are case-sensitive.
    target: str, optional
        If specified, filter the target-specific attributes.
        Target-specific attributes start with the target name.
        For example, 'tex.width' is the 'width' attribute for '.tex' targets.
        If a target is specified, the filtered attributes will only include
        target-specific attributes that match the target, and the
        target-specific part will be stripped.
    raise_error: bool, optional
        If an attribute has been included that is not recognized, raise an
        TagAttributeError.

    Returns
    -------
    attrs: tuple
        A filtered tuple of attributes comprising either 2-ple strings
        (key, value) or strings (positional arguments)

    Raises
    ------
    TagAttributeError
        If raise_error and an attribute is given that is not in the list of
        attribute_names.

    Examples
    --------
    >>> filter_attributes([('class', 'base'), ('style', 'media'), 'red'],
    ...                   ['class', 'red'])
    (('class', 'base'), 'red')
    >>> filter_attributes([('tex.class', 'base'), ('html.class', 'media')],
    ...                   ['class', 'red'], '.tex')
    (('class', 'base'),)
    """
    new_attrs = []
    # Filter attributes based on target
    if target:
        target = target.strip('.')

        for attr in attrs:
            # See if the attribute matches a target and whether it matches
            # the specified target
            if hasattr(attr, '__iter__') and len(attr) == 2:
                # Deal with an attr that is a 2-ple
                if attr[0].startswith(target + '.'):
                    # matches target. ex: 'tex.width'
                    new_attrs.append((attr[0].replace(target + '.', ''),
                                      attr[1]))
                elif '.' in attr[0]:
                    # attr for another target. ex: 'html.width'
                    continue
                else:
                    new_attrs.append(attr)
            else:
                # Deal with an attr that is a string
                if attr.startswith(target + '.'):
                    # matches target. ex: 'tex.width'
                    new_attrs.append(attr.replace(target + '.', ''))
                elif '.' in attr:
                    # attr for another target. ex: 'html.width'
                    continue
                else:
                    new_attrs.append(attr)
        attrs = new_attrs

    if attribute_names:
        new_attrs = []
        # Filter attributes based on attribute names
        for attr in attrs:
            if (hasattr(attr, '__iter__')
               and len(attr) == 2
               and attr[0] in attribute_names):

                new_attrs.append(attr)
            elif attr in attribute_names:
                new_attrs.append(attr)
            elif raise_error:
                msg = "The attribute '{}' is not a valid attribute."
                raise TagAttributeError(msg.format(attr))
    return tuple(new_attrs)


def kwargs_attributes(attrs, attribute_names=None, raise_error=False):
    """Produce a dict of attributes {key: value} suitable to be used
    as kwargs.

    .. note:: This function ignores positional arguments.

    Parameters
    ----------
    attrs: tuple
        A tuple of attributes comprising either 2-ple strings (key, value) or
        strings (positional arguments)
    attribute_names: list of str, optional
        A list of attribute names and positional arguments to include in the
        returned result. Matches are case-sensitive.
    raise_error: bool, optional
        If an attribute has been included that is not recognized, raise an
        TagAttributeError.

    Returns
    -------
    kwargs: dict
        A dict with {key: value} pairs for the attributes.

    Examples
    --------
    >>> kwargs_attributes((('class', 'base'), ('style', 'media'), 'red'))
    {'class': 'base', 'style': 'media'}
    """
    if hasattr(attribute_names, '__iter__'):
        processed_attrs = filter_attributes(attrs, attribute_names, raise_error)
    else:
        processed_attrs = attrs

    kwargs = dict()
    for attr in processed_attrs:
        if hasattr(attr, '__iter__') and len(attr) == 2:
            kwargs[attr[0]] = attr[1]

    return kwargs


def format_html_attributes(attrs, attribute_names=None, raise_error=False):
    """Format attributes into an options string for html.

    .. note:: If there are target-specific attributes (i.e. they start with
              the target's name with a period, like 'html.width') then
              only the 'html.' attributes are added.

    Parameters
    ----------
    attrs: tuple
        A tuple of attributes comprising either 2-ple strings (key, value) or
        strings (positional arguments)
    attribute_names: list of str, optional
        A list of attribute names and positional arguments to include in the
        returned result. Matches are case-sensitive.
    raise_error: bool, optional
        If an attribute has been included that is not recognized, raise an
        TagAttributeError.

    Returns
    -------
    kwargs: dict
        A dict with {key: value} pairs for the attributes.

    Examples
    --------
    >>> format_html_attributes((('class', 'base'), ('style', 'media'), 'red'))
    "class='base' style='media' red"
    >>> format_html_attributes(())
    ''
    >>> format_html_attributes((('tex.width', '100'), ('html.width', '200')))
    "width='200'"
    >>> format_html_attributes((('tex.width', '200'), ))
    ''
    """
    # Convert the given attrs, if needed
    if attrs is None or attrs == '':
        attrs = tuple()
    elif isinstance(attrs, str):
        attrs = parse_attributes(attrs)
    else:
        pass

    if hasattr(attribute_names, '__iter__'):
        processed_attrs = filter_attributes(attrs=attrs,
                                            attribute_names=attribute_names,
                                            target='.html',
                                            raise_error=raise_error)
    else:
        processed_attrs = filter_attributes(attrs=attrs,
                                            target='.html',
                                            raise_error=raise_error)

    if processed_attrs:
        attr_elements = []
        for attr in processed_attrs:
                if isinstance(attr, tuple):
                    attr_elements.append(attr[0] + "='" + attr[1] + "'")
                elif isinstance(attr, str):
                    attr_elements.append(attr)
        return " ".join(attr_elements)
    else:
        return ""


def format_tex_attributes(attrs, attribute_names=None, raise_error=False):
    """Format attributes into an options string for tex.

    .. note:: If there are target-specific attributes (i.e. they start with
              the target's name with a period, like 'html.width') then
              only the 'tex.' attributes are added.

    Parameters
    ----------
    attrs: tuple
        A tuple of attributes comprising either 2-ple strings (key, value) or
        strings (positional arguments)
    attribute_names: list of str, optional
        A list of attribute names and positional arguments to include in the
        returned result. Matches are case-sensitive.
    raise_error: bool, optional
        If an attribute has been included that is not recognized, raise an
        TagAttributeError.

    Returns
    -------
    kwargs: dict
        A dict with {key: value} pairs for the attributes.

    Examples
    --------
    >>> format_tex_attributes((('class', 'base'), ('style', 'media'), 'red'))
    '[class=base, style=media, red]'
    >>> format_tex_attributes(())
    ''
    >>> format_tex_attributes((('tex.width', '100'), ('html.width', '200')))
    '[width=100]'
    >>> format_tex_attributes((('html.width', '200'), ))
    ''
    """
    # Convert the given attrs, if needed
    if attrs is None or attrs == '':
        attrs = tuple()
    elif isinstance(attrs, str):
        attrs = parse_attributes(attrs)
    else:
        pass

    if hasattr(attribute_names, '__iter__'):
        processed_attrs = filter_attributes(attrs=attrs,
                                            attribute_names=attribute_names,
                                            target='.tex',
                                            raise_error=raise_error)
    else:
        processed_attrs = filter_attributes(attrs=attrs,
                                            target='.tex',
                                            raise_error=raise_error)

    if processed_attrs:
        attr_elements = []
        for attr in processed_attrs:
                if isinstance(attr, tuple):
                    attr_elements.append('='.join(attr))
                elif isinstance(attr, str):
                    attr_elements.append(attr)
        return '[' + ", ".join(attr_elements) + "]"
    else:
        return ''

