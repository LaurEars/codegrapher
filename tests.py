import ast
from parsing.parser import FileVisitor


def test_import_visitor():
    function_string = '''import ast'''
    parsed_function = ast.parse(function_string, filename='parsed_function.py')
    visitor = FileVisitor()
    visitor.visit(parsed_function)
    assert 'ast' in visitor.modules
    assert 'ast' in visitor.aliases
