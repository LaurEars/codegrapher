import ast

import click

from graphing.graph import FunctionGrapher
from parsing.parser import FileVisitor


@click.command()
@click.argument('code', type=click.File('rb'))
@click.option('--printed', default=False, is_flag=True, help='Pretty prints the call tree for each class in the file')
@click.option('--remove-builtins', default=False, is_flag=True, help='Removes builtin functions from call trees')
@click.option('--output', help='Graphviz output file name')
@click.option('--output-format', default='pdf', help='File type for graphviz output file')
def cli(code, printed, remove_builtins, output, output_format):
    """
    Parses a file.
    codegrapher [file_name]
    """
    parsed_code = ast.parse(code.read(), filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    if remove_builtins:
        visitor.remove_builtins()
    if printed:
        click.echo('Classes in file:')
        for class_object in visitor.classes:
            click.echo('=' * 80)
            click.echo(class_object.name)
            click.echo(class_object.pprint())
            click.echo('')
    if output:
        graph = FunctionGrapher()
        class_names = set(cls.name for cls in visitor.classes)
        for cls in visitor.classes:
            graph.add_dict_to_graph(class_names, cls.call_tree)
        graph.add_classes_to_graph(visitor.classes)
        graph.name = output
        graph.format = output_format
        graph.render()
