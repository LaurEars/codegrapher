import ast
from parsing.parser import FileVisitor


def test_import_visitor():
    function_string = '''import ast'''
    parsed_function = ast.parse(function_string, filename='parsed_function.py')
    visitor = FileVisitor()
    visitor.visit(parsed_function)
    assert 'ast' in visitor.modules
    assert 'ast' in visitor.aliases


def test_import_aliasing():
    code = '''
import ast
from copy import deepcopy as dc

string1 = 'this'
string2 = dc(string1)
'''
    parsed_code = ast.parse(code, filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    assert 'dc' in visitor.modules
    assert 'dc' in visitor.aliases
    assert visitor.modules['dc'] == 'copy'
    assert visitor.aliases['dc'] == 'deepcopy'


def test_import_deep_scope_dealiasing():
    code = '''
import ast
from copy import deepcopy as dc

class StringCopier(object):
    def copy(self):
        string1 = 'this'
        string2 = dc(string1)
        return string2
'''
    parsed_code = ast.parse(code, filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    string_class_object = visitor.classes[0]
    assert 'dc' in string_class_object.modules
    assert 'dc' in string_class_object.aliases
    assert string_class_object.modules['dc'] == 'copy'
    assert string_class_object.aliases['dc'] == 'deepcopy'


def test_class_declaration():
    code = '''
import ast
from copy import deepcopy as dc

class StringCopier(object):
    string1 = 'this'
    string2 = dc(string1)
'''
    parsed_code = ast.parse(code, filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    assert 'StringCopier' in (c.name for c in visitor.classes)


def test_function_declaration():
    code = '''
import ast
from copy import deepcopy as dc

class StringCopier(object):
    def copy(self):
        string1 = 'this'
        string2 = dc(string1)
        return string2
'''
    parsed_code = ast.parse(code, filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    string_class_object = visitor.classes[0]
    assert 'copy' in (f.name for f in string_class_object.functions)
