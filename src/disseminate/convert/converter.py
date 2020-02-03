"""The base Converter class."""
import subprocess
import logging
import os
from pathlib import Path
from tempfile import mkdtemp
from distutils.spawn import find_executable

from .arguments import SourcePathArgument, TargetPathArgument, Argument
from ..paths import SourcePath, TargetPath
from .. import settings


def convert(src_filepath, target_basefilepath, targets, raise_error=True,
            cache=settings.convert_cache,
            create_dirs=settings.create_dirs,
            **kwargs):
    """Convert a source file to a target file.

    Parameters
    ----------
    src_filepath : :obj:`SourcePath <.paths.SourcePath>`
        The path and filename for the file to convert.
        ex: SourcePath('src/media/img1.svg')
    target_basefilepath : :obj:`TargetPath <.paths.TargetPath>`
        The path and filename (without extension) that the target file should
        adopt. This is a render path, and the final target will be determined
        by this function, if a conversion is possible.
        ex: TargetPath('tex/media/img1')
    targets : List[str]
        A list of possible extensions for formats that the file can be
        converted to, depending on which programs are installed. This list
        is in decreasing order of preference.
        ex: ['.pdf', '.png', '.jpg]
    raise_error : Optional[bool]
        If True, a ConvertError will be raised if a suitable converter was not
        found or the conversion was not possible.
    cache : Optional[bool]
        If True, return an existing target file, rather than convert it, if
        the target file is newer than the source file (src_filepath)
    create_dirs : Optional[bool]
        If True, create any needed directories in the target_basefilepath.

    Raises
    ------
    ConvertError
        A ConvertError is raise if raise_error is True and a suitable converter
        was not found or the conversion was not possible.

    Returns
    -------
    target_filepath : Union[:obj:`TargetPath <.paths.TargetPath>`, False]
        The final path of the converted target file that was  created.
        False is returned if the conversion was not possible.
        ex: 'tex/media/img.pdf'
    """
    assert isinstance(src_filepath, SourcePath)
    assert isinstance(target_basefilepath, TargetPath)

    # The src_filepath should exist
    if not src_filepath.is_file():
        if raise_error:
            msg = "Could not find the file to convert '{}'"
            raise ConverterError(msg.format(src_filepath))
        return False
    # The src file needs a valid extension
    if src_filepath.suffix == '':
        if raise_error:
            msg = "The file '{}' requires a valid extension"
            raise ConverterError(msg.format(src_filepath))
        return False

    # The target_basefilepath directory should exist
    if not target_basefilepath.parent.is_dir():
        if create_dirs:
            target_basefilepath.parent.mkdir(parents=True)
        else:
            msg = ("The file '{}' cannot be converted because the target "
                   "directory '{}' does not exist.")
            raise ConverterError(msg.format(str(src_filepath),
                                            str(target_basefilepath.parent)))

    # Get a suitable converter subclass
    try:
        converter = Converter.get_converter(src_filepath, target_basefilepath,
                                            targets, **kwargs)
    except ConverterError as e:
        if __debug__:
            logging.debug("Converter subclasses:", Converter._converters)
        if raise_error:
            raise e
        return False

    # Get the target_filepath the convert would create
    target_filepath = converter.target_filepath()

    # See if a target already exists and return an existing version if available
    # and up to date
    if (cache and
       target_filepath.is_file() and
       target_filepath.stat().st_mtime >= src_filepath.stat().st_mtime):
        return target_filepath

    # A cached file wasn't used or found. Try to convert the file with the
    # converter
    try:
        successful = converter.convert()
    except ConverterError as e:
        successful = False
        if raise_error:
            raise e

    if successful and target_filepath.is_file():
        return target_filepath
    else:
        return False


class ConverterError(Exception):
    """An error was encountered in converting a file.
    """
    #: (str) The shell command that generated the ConverterError
    cmd = None

    #: (int) The return code for the shell command.
    returncode = None

    #: The stdout for the shell command.
    shell_out = None

    #: The stderr for the shell command.
    shell_err = None


def _all_subclasses(cls):
    """Retrieve all subclasses, sub-subclasses and so on for a class"""
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in _all_subclasses(s)]


class Converter(object):
    """The base class for converting between file types.

    Parameters
    ----------
    src_filepath : :obj:`SourcePath <.paths.SourcePath>`
        The path and filename for the file to convert.
        ex: 'src/media/img1.svg'
    target_basefilepath : :obj:`TargetPath <.paths.TargetPath>`
        The path and filename (without extension) that the target file should
        adopt.
        ex: 'tex/media/img'
    target : str
        The desired extension format to convert to (ex: '.svg')
    kwargs : dict
        The options to use with the converter.

    Attributes
    ----------
    from_formats : List[str]
        A list of text format extensions that can be handled by this converter.
        ex: ['.png', '.svg']
    to_formats : List[str]
        A list of text format extensions that can be generated by this
        converter.
        ex: ['.png', '.pdf']
    order : int
        The order for the converter. If multiple converters are available
        for a given combination of from_format and to_format, the one with
        the lower order will be used first.
    required_execs : List[str]
        A list of required executables for a converter.
    optional_execs : List[str]
        A list of optional executables for a converter
    """

    from_formats = None
    to_formats = None
    order = 1000
    required_execs = None
    optional_execs = None

    src_filepath = None
    target_basefilepath = None
    target = None

    _converters = None
    _temp_dir = None

    def __init__(self, src_filepath, target_basefilepath, target, **kwargs):
        self.src_filepath = SourcePathArgument('src_filepath', src_filepath,
                                               required=True)
        self.target_basefilepath = TargetPathArgument('target_basefilepath',
                                                      target_basefilepath,
                                                      required=True)
        assert target in self.to_formats
        self.target = target

    @classmethod
    def is_available(cls):
        """Return True if this converter can be used (i.e. the required
        executables are all available)."""
        execs_paths = [cls.find_executable(e) for e in cls.required_execs]

        return None not in execs_paths

    @classmethod
    def find_executable(cls, executable_string):
        return find_executable(executable_string)

    @classmethod
    def run(cls, args, env=None, error_msg=None, raise_error=True):
        """Run a command from the given arguments and either log a warning or
        raise an error with the given message, if it fails.

        Parameters
        ----------
        args : List[str]
            The arguments for the command. (Compatible with Popen)
        env : Optional[dict]
            If specified, the env dict will be used in running the command.
            Values will be appended to the current environment.
        error_msg : Optional[str]
            The warning or error message if the command fails. A command fails
            if the returncode is not 0.
            If no error message was specified, a default message will be
            created.
        raise_error : Optional[bool]
            If True, a ConverterError will be raised if the command failed.
            If False, a warning will be logged if the command failed.

        Raises
        ------
        ConverterError
            Raised if the command failed and raise_error is True.

        Returns
        -------
        returncode, output, error : int, str, str
            The returncode, the command output and the command error from
            running the command.
        """
        if __debug__:
            msg = "Running conversion: {}".format(" ".join(map(str, args)))
            logging.debug(msg)

        # Setup the environment
        if env is not None:
            current_env = os.environ.copy()
            for k, v in env.items():
                if k in current_env:
                    current_env[k] += ":" + v
                else:
                    current_env[k] = v
            env = current_env

        # Run the subprocess
        p = subprocess.Popen(args, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, bufsize=4096, )

        # Check that it was succesfully converted
        out, err = p.communicate()
        out = out.decode('latin1')
        err = err.decode('latin1')
        returncode = p.returncode

        if returncode != 0:
            if error_msg is None:
                error_msg = ("The conversion command '{}' was "
                             "unsuccessful. Exited with code "
                             "{}.".format(' '.join(args), returncode))
            if raise_error:
                e = ConverterError(error_msg)
                e.cmd = " ".join(args)
                e.returncode = returncode
                e.shell_out = out
                e.shell_err = err
                raise e
            else:
                logging.warning(error_msg)
                logging.debug(err)

        return returncode, out, err

    @classmethod
    def get_converter(cls, src_filepath, target_basefilepath, targets,
                      **kwargs):
        """Return a Converter subclass instance that can handle the conversion.

        .. note:: converters returned with this method are valid and their
                  required executables are available.

        Parameters
        ----------
        src_filepath : :obj:`SourcePath <.paths.SourcePath>`
            The path with filename for the file to convert.
        target_basefilepath : :obj:`TargetPath <.paths.TargetPath>`
            The path and filename (without extension) that the target file
            should adopt. This is a render path, and the final target will be
            determined by this function, if a conversion is possible.
            ex: 'tex/media/img'
        targets : List[str]
            A list of possible extensions for formats that the file can be
            converted to, depending on which programs are installed. This list
            is in decreasing order of preference.
            ex: ['.pdf', '.png', '.jpg]

        Returns
        -------
        converter : instance of a Converter subclass (:obj:`Converter`)
            A valid converter in which the available executables are available.
        """
        assert isinstance(src_filepath, SourcePath)
        assert isinstance(target_basefilepath, TargetPath)

        # Setup the converter subclasses
        if cls._converters is None:
            cls._converters = sorted(_all_subclasses(cls),
                                     key=lambda s: s.order)

        # Get the extension of the src_filepath and target_filepath
        from_format = src_filepath.suffix

        # Get a list of converters that could be used for this conversion
        valid_converters = []
        for target in targets:
            valid_converters += [c for c in cls._converters
                                 if from_format in c.from_formats
                                 and target in c.to_formats]

        # If valid_converters is empty, then no valid format was found. Raise
        # a ConverterError
        if len(valid_converters) == 0:
            msg = ("Could not find a converter for the file '{}' to any of the "
                   "following possible formats: {}")
            raise ConverterError(msg.format(str(src_filepath),
                                            ", ".join(targets)))

        # Check to make sure that the required executables are available
        available_converters = [c for c in valid_converters
                                if c.is_available()]

        if len(available_converters) == 0:
            required_execs = [", ".join(c.required_execs) for c in
                              valid_converters]
            exe_str = ", ".join(required_execs)

            msg = ("One of the following required program(s) '{}' needs to be "
                   "installed to convert the '{}' file.")
            raise ConverterError(msg.format(exe_str, src_filepath))

        # For the available converters find the converter that can handle the
        # preferred target extension
        best_target = None
        best_converter = None
        for target in targets:
            converters = [c for c in available_converters
                          if target in c.to_formats]
            if len(converters) > 0:
                best_target = target
                best_converter = converters[0]
                break

        assert best_target is not None
        assert best_converter is not None

        # instantiate the Converter subclass
        converter = best_converter(src_filepath=src_filepath,
                                   target_basefilepath=target_basefilepath,
                                   target=best_target, **kwargs)

        return converter

    def temp_filepath(self):
        """Return the filepath that can be used as a temporary file for the
        converted file."""
        target_filepath = self.target_filepath()

        # Load the temp directory
        if getattr(Converter, '_temp_dir', None) is None:
            Converter._temp_dir = Path(mkdtemp())

        # Generate the filename
        if isinstance(target_filepath, Argument):
            filename = target_filepath.value_string.name
        else:
            filename = target_filepath.name

        return self._temp_dir / filename

    def target_filepath(self):
        """Return the full target_path (:obj:`TargetPath <.paths.TargetPath>`)
        with modifiers and an extension."""
        # target_basefilepath is the TargetPath (path, document target and
        # filename) for the file to create
        # ex: tex/Chapter1_GasEquationsState/figures/Fig1_Boyle
        target_basefilepath = self.target_basefilepath.value

        # This target is the format to which the file should be converted.
        # This is separate from the document target
        # ex: .png
        target = ('.' + self.target if not self.target.startswith('.') else
                  self.target)

        # Create a new target path for the target filename to create, including
        # the document target, the target filename and path, and the target
        # format of the new file.
        # ex: tex/Chapter1_GasEquationsState/figures/Fig1_Boyle.png
        return TargetPath(target_root=target_basefilepath.target_root,
                          target=target_basefilepath.target,
                          subpath=str(target_basefilepath.subpath) + target)

    def convert(self):
        """Convert a file and return its new path.

        Raises
        ------
        ConvertError
            If a general error was encountered in the conversion, such as
            a unsuccessful program execution.
        ArgumentError
            One of the arguments was invalid.

        Returns
        -------
        successful : bool
            True if the conversion was successful, False if it wasn't.
        """
        return False

