import ast

import click

from parsing.parser import FileVisitor


@click.command()
@click.argument('code', type=click.File('rb'))
@click.option('--printed', default=False, is_flag=True, help='Pretty prints the call tree for each class in the file')
def cli(code, printed):
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
            click.echo('=' * 80)
            click.echo(class_object.name)
            click.echo(class_object.pprint())
            click.echo('')
