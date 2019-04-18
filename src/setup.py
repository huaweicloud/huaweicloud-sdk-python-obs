#-*- coding:utf-8 -*-

#use 'python setup.py bdist_egg' to generate the egg file package
#use 'easy_install eggfile' to install the egg file to the python Lib

#or

#use 'python setup.py install' to install to the python Lib directly


from setuptools import setup, find_packages

setup(
    name='esdk-obs-python',
    version='3.1.2.1',
    packages=find_packages(),
    zip_safe=False,
    description='OBS Python SDK',
    long_description='OBS Python SDK',
    license='Apache-2.0',
    keywords=('obs', 'python'),
    platforms='Independant',
    url='',
)
