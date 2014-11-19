import ast


class ClassObject(object):
    def __init__(self, name):
        self.name = name
        self.node = None
        self.functions = []
        self.called_functions = []
        self.call_tree = {}

    def visit(self):
        function_visitor = FunctionVisitor()
        function_visitor.visit(self.node)
        self.functions = function_visitor.defined_functions
        self.called_functions = function_visitor.call_names
        self.call_tree = function_visitor.calls

    def __repr__(self):
        return "ClassObject {}".format(self.name)

    def __str__(self):
        return "Class {}\nDefined functions: {}\nCalled functions: {}".format(self.name, self.functions, self.called_functions)


class CallVisitor(ast.NodeVisitor):
    """ Within a call, a Name or Attribute will provide the function name currently in use

    Name vs. attribute:
        name(args)
        object.attr(args)
    """
    def __init__(self):
        self.identifier = ''

    def visit_Name(self, node):
        self.identifier = node.id

    def visit_Attribute(self, node):
        # todo: pull out item for the attr to determine whether node defines a classmethod
        self.identifier = node.attr


class FunctionVisitor(ast.NodeVisitor):
    """ Function definitions are where the function is defined, and the call is where the ast for that function exists

    This only looks for items that are called within the scope of a function, and associates those items
    with the function
    """
    def __init__(self):
        self.defined_functions = set()
        self.call_names = set()
        self.last_defined_func = ''
        self.calls = {}

    def continue_parsing(self, node):
        super(FunctionVisitor, self).generic_visit(node)

    def visit_FunctionDef(self, node):
        self.defined_functions.add(node.name)
        self.last_defined_func = node.name
        self.calls[node.name] = []
        self.continue_parsing(node)

    def visit_Expr(self, node):
        self.continue_parsing(node)

    def visit_Call(self, node):
        # we're only looking at items contained in a function in a class
        if self.last_defined_func:
            # now visit each node using the call visitor
            call_visitor = CallVisitor()
            call_visitor.visit(node.func)
            self.call_names.add(call_visitor.identifier)
            self.calls[self.last_defined_func].append(call_visitor.identifier)

        self.continue_parsing(node)


class FileVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []

    def continue_parsing(self, node):
        super(FileVisitor, self).generic_visit(node)

    def visit_Module(self, node):
        self.continue_parsing(node)

    def visit_ClassDef(self, node):
        # once a class is found, create a class object for it and traverse the ast with its visitor
        new_class = ClassObject(node.name)
        new_class.node = node
        new_class.visit()
        self.classes.append(new_class)
        self.continue_parsing(node)
