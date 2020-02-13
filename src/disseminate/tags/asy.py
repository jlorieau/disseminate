"""
Tags to render asymptote (asy) figures and diagrams
"""
from .img import RenderedImg


class Asy(RenderedImg):
    """The asy tag for inserting asymptote images."""

    src_filepath = None
    active = True
    process_content = False
    input_format = '.asy'

    def __init__(self, name, content, attributes, context):
        super().__init__(name=name, content=content, attributes=attributes,
                         context=context)
