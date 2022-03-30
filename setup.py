"""Minimal setup file for tasks project."""

from setuptools import setup, find_packages

setup(
    name='cognac_deform',
    version='0.1.2',
    license='proprietary',
    description='Module Experiment',

    author='hsasaki',
    author_email='hsasaki@softmatters.net',
    url='https://github.com/softmatter-design/python-cognac-deform/',

    packages=find_packages(where='src'),
    package_dir={'': 'src'},

    entry_points={
        "console_scripts": [
          'deform_setup = cognac_deform.deform_setup:main'
        ]
    }
)