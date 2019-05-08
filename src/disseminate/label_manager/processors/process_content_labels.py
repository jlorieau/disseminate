"""
A label processor to process content labels
"""
from .process_labels import ProcessLabels
from ..types import ContentLabel, DocumentLabel


class ProcessContentLabels(ProcessLabels):
    """A label processor for :obj:`content labels
    <disseminate.label_manager.types.ContentLabel>`.

    This function sets the chapter_label, section_label, etc. for ContentLabels
    to identify which chapter/section/subsection/etc. a particular label belongs
    to.
    """

    order = 1000

    def __call__(self, registered_labels, *args, **kwargs):

        # Keep track of the current heading registered_labels
        part_label = None
        chapter_label = None
        section_label = None
        subsection_label = None
        subsubsection_label = None

        # Process each Contentlabel.
        content_labels = [label for label in registered_labels
                          if isinstance(label, ContentLabel)]

        # Keep track of the current doc_id
        doc_id = None

        for label in content_labels:
            # Switch the local count whenever a new document is encountered.
            # However, the local_counter is not reset between documents
            if not isinstance(label, DocumentLabel) and doc_id != label.doc_id:
                local_counter = dict()
                doc_id = label.doc_id

            if label.kind and label.kind[-1] == 'part':
                # If it's a new chapter (i.e. a chapter or document title)
                # Get its label and reset the counters for the heading
                # registered_labels below
                part_label = label
                chapter_label = None
                section_label = None
                subsection_label = None
                subsubsection_label = None

            elif label.kind and label.kind[-1] == 'chapter':
                # If it's a new chapter (i.e. a chapter or document title)
                # Get its label and reset the counters for the heading
                # registered_labels below
                chapter_label = label
                section_label = None
                subsection_label = None
                subsubsection_label = None

            elif label.kind and label.kind[-1] == 'section':
                section_label = label
                subsection_label = None
                subsubsection_label = None

            elif label.kind and label.kind[-1] == 'subsection':
                subsection_label = label
                subsubsection_label = None

            elif label.kind and label.kind[-1] == 'subsubsection':
                subsubsection_label = label

            # Set the heading label for all registered_labels
            label.part_label = part_label
            label.chapter_label = chapter_label
            label.section_label = section_label
            label.subsection_label = subsection_label
            label.subsubsection_label = subsubsection_label
