from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='SBOannotator',
    version='3.0.2',
    description='SBOannotator: A Python tool for the automated assignment of Systems Biology Ontology terms',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/draeger-lab/SBOannotator',
    author='Nantia Leonidou, Elisabeth Fritze, Alina Renz, Andreas Dräger',
    author_email='nantia.leonidou@uni-tuebingen.de',
    license='GPL-3.0',
    keywords=['SBOannotator', 'SBO Terms', 'automated tool'],
    install_requires=['python-libsbml',
                      'python-collection',
                      'requests',
                      'pypi-json'],
    packages=find_packages(where='src'),
    py_modules=['SBOannotator', '__main__'],
    package_dir={"": "src"},
    # include database file via MANIFEST.in
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Version Control :: Git",
        "Operating System :: MacOS",
        "Operating System :: Unix"
    ],
)
