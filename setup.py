from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="voicedev",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Offline voice dictation for macOS developers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/voicedev",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=[
        "faster-whisper>=0.10.0",
        "pyaudio>=0.2.13",
        "pynput>=1.7.6",
        "pyperclip>=1.8.2",
        "PyQt6>=6.6.0",
        "numpy>=1.24.0",
        "pyobjc-framework-Cocoa>=10.0; sys_platform == 'darwin'",
        "pyobjc-framework-Quartz>=10.0; sys_platform == 'darwin'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pyinstaller>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "voicedev=voicedev.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "voicedev": ["resources/*"],
    },
)
