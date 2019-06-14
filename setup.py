from setuptools import setup


install_requires=[
    'future',
    'passlib',
    'python-dateutil',
    'pyyaml>=5.1',
    'benchmark-templates'
]


tests_require = [
    'coverage>=4.0',
    'coveralls',
    'nose'
]


extras_require = {
    'docs': [
        'Sphinx',
        'sphinx-rtd-theme'
    ],
    'tests': tests_require,
}


setup(
    name='benchmark-engine',
    version='0.1.0',
    description='Reproducible Benchmarks for Data Analysis Engine',
    keywords='reproducibility benchmarks data analysis',
    license='MIT',
    packages=['benchengine'],
    include_package_data=True,
    test_suite='nose.collector',
    extras_require=extras_require,
    tests_require=tests_require,
    install_requires=install_requires
)
