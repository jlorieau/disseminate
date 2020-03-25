from .composite_builder import CompositeBuilder
from ..copy import Copy


class SequentialBuilder(CompositeBuilder):
    """A composite builder that runs subbuilders in sequence (i.e. wait for
    one to finish before starting the next)

    Attributes
    ----------
    chain_on_create : bool
        If True (default), chain the infilepaths and outfilepath of the
        subbuilders to follow each other.
    copy : bool
        If True (default), the last subbuilders will be a Copy build to copy
        the result to the final outfilepath
    """
    parallel = False

    chain_on_creation = True
    copy = True

    def __init__(self, env, **kwargs):
        super().__init__(env, **kwargs)

        # Make the last subbuilder a copy builder to copy the result of the
        # sub-builders to the final outfilepath.
        # This only applies if other subbuilders are present
        if self.copy and self.subbuilders:
            self.subbuilders.append(Copy(env))

        # Order the subbuilders, if subbuilders are present
        if self.chain_on_creation and self.subbuilders:
            self.chain_subbuilders()

    def chain_subbuilders(self):
        """Chain the infilepaths and outfilepath of the subbuilders to follow
        each other"""
        # Set the infilepaths and outfilepaths
        current_infilepaths = self.infilepaths
        for subbuilder in self.subbuilders:
            # For the subbuilders to work together, reset their infilepaths
            # and outfilepath
            if current_infilepaths:
                subbuilder.infilepaths = current_infilepaths
            subbuilder.outfilepath = None

            # Convert the output of subbuilder into an infilepath for the
            # next subbuilder
            outfilepath = subbuilder.outfilepath
            if outfilepath:
                infilepath = outfilepath
                current_infilepaths = [infilepath]

        # Set the copy builder to point to the final outfilepath
        self.subbuilders[-1].outfilepath = self.outfilepath

        # Chain any sequential builder subbuilders
        for subbuilder in self.subbuilders:
            if not hasattr(subbuilder, 'chain_subbuilders'):
                continue
            subbuilder.chain_subbuilders()

    @property
    def status(self):
        if not self.build_needed():
            return 'done'

        # The composite builder's status is basically the same as the next
        # non-done subbuilder. The reason it is implemented this way is to
        # avoid checking the status of intermediary builders whose input files,
        # which may be cached or temporary, may not yet exist.
        number_subbuilders_done = 0
        for subbuilder in self.subbuilders:
            # Bug alert: The subbuilder's status should be retrieved and
            # returned once. Polling the subbuilder.status multiple times may
            # return different answers if the subbuilder changes status when
            # polled at different points.
            status = subbuilder.status
            if status == 'done':
                number_subbuilders_done += 1
            else:
                return status

        if number_subbuilders_done == len(self.subbuilders):
            self.build_needed(reset=True)
            return 'done'
        else:
            return 'building'
