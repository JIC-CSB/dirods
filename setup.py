from setuptools import setup

url = ""
version = "0.1.0"
readme = open('README.rst').read()

setup(name="dirods",
      packages=["dirods"],
      version=version,
      description="Manage datasets in iRODS",
      long_description=readme,
      include_package_data=True,
      author="Matthew Hartley",
      author_email="Matthew.Hartley@jic.ac.uk",
      url=url,
      install_requires=[
          "click",
          "dtoolcore",
          "pygments",
          "python-irodsclient",
      ],
      entry_points={
          'console_scripts': ['dirods=dirods.cli:cli']
      },
      download_url="{}/tarball/{}".format(url, version),
      license="MIT")
