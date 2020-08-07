
"""
Tags to render asymptote (asy) figures and diagrams
"""
from .img import Img


class Asy(Img):
    """The asy tag for inserting asymptote images."""

    active = True
    process_content = False
    in_ext = '.save'

    def __init__(self, name, content, attributes, context):
        super().__init__(name=name, content=content, attributes=attributes,
                         context=context)
