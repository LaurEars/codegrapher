from graphviz import Digraph


class FilenameNotSpecifiedException(Exception):
    """ An exception raised when a file name is not specified in a :class:`FunctionGrapher` instance before calling
    :func:`FunctionGrapher.render` on it.
    """
    pass


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

    def add_visitor_to_graph(self, visitor):
        """ When given a :class:`codegrapher.parser.FileVisitor` object, this adds all classes to the current graph.

        Arguments:
            visitor (:class:`codegrapher.parser.FileVisitor`): Visitor objects to have all its classes added to the
              current graph.
        """
        class_names = set(cls.name for cls in visitor.classes)
        for cls in visitor.classes:
            self.add_dict_to_graph(class_names, cls.call_tree)
        self.add_classes_to_graph(visitor.classes)

    def add_dict_to_graph(self, class_names, dictionary):
        """ Creates a list of nodes and edges to be rendered. Deduplicates input.

        Arguments:
            class_names (list): List of class names to be recognized by the graph as `class_name.__init__` nodes.
            dictionary (dict): `ClassObject.call_tree` dict to be added to graph nodes and edges.
        """
        # todo: better handle project hierarchy by looking at imports

        # add nodes
        for origin in dictionary:
            self.nodes.add(origin)
            for destination in dictionary[origin]:
                if destination[0] in class_names:
                    destination = (destination[0], '__init__')
                self.nodes.add(destination)

        # add edges
        for origin in dictionary:
            for destination in dictionary[origin]:
                # if destination is a class name, it is a constructor
                if destination[0] in class_names:
                    destination = (destination[0], '__init__')
                self.edges.add((origin, destination))

    def add_classes_to_graph(self, classes):
        """ Adds classes with constructors to the set.
        This adds edges between a class constructor and the methods called on those items.

        Arguments:
            classes (list): list of :class:`codegrapher.parser.ClassObject` items.
        """
        # todo: separate class methods from instance methods
        for cls in classes:
            functions = set(fcn.name for fcn in cls.functions)
            if '__init__' in functions:
                self.nodes.add((cls.name, '__init__'))
                for fcn in functions:
                    if fcn == '__init__':
                        continue  # skip the case where init would refer back to itself
                    self.edges.add(((cls.name, '__init__'), (cls.name, fcn)))

    def render(self, name=None):
        """ Renders the current graph.

        Arguments:
            name (string): filename to override `self.name`.

        Raises:
            FilenameNotSpecifiedException: If `FunctionGrapher.name` is not specified.
        """
        for node in self.nodes:
            if isinstance(node, tuple):
                self.dot_file.node('.'.join(node), '.'.join(node))
            else:
                self.dot_file.node(node)
        for edge in self.edges:

            new_edge = []
            if isinstance(edge[0], tuple):
                new_edge.append('.'.join(edge[0]))
            else:
                new_edge.append(edge[0])
            if isinstance(edge[1], tuple):
                new_edge.append('.'.join(edge[1]))
            else:
                new_edge.append(edge[1])
            self.dot_file.edge(*new_edge)
        if name is None:
            if not self.name:
                raise FilenameNotSpecifiedException
            name = self.name
        self.dot_file.render(name)