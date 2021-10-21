.PHONY: all mypy flake8 tests zonedbpy

all: mypy flake8 tests

#------------------------------------------------------------------------------
# Python mypy, flake8 and unittests
#------------------------------------------------------------------------------

mypy:
	mypy --strict \
		--exclude src/acetime/zonedbpy \
		src tests benchmarks

tests:
	python3 -m unittest

# W503 and W504 are both enabled by default and are mutual
# contradictory, so we have to suppress one of them.
# E501 uses 79 columns by default, but 80 is the default line wrap in
# vim, so change the line-length.
flake8:
	flake8 . \
		--exclude=src/acetime/zonedbpy \
		--count \
		--ignore W503 \
		--show-source \
		--statistics \
		--max-line-length=80

#------------------------------------------------------------------------------
# Generate the zonedbpy files with 'zonedbpy' target.
#------------------------------------------------------------------------------

zonedby:
	$(MAKE) -C src/acetime/zonedbpy

clean:
	$(MAKE) -C src/acetime/zonedbpy clean
