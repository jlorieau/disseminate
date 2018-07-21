"""
Renderer using the Jinja2 template rendering system.
"""
import os.path

import jinja2
import jinja2.meta

from .base_renderer import BaseRenderer
from .. import settings


class JinjaRenderer(BaseRenderer):
    """Manage templates and the rendering of files.

    Multiple template managers may be available for each project.
    """

    _jinja_templates = None
    _environment = None

    def __init__(self, context, template, targets, module_only=False):
        assert context.is_valid('src_filepath')

        # Prepare the cached templates dict
        self._jinja_templates = dict()

        # Load the template environment
        # Get the src_path
        src_filepath = context.get('src_filepath', None)
        src_path = (os.path.dirname(src_filepath) if src_filepath is not None
                    else None)

        # Create the filesystem loader to search paths for the template
        fsl = None
        if not self.module_only and src_path is not None:
            # Create a jinja2 FileSystemLoader that checks the directory of
            # src_path
            # and all parent directories.
            dir_tree = []

            parent_dir = src_path
            while parent_dir != "" and parent_dir != "/":
                dir_tree.append(parent_dir)
                parent_dir = os.path.dirname(parent_dir)

            fsl = jinja2.FileSystemLoader(dir_tree)

        dl = jinja2.PackageLoader('disseminate', 'templates')
        cl = jinja2.ChoiceLoader([fsl, dl]) if fsl is not None else dl

        # Create the environment
        kwargs = {'block_start_string': settings.template_block_start,
                  'block_end_string': settings.template_block_end,
                  'variable_start_string': settings.template_variable_start,
                  'variable_end_string': settings.template_variable_end,
                  'comment_start_string': settings.template_comment_start,
                  'comment_end_string': settings.template_comment_end,
                  'keep_trailing_newline': True,
                  }

        ae = jinja2.select_autoescape(['html', 'htm', 'xml'])
        env = jinja2.Environment(autoescape=ae, loader=cl, **kwargs)
        self._environment = env

        super(JinjaRenderer, self).__init__(context, template, targets,
                                            module_only)

        # Load and cache the template objects
        self.load_templates()

    @property
    def mtime(self):

        # Get all of the template objects
        templates = self._jinja_templates.values()

        # Get all of the filenames for the templates
        filenames = [t.filename for t in templates]

        # Get the maximum modification time
        mtimes = [os.path.getmtime(filename) for filename in filenames]
        return max(mtimes) if len(mtimes) > 0 else None

    @property
    def from_module(self):

        # Get a template for one of the targets
        templates = list(self._jinja_templates.values())
        if len(templates) == 0:
            return False

        template = templates[0]

        # For Jinja2 templates, the name for a template from the module is
        # relative to the module path directory. We will see if the filename
        # of the template matches its location in the module path
        abs_filepath = template.filename
        name = template.name

        if (name is not None and abs_filepath is not None and
           os.path.join(self.module_path, name) == abs_filepath):
            return True
        else:
            return False

    def template_filepaths(self, target=None):

        # Load all of the template objects
        if target is None or target not in self._jinja_templates:
            templates = self._jinja_templates.values()
        else:
            templates = [self._jinja_templates[target]]  # create list

        # Prepare a list of absolute paths (render paths) for the templates
        filenames = []

        # Get the loader from the environment
        env = self._environment
        loader = env.loader

        # Find the parent templates for each template
        for template in templates:
            # Get the template name
            name = template.name

            # Get the template's filename and add it to the filenames set
            filenames.append(template.filename)

            # Load the source code for the template using the loader
            source = loader.get_source(env, name)

            # Produce a Jinja2 AST from the source
            ast = env.parse(source)

            # Get a list of all parent template names from the AST
            parent_names = list(jinja2.meta.find_referenced_templates(ast))

            # Convert the parent names to template file paths (render paths)
            # This is done by loading the parent template objects.
            parent_templates = [env.get_template(parent_name)
                                for parent_name in parent_names]

            parent_filenames = [t.filename for t in parent_templates
                                if t.filename is not None]

            # Append new filenames
            filenames += [filename for filename in parent_filenames
                          if filename not in filenames]

        return filenames

    def render(self, context, target):
        self.load_templates()

        # get the template
        template = self.get_template(target)
        return template.render(**context)

    def is_available(self, target):
        """Is a template available for the given target?"""
        return self.get_template(target) is not None

    def load_templates(self):
        """Loads all the Jinja2 template objects needed to render the targets
        specified in the context."""
        # Get the targets specified in the context
        targets = self.targets

        # Replace intermediary targets. Ex: 'pdf' targets, which need to be
        # compiled, should be replaced with their source format (.tex)
        targets = [settings.compiled_exts[t]
                   if t in settings.compiled_exts else t
                   for t in targets]

        # find templates that haven't been loaded yet or need to be updated
        stale_targets = {k for k, v in self._jinja_templates.items()
                         if not v.is_up_to_date}  # set
        missing_targets = targets - self._jinja_templates.keys()
        reload_targets = missing_targets | stale_targets

        # Get the name of the template. This may or may not include the
        # actual name of the template file.
        template = self.template

        # Load missing templates
        for target in reload_targets:
            # Construct the template file name. The the template name may
            # include the the template file's base filename (without extension)
            # ex: template = 'books/tufte/template',
            #     template_file1 = 'books/tufte/template.html'
            template_file1 = "".join((template, target))

            # Or, it may just be a path. If it's a path, use 'template' as the
            # default base filename
            # ex: template = 'books/tufte'
            #     template_file2 = 'books/tufte/template.html'
            template_path = os.path.join(template, 'template')
            template_file2 = "".join((template_path, target))

            # Get the template environment
            env = self._environment

            # Load the template and cache it in the jinja_templates
            # May raise a jinja2.TemplateNotFound exception
            jinja_template = env.select_template([template_file1,
                                                  template_file2])

            self._jinja_templates[target] = jinja_template

    def get_template(self, target):
        """Retrieve the Jinja2 template object for the given target.

        Parameters
        ----------
        target : str
            The target (extension) for the template to retrieve. ex: '.html'

        Returns
        -------
        template : :obj:`jinja2.Template`
            The Jinja2 template object for the given target.

        Raises
        ------
        jinja2.TemplateNotFound
            Raised exception if the template file could not be found.
        """
        self.load_templates()
        # Return the cached version, if one is available
        return self._jinja_templates.get(target, None)
