from setuptools import setup, find_packages

from aws_mail._version import __version__


setup(
    name="aws_mail",
    version=__version__,
    author="Norman Moeschter-Schenck",
    author_email="norman.moeschter@gmail.com",
    maintainer="Norman Moeschter-Schenck",
    maintainer_email="<norman.moeschter@gmail.com>",
    url="https://github.com/normoes/aws_mail",
    download_url=f"https://github.com/normoes/aws_mail/archive/{__version__}.tar.gz",
    description=("AWS sendmail replacement using boto3."),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests*"]),
    scripts=["bin/aws_mail"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
    ],
    install_requires=["eventhooks[aws]>=0.3", "pyyaml>=5.4.1"],
)
