from graphviz import Digraph


class FilenameNotSpecifiedException(Exception):
    pass


class FunctionGrapher(object):
    def __init__(self):
        self.name = ''
        self.dot_file = Digraph()
        self.nodes = set()
        self.edges = set()

    def add_dict_to_graph(self, dictionary):
        """ Creates a list of nodes and edges to be rendered
        Deduplicates input
        """
        # add nodes
        for origin in dictionary:
            self.nodes.add(origin)
            for destination in dictionary[origin]:
                self.nodes.add(destination)
                
        # add edges
        for origin in dictionary:
            for destination in dictionary[origin]:
                self.edges.add((origin, destination))

    def render(self, name=None):
        """ Renders the current graph
        name (optional): filename to override self.name
        """
        for node in self.nodes:
            self.dot_file.node(node)
        for edge in self.edges:
            self.dot_file.edge(*edge)
        if name is None:
            if not self.name:
                raise FilenameNotSpecifiedException
            name = self.name
        self.dot_file.render(name)