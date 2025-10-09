from setuptools import setup, find_packages

setup(
    name="video2note",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyYAML",
        "requests",
        "yt-dlp",
        "you-get",
        "bilix>=0.18.0",
        "openai",
        "httpx",
        "notion-client",
        "rich"
    ],
    python_requires=">=3.12",
)
