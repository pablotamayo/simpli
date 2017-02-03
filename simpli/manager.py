import sys  # Don't remove this import - sys IS used!
from os import listdir
from os.path import isdir, join
import inspect  # Don't remove this import - inspect IS used!
from json import loads


from IPython.display import clear_output

from . import HOME_DIR, SIMPLI_JSON_DIR
from .support import get_name, merge_dicts, title_str, cast_str_to_int_float_bool_or_str, reset_encoding

import sys
sys.path.insert(0, '/home/cyborg/simpli')
import simpli

class Manager:
    """
    Notebook Manager.
    """

    def __init__(self):
        """
        Initialize a Notebook Manager.
        """

        self._namespace = {}

        # Tasks (and their specifications) keyed by their unique label
        self._tasks = {}

    def get_namespace(self):
        """
        Get namespace.
        :return: dict;
        """

        # print('(Getting namespace ...)')
        return self._namespace

    def set_namespace(self, namespace):
        """
        Set namespace
        :param namespace: dict;
        :return: None
        """

        # print('(Setting namespace ...)')
        self._namespace = namespace

    namespace = property(get_namespace, set_namespace)

    def update_namespace(self, namespace):
        """
        Update namespace.
        :param namespace: dict;
        :return: None
        """

        # print('Updating namespace with {} ...'.format(namespace))
        self.namespace = merge_dicts(self.namespace, namespace)

    def _get_tasks(self):
        """
        Get tasks.
        :return: list; list of dict
        """

        # print('(Getting tasks ...)')
        return self._tasks

    def _set_tasks(self, tasks):
        """
        Set tasks.
        :param tasks: list; list of dict
        :return:  None
        """

        # print('(Setting tasks ...)')
        self._tasks = tasks

    tasks = property(_get_tasks, _set_tasks)

    def get_task(self, task_label):
        """
        Get a task, whose label is task_label.
        :param task_label: str;
        :return: dict;
        """
        # print('Getting task {} ...'.format(task_label))
        return {task_label: self.tasks[task_label]}

    def set_task(self, task_label, task):
        """
        Set or update a task, whose label is task_label, to be task.
        :param task_label: str;
        :param task: dict;
        :return: None
        """

        # print('Setting/updating task {} to be {} ...'.format(task_label, task))
        self.tasks.update({task_label: task})

    def load_tasks_from_json_dir(self, json_directory_path=SIMPLI_JSON_DIR):
        """
        Load tasks from task-specifying JSONs in json_directory_path.
        :param json_directory_path: str; directory containing task-specifying JSONs
        :return: None
        """

        # print('Loading task-specifying JSONs in directory {} ...'.format(json_directory_path))
        for f in listdir(json_directory_path):
            fp_json = join(json_directory_path, f)
            try:
                self.tasks.update(self.load_tasks_from_json(fp_json))
            except:
                pass

    def load_tasks_from_json(self, json_filepath):
        """
        Load a task from a task-specifying JSON, json_filepath
        :param json_filepath: str; filepath to a task-specifying JSON
        :return: dict;
        """

        # print('Loading a task-specifying JSON {} ...'.format(json_filepath))

        with open(json_filepath) as f:
            tasks_json = loads(reset_encoding(f.read()))

        tasks = {}

        # Load library path, which is common for all tasks
        library_path = tasks_json['library_path']
        if not isdir(library_path):  # Use absolute path
            library_path = join(HOME_DIR, library_path)
            # print('\tAssumed that library_path ({}) is relative to the user-home directory.'.format(library_path))

        # Load each task
        for t in tasks_json['tasks']:

            function_path = t['function_path']
            if '.' in function_path:
                split = function_path.split('.')
                library_name = '.'.join(split[:-1])
                function_name = split[-1]
            else:
                raise ValueError('function_path must be like: \'path.to.file.function_name\'.')

            # Task label is this task's UID; so no duplicates are allowed
            label = t.get('label', '{} (no task label)'.format(function_name))
            if label in tasks:  # Label is duplicated
                # print('Task label \'{}\' is duplicated; automatically making a new task label ...'.format(label))

                i = 2
                new_label = '{} (v{})'.format(label, i)
                while new_label in tasks:
                    i += 1
                    new_label = '{} (v{})'.format(label, i)
                label = new_label

            tasks[label] = {
                'library_path': library_path,
                'library_name': library_name,
                'function_name': function_name,
                'description': t.get('description', 'No description.'),
                'required_args': self._process_args(t.get('required_args', [])),
                'default_args': self._process_args(t.get('default_args', [])),
                'optional_args': self._process_args(t.get('optional_args', [])),
                'returns': self._process_returns(t.get('returns', []))}

        return tasks

    def load_task_from_notebook_cell(self, text):
        """
        Load task from a notebook cell.
        :param cell_text: str;
        :return: dict;
        """
        # print('Loading a task from a notebook cell ...')

        print('*********\n{}\n*********'.format(text))

        lines = text.split('\n')
        print('\nlines: {}'.format(lines))

        # Comment
        comment = [l for l in lines if l.startswith('#')]
        print('\ncomment: {}'.format(comment))

        label = comment[0].split('#')[1].strip()
        print('\nlabel: {}'.format(label))

        # Code
        code = ''.join([l for l in lines if not l.startswith('#')]).replace(' ', '')
        print('\ncode: {}'.format(code))

        i = code.find('(')
        before, args = code[:i], code[i + 1:-1]
        print('\nbefore: {}'.format(before))

        i = before.find('=')
        if i == -1:  # No returns
            i = 0
        returns = before[:i]
        print('\nreturns: {}'.format(returns))

        if i != 0:
            i += 1
        function_name = before[i:]
        s = None
        print('s = inspect.signature({})'.format(function_name))
        exec('s = inspect.signature({})'.format(function_name))

        library_name = None
        exec('library_name = {}.__module__'.format(function_name))
        print('library_name: {}'.format(library_name))

        library_path = None
        exec('library_path = {}.__globals__.get(\'__file__\')'.format(function_name))
        library_path = library_path.split(library_name.replace('.', '/'))[0]
        print('library_path: {}'.format(library_path))

        function_name = function_name.split('.')[-1]
        print('\nfunction_name: {}'.format(function_name))

        args = args[:-1].split(',')
        print('\nargs: {}'.format(args))

        required_args = [{'label': n.upper(),
                          'description': 'No description.',
                          'name': n,
                          'value': v} for n, v in zip(list(s.parameters), [x for x in args if '=' not in x])]
        print('\nrequired_args: {}'.format(required_args))

        optional_args = [{'label': n.upper(),
                          'description': 'No description',
                          'name': n,
                          'value': v} for n, v in [x.split('=') for x in args if '=' in x]]
        print('\noptional_args: {}'.format(optional_args))

        returns = [{'label': l.upper(),
                    'description': 'No description.'} for l in returns]

        self.tasks.update({label: {
            'description': 'No description.',
            'library_path': library_path,
            'library_name': library_name,
            'function_name': function_name,
            'required_args': required_args,
            'default_args': [],
            'optional_args': optional_args,
            'returns': returns
        }
        }
        )

        return self.get_task(label)

    def _process_args(self, dicts):
        """
        Process args.
        :param dicts: list; list of dict
        :return: dict;
        """

        processed_dicts = []

        for d in dicts:
            processed_dicts.append({'name': d.get('name'),
                                    'value': d.get('value', ''),
                                    'label': d.get('label', title_str(d['name'])),
                                    'description': d.get('description', 'No description')})

        return processed_dicts

    def _process_returns(self, dicts):
        """
        Process returns.
        :param dicts: list; list of dict
        :return: dict;
        """

        processed_dicts = []

        for d in dicts:
            processed_dicts.append({'label': d.get('label'),
                                    'description': d.get('description', 'No description')})

        return processed_dicts

    # Execute a task
    def execute_task(self, task):
        """
        Execute task.
        :param task: dict;
        :return: None
        """

        # Clear any existing output
        clear_output()

        if len(task) == 1:
            label, task = task.popitem()

        # Process and merge args
        required_args = {a['name']: a['value'] for a in task['required_args']}
        default_args = {a['name']: a['value'] for a in task['default_args']}
        optional_args = {a['name']: a['value'] for a in task['optional_args']}
        args = self._merge_process_args(required_args, default_args, optional_args)

        # Get returns
        returns = [a['value'] for a in task['returns']]
        if None in returns or '' in returns:
            raise ValueError('Missing returns.')
        else:
            print('returns: {}'.format(returns))

        # Call function
        returned = self._path_import_execute(task['library_path'], task['library_name'], task['function_name'], args)

        # Handle returns
        if len(returns) == 1:
            self.namespace[returns[0]] = returned
        elif len(returns) > 1:
            for n, v in zip(returns, returned):
                self.namespace[n] = v
        else:
            # TODO: think about how to better handle no-returns
            pass
            # print('self.namespace (after execution): {}'.format(self.namespace))

    def _path_import_execute(self, library_path, library_name, function_name, args):
        """
        Prepend path, import library, and execute task.

        :param library_path: str;
        :param library_name: str;
        :param function_name: str;

        :param args: dict;

        :return: list; raw output of the function
        """

        print('Updating path, importing function, and executing task ...')

        # Prepend library path
        code = 'sys.path.insert(0, \'{}\')'.format(library_path)
        print('\t{}'.format(code))
        exec(code)

        # Import function
        code = 'from {} import {} as function'.format(library_name, function_name)
        print('\t{}'.format(code))
        exec(code)

        # Execute
        print('\tExecuting {} with:'.format(locals()['function']))
        for n, v in sorted(args.items()):
            print('\t\t{} = {} ({})'.format(n, get_name(v, self.namespace), type(v)))

        return locals()['function'](**args)

    def _merge_process_args(self, required_args, default_args, optional_args):
        """
        Convert input str arguments to corresponding values:
            If the str is the name of a existing variable in the Notebook namespace, use its corresponding value;
            If the str contains ',', convert it into a list of str;
            Try to cast str in the following order and use the 1st match: int, float, bool, and str;
        :param required_args: dict;
        :param default_args: dict;
        :param optional_args: dict;
        :return: dict; merged and processed args
        """

        # print('\tMerging and processing arguments ...')

        if None in required_args or '' in required_args:
            raise ValueError('Missing required_args.')

        repeating_args = set(required_args.keys() & default_args.keys() & optional_args.keys())
        if any(repeating_args):
            raise ValueError('Argument \'{}\' is repeated.'.format(required_args))

        merged_args = merge_dicts(required_args, default_args, optional_args)

        processed_args = {}
        for n, v in merged_args.items():

            if v in self.namespace:  # Process as already defined variable from the Notebook environment
                processed_v = self.namespace[v]

            else:  # Process as float, int, bool, or str
                # First assume a list of str to be passed
                processed_v = [cast_str_to_int_float_bool_or_str(s) for s in v.split(',') if s]

                # If there is only 1 item in the assumed list, use it directly
                if len(processed_v) == 1:
                    processed_v = processed_v[0]

            processed_args[n] = processed_v
            # print('\t\t{}: {} > {} ({})'.format(n, v, get_name(processed_v, self.namespace), type(processed_v)))

        return processed_args
