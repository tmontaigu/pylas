from setuptools import setup, find_packages

with open("README.rst") as f:
    readme = f.read()

setup(
    name="pylas",
    version="0.2.0",
    description="Las/Laz reading and writing in python",
    long_description=readme,
    url="https://github.com/tmontaigu/pylas",
    author="Thomas Montaigu",
    author_email="thomas.montaigu@laposte.net",
    python_requires=">=3",
    keywords="las lidar",
    install_requires=["numpy"],
    license="BSD 3-Clause",
    packages=find_packages(exclude=("pylastests",)),
    zip_safe=False,
)

