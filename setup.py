from setuptools import setup, find_packages

import codegrapher


setup(
    name='codegrapher',
    version=codegrapher.__version__,
    description='Code that graphs code',
    url='http://github.com/LaurEars/codegrapher',
    author='Laura Rupprecht',
    author_email='lauracr@bu.edu',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'graphviz'
    ],
    tests_require=[
        'coverage'
    ],
    entry_points='''
        [console_scripts]
        codegrapher=cli:cli
    ''',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Software Development :: Documentation',
    ]
)
