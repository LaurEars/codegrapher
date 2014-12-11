import ast

import click

from parsing.parser import FileVisitor


@click.command()
@click.argument('code', type=click.File('rb'))
@click.option('--printed', default=False, is_flag=True, help='Pretty prints the call tree for each class in the file')
@click.option('--remove-builtins', default=False, is_flag=True, help='Removes builtin functions from call trees')
def cli(code, printed, remove_builtins):
    """
    Parses a file.
    codegrapher [file_name]
    """
    parsed_code = ast.parse(code.read(), filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    if printed:
        click.echo('Classes in file:')
        for class_object in visitor.classes:
            if remove_builtins:
                class_object.remove_builtins()
            click.echo('=' * 80)
            click.echo(class_object.name)
            click.echo(class_object.pprint())
            click.echo('')
