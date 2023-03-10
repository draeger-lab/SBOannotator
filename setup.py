from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='SBOannotator',
    version='2.0.4',
    description='SBOannotator: A Python tool for the automated assignment of Systems Biology Ontology terms',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/draeger-lab/SBOannotator',
    author='Nantia Leonidou, Elisabeth Fritze, Alina Renz, Andreas Dräger',
    author_email='nantia.leonidou@uni-tuebingen.de',
    license=' GPL-3.0',
    keywords=['SBOannotator', 'SBO Terms', 'automated tool'],
    packages=find_packages(where='SBOannotator', include=['SBOannotator', 'main']),
    install_requires=['python-libsbml',
                      'python-collection',
                      'requests',
                      'pypi-json'],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Version Control :: Git",
        "Operating System :: MacOS",
        "Operating System :: Unix"

    ],
)
