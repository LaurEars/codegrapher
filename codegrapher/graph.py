from graphviz import Digraph


class FilenameNotSpecifiedException(Exception):
    """ An exception raised when a file name is not specified in a :class:`FunctionGrapher` instance before calling
    :func:`FunctionGrapher.render` on it.
    """
    pass


class Node(object):
    """ A class to more easily handle manipulations needed to properly display nodes in a graph.
    Optimized to handle nodes that represent functions in a program.

    Attributes:
        tuple (tuple): Contains the namespace, class, and function name for the current node.
    """
    def __init__(self, input_node):
        if isinstance(input_node, tuple):
            self.tuple = input_node
        else:
            self.tuple = (input_node,)

    @property
    def represent(self):
        """ Provides a string representation of the current node

        Returns:
            (string): Dotted form of current node, as in `namespace.class.function_name`.
        """
        return '.'.join(self.tuple)

    def __str__(self):
        return '.'.join(self.tuple)

    def __repr__(self):
        return "<Node: {}>".format(self.tuple)

    def __hash__(self):
        return hash('.'.join(self.tuple))

    def __eq__(self, other):
        return self.tuple == other.tuple


class FunctionGrapher(object):
    """ `FunctionGrapher` is a class for producing `graphviz <http://www.graphviz.org/>`_ graphs showing the call
    graph for sets of classes.

    Attributes:
        name (string): Name to be used when a graph is made.
        nodes (set): Graphviz nodes to be graphed.
        edges (set): Directional edges connecting one node to another.
        format (string): File format for graph. Default is `pdf`.
    """
    def __init__(self):
        self.name = ''
        self.dot_file = Digraph()
        self.nodes = set()
        self.edges = set()

    @property
    def format(self):
        return self.dot_file.format

    @format.setter
    def format(self, value):
        self.dot_file.format = value

    def add_file_to_graph(self, file_object):
        """ When given a :class:`codegrapher.parser.FileObject` object, this adds all classes to the current graph.

        Arguments:
            file_object (:class:`codegrapher.parser.FileObject`): Visitor objects to have all its classes added to the
              current graph.
        """
        class_namespace = dict((cls.name, file_object.relative_namespace) for cls in file_object.classes)
        for cls in file_object.classes:
            self.add_dict_to_graph(class_namespace, cls.call_tree, file_object.relative_namespace)
        self.add_classes_to_graph(file_object.classes, file_object.relative_namespace)

    def add_dict_to_graph(self, class_names, dictionary, relative_namespace):
        """ Creates a list of nodes and edges to be rendered. Deduplicates input.

        Arguments:
            class_names (list): List of class names to be recognized by the graph as `class_name.__init__` nodes.
            dictionary (dict): `ClassObject.call_tree` dict to be added to graph nodes and edges.
        """
        # todo: better handle project hierarchy by looking at imports
        # add nodes
        for origin in dictionary:
            self.nodes.add(Node(origin))
            for destination in dictionary[origin]:
                if destination[0] in class_names:
                    destination = Node((relative_namespace, destination[0], '__init__'))
                else:
                    destination = Node(destination)
                self.nodes.add(destination)

        # add edges
        for origin in dictionary:
            for destination in dictionary[origin]:
                # if destination is a class name, it is a constructor
                if destination[0] in class_names:
                    destination = (relative_namespace, destination[0], '__init__')
                else:
                    destination = destination
                self.edges.add((Node(origin), Node(destination)))

    def add_classes_to_graph(self, classes, relative_namespace):
        """ Adds classes with constructors to the set.
        This adds edges between a class constructor and the methods called on those items.

        Arguments:
            classes (list): list of :class:`codegrapher.parser.ClassObject` items.
        """
        # todo: separate class methods from instance methods
        for cls in classes:
            functions = set(fcn.name for fcn in cls.functions)
            if '__init__' in functions:
                self.nodes.add(Node((relative_namespace, cls.name, '__init__')))
                for fcn in functions:
                    if fcn == '__init__':
                        continue  # skip the case where init would refer back to itself
                    self.edges.add((Node((relative_namespace, cls.name, '__init__')),
                                    Node((relative_namespace, cls.name, fcn))))

    def render(self, name=None):
        """ Renders the current graph.

        Arguments:
            name (string): filename to override `self.name`.

        Raises:
            FilenameNotSpecifiedException: If `FunctionGrapher.name` is not specified.
        """
        for node in self.nodes:
            self.dot_file.node(node.represent)
        for edge in self.edges:
            self.dot_file.edge(edge[0].represent, edge[1].represent)
        if name is None:
            if not self.name:
                raise FilenameNotSpecifiedException
            name = self.name
        self.dot_file.render(name)
