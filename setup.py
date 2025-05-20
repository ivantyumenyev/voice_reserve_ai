from setuptools import setup, find_packages

setup(
    name="voice_reserve_ai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-openai",
        "pydantic",
    ],
    python_requires=">=3.10",
) 