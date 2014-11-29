import ast
import copy


class ClassObject(object):
    def __init__(self, name, aliases=None, modules=None):
        self.modules = copy.deepcopy(modules) if modules else {}
        self.aliases = copy.deepcopy(aliases) if aliases else {}
        self.name = name
        self.node = None
        self.functions = []
        self.called_functions = []
        self.call_tree = {}

    def visit(self):
        function_visitor = FunctionVisitor(aliases=self.aliases, modules=self.modules)
        function_visitor.visit(self.node)
        self.functions = function_visitor.functions
        self.called_functions = function_visitor.call_names
        self.call_tree = dict(((self.name, k), v) for k, v in function_visitor.calls.iteritems())

    def remove_builtins(self):
        """ For many classes, we may not want to include builtin functions in the graph.
        Remove builtins from the call tree and from called functions list
        """
        new_call_tree = {}
        for caller, call_list in self.call_tree.iteritems():
            for call in call_list:
                if __builtins__.has_key(call[0]):
                    continue
                try:
                    new_call_tree[caller].append(call)
                except KeyError:
                    new_call_tree[caller] = [call]

        self.call_tree = new_call_tree

    def __repr__(self):
        return "ClassObject {}".format(self.name)

    def __str__(self):
        functions = [fcn.name for fcn in self.functions]
        return "Class {}\nDefined functions: {}\nCalled functions: {}".format(self.name, functions, self.called_functions)


class FunctionObject(object):
    def __init__(self, aliases=None, modules=None):
        self.modules = copy.deepcopy(modules) if modules else {}
        self.aliases = copy.deepcopy(aliases) if aliases else {}
        self.name = ''
        self.node = None
        self.called_functions = []
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
    """
    def __init__(self, **kwargs):
        super(CallVisitor, self).__init__(**kwargs)
        self.defined_functions = set()
        self.call_names = set()
        self.calls = []

    def continue_parsing(self, node):
        super(CallVisitor, self).generic_visit(node)

    def visit_Call(self, node):
        call_visitor = CallInspector()
        call_visitor.visit(node.func)
        self.call_names.add(call_visitor.identifier)
        if call_visitor.module and call_visitor.module in self.aliases:
            call = (call_visitor.module, call_visitor.identifier)
        else:
            call = (call_visitor.identifier,)
        self.calls.append(call)


class FunctionVisitor(ImportVisitor):
    """ Function definitions are where the function is defined, and the call is where the ast for that function exists

    This only looks for items that are called within the scope of a function, and associates those items
    with the function
    """
    def __init__(self, **kwargs):
        super(FunctionVisitor, self).__init__(**kwargs)
        self.defined_functions = set()
        self.functions = []
        self.call_names = set()
        self.calls = {}

    def continue_parsing(self, node):
        super(FunctionVisitor, self).generic_visit(node)

    def visit_FunctionDef(self, node):
        self.defined_functions.add(node.name)
        function_def = FunctionObject(aliases=self.aliases, modules=self.modules)
        function_def.name = node.name
        function_def.node = node
        function_def.visit()
        self.calls[function_def.name] = function_def.calls
        self.functions.append(function_def)


class FileVisitor(ImportVisitor):
    def __init__(self):
        super(FileVisitor, self).__init__()
        self.classes = []

    def continue_parsing(self, node):
        super(FileVisitor, self).generic_visit(node)

    def visit_Module(self, node):
        self.continue_parsing(node)

    def visit_ClassDef(self, node):
        # once a class is found, create a class object for it and traverse the ast with its visitor
        new_class = ClassObject(node.name, aliases=self.aliases, modules=self.modules)
        new_class.node = node
        new_class.visit()
        self.classes.append(new_class)
