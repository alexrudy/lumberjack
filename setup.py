from setuptools import setup, find_packages
import lumberjack

classifiers = [
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 3",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Topic :: Software Development :: Libraries",
    "Topic :: System :: Logging",
    "Topic :: Utilities",
]

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(name="lumberjack-logging",
      version=lumberjack.__version__,
      
      author="Alexander Rudy",
      author_email="alex.rudy@gmail.com",
      
      packages=find_packages(),
      
      description="Logging tools.",
      long_description=long_description,
      classifiers=classifiers,
      
      install_requires=['six'],
      package_data = {'lumberjack.config' : ['*.cfg'] },
      entry_points={
          'console_scripts':
          ['lumberjack-listen = lumberjack.listener:main']
      },
      )
