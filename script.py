import ast

import click

from parsing.parser import FileVisitor


@click.command()
@click.argument('code', type=click.File('rb'))
def cli(code):
    """
    Parses a file.
    codegrapher [file_name]
    """
    parsed_code = ast.parse(code.read(), filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    click.echo('Classes in file:')
    for class_object in visitor.classes:
        click.echo(class_object.name)
