

build:
	python3 setup.py sdist

test:
	tox


clean:
	rm -rf Gladiator.egg-info
	rm -f dist/*.tar.gz

git_tag:
	git tag $(CURRENT_VERSION)

pypi_upload:
	python3 setup.py sdist upload -r pypi

pypi_register:
	python3 setup.py register -r pypi

pypitest_upload:
	python3 setup.py sdist upload -r pypitest

pypitest_register:
	python3 setup.py register -r pypitest

release: clean test build
	echo "1. runnint tests"
	echo "2. Change version"
	echo "3. commit and create tag"
	echo "4. git push --tags"
	echo "5. setup.py upload"

