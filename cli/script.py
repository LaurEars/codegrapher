import click

from codegrapher.graph import FunctionGrapher
from codegrapher.parser import FileObject


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
    file_object = FileObject(code.name)
    file_object.visit()
    file_object.namespace()
    if remove_builtins:
        file_object.remove_builtins()
    if printed:
        click.echo('Classes in file:')
        for class_object in file_object.classes:
            click.echo('=' * 80)
            click.echo(class_object.name)
            click.echo(class_object.pprint())
            click.echo('')
    if output:
        graph = FunctionGrapher()
        graph.add_visitor_to_graph(file_object)
        graph.name = output
        graph.format = output_format
        graph.render()
