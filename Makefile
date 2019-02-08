.PHONY: install test

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	nosetests --with-coverage --cover-html --cover-package=codegrapher,cli
