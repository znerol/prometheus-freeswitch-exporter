import codecs
from setuptools import find_packages
from setuptools import setup

setup(
    name="prometheus-freeswitch-exporter",
    version="1.0.1",
    author="Lorenz Schori",
    author_email="lo@znerol.ch",
    description=("FreeSWITCH exporter for the Prometheus monitoring system."),
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    license="Apache Software License 2.0",
    keywords="prometheus exporter network monitoring voip",
    url="https://github.com/znerol/prometheus-freeswitch-exporter",
    package_dir={"": "src"},
    packages=find_packages('src'),
    entry_points={
        'console_scripts': [
            'freeswitch_exporter=freeswitch_exporter.cli:main',
        ],
    },
    test_suite="tests",
    install_requires=[
        "asgiref",
        "prometheus_client>=0.0.11",
        "pyyaml",
        "requests",
        'Werkzeug',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: Apache Software License",
    ],
)
