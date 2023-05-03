import os

from click.testing import CliRunner

from cli.script import cli


def get_graph_code():
    return '''
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


def test_produce_graph():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('code.py', 'w') as f:
            f.write(get_graph_code())

        runner.invoke(cli, ['code.py', '--output', 'code_output'])
        assert 'code_output' in os.listdir(os.path.curdir)


def test_file_extension():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('code.py', 'w') as f:
            f.write(get_graph_code())

        runner.invoke(cli, ['code.py', '--output', 'code_output', '--output-format', 'png'])
        assert 'code_output' in os.listdir(os.path.curdir)
