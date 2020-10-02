from setuptools import setup, find_packages

with open("README.rst") as f:
    readme = f.read()

setup(
    name="pylas",
    version="0.4.2",
    description="Las/Laz reading and writing in python",
    long_description=readme,
    url="https://github.com/tmontaigu/pylas",
    author="Thomas Montaigu",
    author_email="thomas.montaigu@laposte.net",
    python_requires=">=3.6",
    keywords="las lidar",
    license="BSD 3-Clause",
    packages=find_packages(exclude=("pylastests",)),
    zip_safe=False,
    install_requires=["numpy"],
    extras_require={
        "dev": [
            "pytest",
            "sphinx",
            "sphinx-rtd-theme"
        ],
        "lazrs": [
            "lazrs>=0.2.0, < 0.3.0"
        ]
    }
)
