from setuptools import setup, find_packages

setup(
    name="dizical",
    version="0.1.0",
    packages=find_packages(),
    package_dir={"src": "src"},
    include_package_data=True,
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "chinese-calendar>=1.8.0",
        "python-dateutil>=2.8.2",
        "python-dotenv>=1.0.0",
        "wcwidth>=0.2.13",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "python-multipart>=0.0.6",
    ],
    author="mtt",
    description="竹笛课程管理 + 缴费提醒 + 统计助手",
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "dizical=src.cli:app",
            "dizical-kid=src.kid_app.__main__:kid_app",
        ],
    },
)
