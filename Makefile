ACCEPTANCE_PY_REQUIRES = robotframework==3.0.4

.PHONY: acceptance
acceptance:
	# Must have GNU sed in your path for script to work
	sed --version | grep GNU
ifeq (,$(wildcard .at_venv/))
	python3.7 -m venv .at_venv
	.at_venv/bin/python .at_venv/bin/pip install $(ACCEPTANCE_PY_REQUIRES)
endif
	mkdir -p .robot/
	PATH=$(CURDIR)/bin:$(PATH) .at_venv/bin/robot --outputdir=.robot/ acceptance_tests/
