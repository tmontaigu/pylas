from setuptools import setup, find_packages

setup(
    name='pylas',
    version='0.1.0',
    description='Las/Laz in python',
    url='https://github.com/tmontaigu/pylas',
    author='Thomas Montaigu',
    python_requires='>=3',
    install_requires=['numpy'],
    license='BSD 3-Clause',
    packages=find_packages(exclude=('pylastests',)),
    zip_safe=False
)
