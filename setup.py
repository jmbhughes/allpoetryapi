from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='allpoetryapi',
      version='0.0.1',
      description='API to fetch poetry from allpoetry.com',
      url='https://github.com/jmbhughes/allpoetryapi',
      author='J. Marcus Hughes',
      author_email='hughes.jmb@gmail.com',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      # test_suite='nose.collector',
      # tests_require=['nose'],
      scripts=[],
      long_description=long_description,
      long_description_content_type="text/markdown",
      install_requires=['requests',
                        'bs4',
                        'lxml',
                        'python-dateutil',
                        'Pillow'])
