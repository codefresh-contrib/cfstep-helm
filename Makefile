ACCEPTANCE_PY_REQUIRES = robotframework==3.0.4

HAS_VENV := $(shell command -v virtualenv)

.PHONY: acceptance
acceptance:
ifndef HAS_VENV
	$(error Must install virtualenv)
endif
ifeq (,$(wildcard .venv/))
	virtualenv -p $$(which python2.7) .venv/
	.venv/bin/python .venv/bin/pip install $(ACCEPTANCE_PY_REQUIRES)
endif
	mkdir -p .robot/
	PATH=$(CURDIR)/bin:$(PATH) .venv/bin/robot --outputdir=.robot/ acceptance_tests/
