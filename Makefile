.PHONY: acceptance
acceptance:
	# Must have GNU sed in your path for script to work
	sed --version | grep GNU
ifeq (,$(wildcard .at_venv/))
	python3 -m venv .at_venv
	source .at_venv/bin/activate
	pip install -r requirements.txt
endif
	mkdir -p .robot/
	CFSTEP_HELM_ROOTDIR=$(CURDIR) robot --outputdir=.robot/ acceptance_tests/
