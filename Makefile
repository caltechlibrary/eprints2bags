# =============================================================================
# @file    Makefile
# @brief   Makefile for some steps in creating releases
# @author  Michael Hucka
# @date    2019-11-08
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/eprints2bags
# =============================================================================

version := $(shell grep 'version\s*=' setup.cfg | cut -f2 -d'=' | tr -d '[:blank:]')
branch  := $(shell git rev-parse --abbrev-ref HEAD)

release:;
ifeq ($(branch),master)
	sed -i .bak -e "/version/ s/[0-9].[0-9].[0-9]/$(version)/" codemeta.json
	git add codemeta.json
	git diff-index --quiet HEAD || git commit -m"Update version number" codemeta.json
	git tag -a v$(version) -m "Release $(version)"
	git push -v --all
	git push -v --tags
	$(info Go to GitHub and fill out new release info)
else
	$(error Current git branch != master. Merge changes into master first)
endif
