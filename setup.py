#!/usr/bin/env python3
"""
Setup script for Smart Log Analyzer

This script configures the Smart Log Analyzer package for installation
and distribution.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "scikit-learn>=1.1.0",
        "joblib>=1.2.0",
        "nltk>=3.8",
        "jira>=3.4.0",
        "click>=8.1.0"
    ]

setup(
    name="smart-log-analyzer",
    version="1.0.0",
    author="Development Team",
    author_email="dev-team@company.com",
    description="Intelligent Error Pattern Detection & Automated Defect Management System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/company/smart-log-analyzer",
    project_urls={
        "Bug Tracker": "https://github.com/company/smart-log-analyzer/issues",
        "Documentation": "https://github.com/company/smart-log-analyzer/docs",
        "Source Code": "https://github.com/company/smart-log-analyzer",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(include=["src", "src.*"]),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.1.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "ml": [
            "tensorflow>=2.10.0",
            "torch>=1.12.0",
            "transformers>=4.21.0",
            "spacy>=3.4.0",
        ],
        "viz": [
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
            "plotly>=5.10.0",
        ],
        "database": [
            "sqlalchemy>=1.4.0",
            "psycopg2-binary>=2.9.0",
            "pymongo>=4.2.0",
        ],
        "monitoring": [
            "prometheus-client>=0.14.0",
            "sentry-sdk>=1.9.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "smart-log-analyzer=src.main:main",
            "sla=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": [
            "configs/*.yaml",
            "configs/*.yml",
            "data/models/*",
        ],
    },
    zip_safe=False,
    keywords=[
        "log analysis",
        "machine learning",
        "error detection",
        "pattern recognition",
        "automation",
        "jira integration",
        "defect management",
        "anomaly detection",
        "nlp",
        "monitoring"
    ],
    platforms=["any"],
)
