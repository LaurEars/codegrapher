import ast
import copy
from pprint import pformat


class ClassObject(object):
    """ Class for keeping track of classes in code

    attributes:
        modules: dict of current modules with alias: module_name, key:value pairs
        aliases: dict of current modules with alias: original_name, key:value pairs
        node (ast.AST): node for entire class
        name (string): class name
        functions (list): FunctionObject items defined in the current class
        call_tree (dict): (module, FunctionObject.name): (module, identifier)

    """
    def __init__(self, node=None, aliases=None, modules=None):
        self.modules = copy.deepcopy(modules) if modules else {}
        self.aliases = copy.deepcopy(aliases) if aliases else {}
        self.node = node
        self.name = node.name if node else ''
        self.functions = []
        self.call_tree = {}

    def visit(self):
        function_visitor = FunctionVisitor(aliases=self.aliases, modules=self.modules)
        function_visitor.visit(self.node)
        self.functions = function_visitor.functions
        self.call_tree = dict(((self.name, k), v) for k, v in function_visitor.calls.iteritems())

    def remove_builtins(self):
        """ For many classes, we may not want to include builtin functions in the graph.
        Remove builtins from the call tree and from called functions list
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

    def pprint(self):
        """ Pretty print formatter for class object
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
        modules: dict of current modules with alias: module_name, key:value pairs
        aliases: dict of current modules with alias: original_name, key:value pairs
        node (ast.AST): node for entire class
        name (string): function name
        calls (list): (module, identifier) items called within current node
                      with with identifiers decoded form current alias, and modules expanded to their full import paths

    """
    def __init__(self, node=None, aliases=None, modules=None):
        self.modules = copy.deepcopy(modules) if modules else {}
        self.aliases = copy.deepcopy(aliases) if aliases else {}
        self.node = node
        self.name = node.name if node else ''
        self.calls = []

    def visit(self):
        visitor = CallVisitor(aliases=self.aliases, modules=self.modules)
        visitor.visit(self.node)
        self.calls = visitor.calls
        self.modules.update(visitor.modules)
        self.aliases.update(visitor.aliases)


class CallInspector(ast.NodeVisitor):
    """ Within a call, a Name or Attribute will provide the function name currently in use

    Name vs. attribute:
        name(args)
        object.attr(args)
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
    Designed to be inherited by other classes that need to know about imports in their current scope

    attributes:
        modules: dict of current modules with alias: module_name, key:value pairs
        aliases: dict of current modules with alias: original_name, key:value pairs
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
    """ Find all calls present in the current scope and inspect them

    attributes:
        call_names (set): set of CallInspector.identifier items within current node
        calls (list): (module, identifier) items called within current node
                      with with identifiers decoded form current alias, and modules expanded to their full import paths
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
    """ Function definitions are where the function is defined, and the call is where the ast for that function exists

    This only looks for items that are called within the scope of a function, and associates those items
    with the function

    attributes:
        defined_functions (set): names of functions found by function visitor instance
        functions (list): FunctionObject instances found by function visitor instance
        calls (dict): mapping from function names defined to calls within that function definition
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

    attributes:
        classes: list of ClassObject instances defined in the current file
    """
    def __init__(self):
        super(FileVisitor, self).__init__()
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
        for class_object in self.classes:
            class_object.remove_builtins()
