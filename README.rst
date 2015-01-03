codegrapher
===========

.. image:: https://travis-ci.org/LaurEars/codegrapher.svg?branch=master
    :target: https://travis-ci.org/LaurEars/codegrapher


Code that graphs code
---------------------
Uses the python `AST <https://docs.python.org/2/library/ast.html>`_ to parse Python source code and build a call graph.


Output
------
An example of the current output of the parser parsing itself.

.. image:: http://i.imgur.com/QMES0Na.png
    :target: http://i.imgur.com/QMES0Na.png
    :align: center
    :width: 600 px
    :alt: parser.py


Installation
------------

.. code:: bash

    pip install codegrapher


To generate graphs, `graphviz <http://www.graphviz.org/Download.php>`_ must be installed.


Usage
-----

To parse a file and output results to the console:

.. code:: bash

    codegrapher path/to/file.py --printed


To parse a file and output results to a file:

.. code:: bash

    codegrapher path/to/file.py --output output_file_name --output-type png
