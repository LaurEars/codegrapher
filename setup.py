from setuptools import setup, find_packages


setup(
    name='codegrapher',
    version='0.1.1',
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
    tests_require=['nose'],
    entry_points='''
        [console_scripts]
        codegrapher=script:cli
    ''',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Software Development :: Documentation',
    ]
)
