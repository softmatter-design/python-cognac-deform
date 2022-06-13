"""Minimal setup file for tasks project."""

from setuptools import setup, find_packages


setup(
    name='cognac-deform',
    version='0.0.2',
    license='proprietary',
    description='Module Experiment',

    author='hsasaki',
    author_email='hsasaki@softmatters.net',
    url='https://github.com/softmatter-design/python-cognac-deform/',

    packages=find_packages(where='src'),
    package_dir={'': 'src'},

    entry_points={
        "console_scripts": [
          'deform_setup = cognac_deform.deform_setup:main',
          'evaluate_simple_deform = evaluate_simple_deform.eval_sim_def:main',
          'evaluate_cyclic_deform = evaluate_simple_deform.eval_cyc_def:main'
        ]
    }
)