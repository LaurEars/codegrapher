import ast

from nose.tools import eq_
from click.testing import CliRunner

from script import cli
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
    eq_(visitor.modules['dc'], 'copy')
    eq_(visitor.aliases['dc'], 'deepcopy')


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
    eq_(string_class_object.modules['dc'], 'copy')
    eq_(string_class_object.aliases['dc'], 'deepcopy')


def test_import_module_call_alias_only():
    code = '''
import collections as coll

class CounterCounter(object):
    def __init__(self):
        self.new_counter = coll.Counter()

    def count(self, some_key):
        self.new_counter[some_key] += 1
'''
    parsed_code = ast.parse(code, filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    counting_class = visitor.classes[0]
    assert ('CounterCounter', '__init__') in counting_class.call_tree
    assert ('collections', 'Counter') in counting_class.call_tree[('CounterCounter', '__init__')]


def test_import_module_alias_call_by_attr():
    code = '''
from itertools import chain

class CounterCounter(object):
    def __init__(self):
        self.new_counter = coll.Counter()

    def count(self, some_key):
        self.new_counter[some_key] += 1

    def repeat(self):
        chain.from_iterable(['a', 'b', 'c'], ['1', '2', '3'])
'''
    parsed_code = ast.parse(code, filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    counting_class = visitor.classes[0]
    assert ('CounterCounter', 'repeat') in counting_class.call_tree
    assert ('itertools.chain', 'from_iterable') in counting_class.call_tree[('CounterCounter', 'repeat')]


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


def test_remove_builtins():
    code = '''
from copy import deepcopy as dc

class StringCopier(object):
    def __init__(self):
        self.copied_strings = set()

    def copy(self):
        string1 = 'this'
        string2 = dc(string1)
        string1.add(string1)
        return string2
'''
    parsed_code = ast.parse(code, filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    string_class_object = visitor.classes[0]
    assert ('StringCopier', '__init__') in string_class_object.call_tree
    assert ('set',) in string_class_object.call_tree[('StringCopier', '__init__')]

    string_class_object.remove_builtins()
    eq_(string_class_object.call_tree[('StringCopier', '__init__')], [])


def test_init_call():
    code = '''
from copy import deepcopy as dc

class StringCopier(object):
    def __init__(self):
        self.copied_strings = set()

    def copy(self):
        string1 = 'this'
        string2 = dc(string1)
        string1.add(string1)
        return string2

class DoSomething(object):
    def something(self):
        copier = StringCopier()
        copied_string = copier.copy()
'''
    parsed_code = ast.parse(code, filename='code.py')
    visitor = FileVisitor()
    visitor.visit(parsed_code)
    something_class = visitor.classes[1]
    assert ('DoSomething', 'something') in something_class.call_tree
    assert ('StringCopier',) in something_class.call_tree[('DoSomething', 'something')]


def test_cli_printed():
    code = '''
import ast
from copy import deepcopy as dc

class StringCopier(object):
    def copy(self):
        string1 = 'this'
        string2 = dc(string1)
        return string2
'''
    code_result = '''Classes in file:
================================================================================
StringCopier
{('StringCopier', 'copy'): [('copy', 'deepcopy')]}

'''
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('code.py', 'w') as f:
            f.write(code)

        result = runner.invoke(cli, ['code.py', '--printed'])
        eq_(result.exit_code, 0)
        eq_(result.output, code_result)


def test_cli_printed_remove_builtins():
    code = '''
from copy import deepcopy as dc

class StringCopier(object):
    def __init__(self):
        self.copied_strings = set()
'''
    code_result = '''Classes in file:
================================================================================
StringCopier
{('StringCopier', '__init__'): []}

'''
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('code.py', 'w') as f:
            f.write(code)

        result = runner.invoke(cli, ['code.py', '--printed', '--remove-builtins'])
        eq_(result.exit_code, 0)
        eq_(result.output, code_result)
