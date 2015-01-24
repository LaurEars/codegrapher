import os
import ast
import copy
from pprint import pformat


class FileObject(object):
    """ Class for keeping track of files.

    Attributes:
        modules (dict): dict of current modules with `alias: module_name`, `key:value pairs`.
        aliases (dict): dict of current modules with `alias: original_name`, `key:value pairs`.
        node (:mod:`ast.AST`): AST node for entire file.
        name (string): File name.
        classes (list): :class:`ClassObject` items defined in the current file.
    """
    def __init__(self, file_name, modules=None, aliases=None):
        self.modules = copy.deepcopy(modules) if modules else {}
        self.aliases = copy.deepcopy(aliases) if aliases else {}
        self.name = file_name
        self.full_path = os.path.abspath(file_name)
        with open(self.full_path, 'r') as input_file:
            self.node = ast.parse(input_file.read(), filename=self.name)
        self.classes = []
        self.relative_namespace = self.name.split('.')[0].replace('/', '.')
        self.ignore = set()

    def visit(self):
        """ Visits all the nodes within the current file AST node.

        Updates `self.classes` for the current instance.
        """
        file_visitor = FileVisitor(aliases=self.aliases, modules=self.modules)
        file_visitor.visit(self.node)
        self.modules = file_visitor.modules
        self.aliases = file_visitor.aliases
        self.classes = file_visitor.classes
        self.namespace()

    def remove_builtins(self):
        """ Removes builtins from each class in a `FileObject` instance.
        """
        for class_object in self.classes:
            class_object.remove_builtins()

    def add_ignore_file(self):
        """ Use a file `.cg_ignore` to ignore a list of functions from the call graph
        """
        if os.path.isfile('.cg_ignore'):
            with open('.cg_ignore', 'r') as ignore_file:
                for line in ignore_file:
                    if line.strip() and line.strip()[0] != '#':
                        self.ignore.add(line.strip())

    def ignore_functions(self):
        for class_object in self.classes:
            class_object.ignore_functions(self.ignore)

    def namespace(self):
        """ Programmatically change the name of items in the call tree so they have relative path information
        :return:
        """

        for class_object in self.classes:
            class_object.namespace(self.relative_namespace)


class ClassObject(object):
    """ Class for keeping track of classes in code.

    Attributes:
        modules (dict): dict of current modules with `alias: module_name`, `key:value pairs`.
        aliases (dict): dict of current modules with `alias: original_name`, `key:value pairs`.
        node (:mod:`ast.AST`): AST node for entire class.
        name (string): Class name.
        functions (list): :class:`FunctionObject` items defined in the current class.
        call_tree (dict): dict with `key:value` pairs `(module, FunctionObject.name): (module, identifier)`.

    """
    def __init__(self, node=None, aliases=None, modules=None):
        self.modules = copy.deepcopy(modules) if modules else {}
        self.aliases = copy.deepcopy(aliases) if aliases else {}
        self.node = node
        self.name = node.name if node else ''
        self.functions = []
        self.call_tree = {}

    def visit(self):
        """ Visits all the nodes within the current class AST node.

        Updates `self.functions` and `self.call_tree` for the current instance.
        """
        function_visitor = FunctionVisitor(aliases=self.aliases, modules=self.modules)
        function_visitor.visit(self.node)
        self.functions = function_visitor.functions
        self.call_tree = dict(((self.name, k), v) for k, v in function_visitor.calls.iteritems())

    def remove_builtins(self):
        """ For many classes, we may not want to include builtin functions in the graph.
        Remove builtins from the call tree and from called functions list.
        """
        new_call_tree = {}
        for caller, call_list in self.call_tree.iteritems():
            new_call_list = []
            for call in call_list:
                if __builtins__.has_key(call[0]):
                    continue
                else:
                    new_call_list.append(call)
            new_call_tree[caller] = new_call_list

        self.call_tree = new_call_tree

    def ignore_functions(self, ignore_set):
        new_call_tree = {}
        for caller, call_list in self.call_tree.iteritems():
            new_call_list = []
            for call in call_list:
                if call[-1] not in ignore_set:
                    new_call_list.append(call)
            new_call_tree[caller] = new_call_list

        self.call_tree = new_call_tree

    def namespace(self, relative_namespace):
        new_call_tree = {}
        for caller in self.call_tree:
            new_call_tree[(relative_namespace, caller[0], caller[1])] = self.call_tree[caller]
        self.call_tree = new_call_tree

    def pprint(self):
        """ Pretty print formatter for class object.

        Returns:
            string
        """
        return pformat(self.call_tree)

    def __repr__(self):
        return "ClassObject {}".format(self.name)

    def __str__(self):
        functions = [fcn.name for fcn in self.functions]
        return "Class {}\nDefined functions: {}".format(self.name, functions)


class FunctionObject(object):
    """ Object that stores information within a single function definition

    attributes:
        modules: dict of current modules with `alias: module_name`, `key:value pairs`.
        aliases: dict of current modules with `alias: original_name`, `key:value pairs`.
        node (:mod:`ast.AST`): AST node for entire function.
        name (string): function name.
        calls (list): `(module, identifier)` tuples describing items called within current node,
                      with identifiers decoded form current alias, and modules expanded to their full import paths.
        decorator_list (list): list of decorators, by name as a string, applied to the current function definition.
        is_classmethod (bool): True if the current function is designated as a classmethod by a decorator.

    """
    def __init__(self, node=None, aliases=None, modules=None):
        self.modules = copy.deepcopy(modules) if modules else {}
        self.aliases = copy.deepcopy(aliases) if aliases else {}
        self.node = node
        self.name = node.name if node else ''
        self.calls = []
        self.decorator_list = []
        self.is_classmethod = False

    def visit(self):
        """ Visits all the nodes within the current function object's AST node.

        Updates `self.calls`, `self.modules`, and `self.aliases` for the current instance.
        """
        visitor = CallVisitor(aliases=self.aliases, modules=self.modules)
        visitor.visit(self.node)
        self.decorator_list = [decorator.id for decorator in self.node.decorator_list]
        if 'classmethod' in self.decorator_list:
            self.is_classmethod = True
        self.calls = visitor.calls
        self.modules.update(visitor.modules)
        self.aliases.update(visitor.aliases)


class CallInspector(ast.NodeVisitor):
    """ Within a call, a Name or Attribute will provide the function name currently in use.

    Identifies `Name` nodes, which are called as ``name(args)``, and `Attribute` nodes, which are called as
    ``object.attr(args)``
    """
    def __init__(self):
        self.module = ''
        self.identifier = ''

    def visit_Name(self, node):
        self.identifier = node.id

    def visit_Attribute(self, node):
        # todo: pull out item for the attr to determine whether node defines a classmethod
        # currently does not handle multiple chaining of attr items
        if hasattr(node.value, 'id'):
            self.module = node.value.id
        self.identifier = node.attr


class ImportVisitor(ast.NodeVisitor):
    """ For import related calls, store the source modules and aliases used.
    Designed to be inherited by other classes that need to know about imports in their current scope.

    Attributes:
        modules (dict): dict of current modules with `alias: module_name`, `key:value pairs`.
        aliases (dict): dict of current modules with `alias: original_name`, `key:value pairs`.
    """
    def __init__(self, aliases=None, modules=None):
        self.modules = copy.deepcopy(modules) if modules else {}
        self.aliases = copy.deepcopy(aliases) if aliases else {}

    def continue_parsing(self, node):
        super(ImportVisitor, self).generic_visit(node)

    def visit_Import(self, node):
        for item in node.names:
            asname = item.asname if item.asname else item.name
            self.aliases[asname] = item.name
            self.modules[asname] = None

    def visit_ImportFrom(self, node):
        module = node.module
        for item in node.names:
            asname = item.asname if item.asname else item.name
            self.aliases[asname] = item.name
            self.modules[asname] = module

        
class CallVisitor(ImportVisitor):
    """ Finds all calls present in the current scope and inspect them.

    Attributes:
        call_names (set): set of :class:`CallInspector.identifier` items within current AST node.
        calls (list): `(module, identifier)` items called within current AST node,
                      with identifiers decoded form current alias, and modules expanded to their full import paths.
    """
    def __init__(self, **kwargs):
        super(CallVisitor, self).__init__(**kwargs)
        self.call_names = set()
        self.calls = []

    def continue_parsing(self, node):
        super(CallVisitor, self).generic_visit(node)

    def visit_Call(self, node):
        call_visitor = CallInspector()
        call_visitor.visit(node.func)

        # handles calls within function calls
        for arg in node.args:
            self.continue_parsing(arg)
            if isinstance(arg, ast.Call):
                arg_visitor = CallVisitor(aliases=self.aliases, modules=self.modules)
                arg_visitor.visit(arg)
                self.call_names.update(arg_visitor.call_names)
                self.calls.extend(arg_visitor.calls)

        self.call_names.add(call_visitor.identifier)

        # if names are aliased, pull out aliased name
        if call_visitor.identifier in self.aliases:
            identifier = self.aliases[call_visitor.identifier]
        else:
            identifier = call_visitor.identifier

        if call_visitor.module in self.modules:
            # module is imported and called by attr
            if self.modules[call_visitor.module]:
                module = '.'.join([self.modules[call_visitor.module], self.aliases[call_visitor.module]])
            else:
                module = self.aliases[call_visitor.module]
        elif call_visitor.identifier in self.modules:
            # module is imported, but not called by attr
            module = self.modules[call_visitor.identifier]
        else:
            # no module specified
            module = None

        if module:
            call = (module, identifier)
        else:
            call = (identifier,)

        self.calls.append(call)


class FunctionVisitor(ImportVisitor):
    """ Function definitions are where the function is defined, and the call is where the ast for that function exists.

    This only looks for items that are called within the scope of a function, and associates those items
    with the function.

    Attributes:
        defined_functions (set): names of functions found by function visitor instance.
        functions (list): :class:`FunctionObject` instances found by function visitor instance.
        calls (dict): mapping from function names defined to calls within that function definition.
    """
    def __init__(self, **kwargs):
        super(FunctionVisitor, self).__init__(**kwargs)
        self.defined_functions = set()
        self.functions = []
        self.calls = {}

    def continue_parsing(self, node):
        super(FunctionVisitor, self).generic_visit(node)

    def visit_FunctionDef(self, node):
        self.defined_functions.add(node.name)
        function_def = FunctionObject(node=node, aliases=self.aliases, modules=self.modules)
        function_def.visit()
        self.calls[function_def.name] = function_def.calls
        self.functions.append(function_def)


class FileVisitor(ImportVisitor):
    """ First visitor that should be called on the file level.

    Attributes:
        classes (list): list of :class:`ClassObject` instances defined in the current file.
    """
    def __init__(self, **kwargs):
        super(FileVisitor, self).__init__(**kwargs)
        self.classes = []

    def continue_parsing(self, node):
        super(FileVisitor, self).generic_visit(node)

    def visit_Module(self, node):
        self.continue_parsing(node)

    def visit_ClassDef(self, node):
        # once a class is found, create a class object for it and traverse the ast with its visitor
        new_class = ClassObject(node=node, aliases=self.aliases, modules=self.modules)
        new_class.visit()
        self.classes.append(new_class)

    def remove_builtins(self):
        """ Removes builtins from each class in a `FileVisitor` instance.
        """
        for class_object in self.classes:
            class_object.remove_builtins()
