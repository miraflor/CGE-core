"""
CGE-Core: A Pyomo-based CGE framework faithful to Hosoe et al. (2010).

Fork of PyCGE (Juan Fung & Charley Burtwistle, NIST) with bug fixes,
a Walras'-law degree-of-freedom correction for local NLP solving, and
a pytest regression suite.

Original PyCGE: https://github.com/juanfung/pycge
"""
from setuptools import setup, find_packages

setup(
    name='cge-core',
    version='0.2.0',
    python_requires='>=3.9',
    install_requires=[
        'pyomo>=6.0',
        'dill>=0.3',
    ],
    extras_require={
        # one local NLP solver is required; cyipopt is pip-installable
        # (needs the IPOPT system library + PyNumero ASL extension), or
        # supply an 'ipopt' executable on PATH instead.
        'solver': ['cyipopt>=1.4'],
        'test': ['pytest>=7.0'],
    },
    packages=find_packages(),
    url='https://github.com/jamesmiraflor/CGE-Core',
    license='MIT',
    description=('A Pyomo-based CGE framework faithful to '
                 'Hosoe, Gasawa & Hashimoto (2010)'),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='James Miraflor',
    author_email='james.miraflor@gmail.com',
    include_package_data=True,
    package_data={'cge_core': ['data/**/*.csv']},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
    ],
)
