#!/usr/bin/env python3
"""
Setup script for AI Driven Realtime Log Analyser
"""

from setuptools import setup, find_packages
import os

def read_requirements():
    """Read requirements from requirements.txt"""
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def read_readme():
    """Read README.md for long description"""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "AI Driven Realtime Log Analyser"

setup(
    name="ai-driven-realtime-log-analyser",
    version="1.0.0",
    description="Enterprise-grade intelligent log analysis system with AI/ML capabilities and real-time monitoring",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="AI Log Analysis Team",
    author_email="contact@example.com",
    url="https://github.com/your-username/ai-driven-realtime-log-analyser",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.html", "*.css", "*.js"],
    },
    install_requires=read_requirements(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "ai-log-analyser=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="log-analysis machine-learning real-time monitoring dashboard ai ml",
    project_urls={
        "Bug Reports": "https://github.com/your-username/ai-driven-realtime-log-analyser/issues",
        "Source": "https://github.com/your-username/ai-driven-realtime-log-analyser",
        "Documentation": "https://github.com/your-username/ai-driven-realtime-log-analyser/wiki",
    },
)
