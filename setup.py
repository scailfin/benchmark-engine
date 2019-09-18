from setuptools import setup, find_packages


install_requires=[
    'future',
    'passlib',
    'python-dateutil',
    'pyyaml>=5.1',
    'benchmark-templates>=0.2.0'
]


tests_require = [
    'coverage>=4.0',
    'pytest',
    'pytest-cov',
    'tox'
]


extras_require = {
    'docs': [
        'Sphinx',
        'sphinx-rtd-theme'
    ],
    'tests': tests_require,
}


setup(
    name='benchmark-api',
    version='0.2.0',
    description='API for Reproducible Open Benchmarks',
    keywords='reproducibility benchmarks data analysis',
    license='MIT',
    packages=find_packages(exclude=('tests',)),
    include_package_data=True,
    extras_require=extras_require,
    tests_require=tests_require,
    install_requires=install_requires,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python'
    ]
)
