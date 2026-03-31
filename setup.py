from setuptools import setup, find_packages
import pathlib

# Read the long description from README.md if it exists
here = pathlib.Path(__file__).parent
readme_path = here / "README.md"
if readme_path.is_file():
    long_description = readme_path.read_text(encoding="utf-8")
else:
    long_description = "Bud Credit Form Application"

setup(
    name="baked",
    version="0.1.0",
    description="Bud Credit Form Application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Andile Sizophila Mchunu",
    author_email="andilexmchunu@gmail.com",
    url="https://github.com/Skywalkingzulu1/baked",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask",
        "python-dotenv",
        "psycopg2-binary",
        "PyJWT",
        "bcrypt",
        "pydantic",
        "pydantic-settings",
        "tenacity",
        "fastapi",
        "uvicorn"
    ],
    python_requires=">=3.11",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
