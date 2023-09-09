from os import path

import setuptools

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

from drafter import __version__

setuptools.setup(
    name='drafter',
    version=__version__,
    python_requires='>=3.7',
    author='acbart',
    py_modules=['drafter'],
    #package_data={
    #    'websites': [] #'data/emojis.zip']
    #},
    author_email='acbart@udel.edu',
    description='Student-friendly full stack web development library.',
    install_requires=REQUIREMENTS,
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/drafter-edu/drafter',
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Topic :: Education',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ])