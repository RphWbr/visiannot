from setuptools import setup
from visiannot import __version__ as version


description = "Graphical user interface for visualization and annotation of video and signal data"

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='visiannot',
    version=version,    
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/RphWbr/visiannot',
    author='Raphael Weber',
    author_email='raphael.weber@univ-rennes1.fr',
    license='CeCILL',
    # package_dir={'': 'visiannot'},
    # packages=find_packages(where='visiannot'),
    packages=[
        'visiannot',
        'visiannot.visiannot',
        'visiannot.visiannot.components',
        'visiannot.configuration',
        'visiannot.tools'
    ],
    include_package_data=True,
    install_requires=[
        'configobj>=5.0.6',
        'opencv-python>=3.4.8.29',
        'h5py>=2.10.0',
        'numpy>=1.18.5',
        'PyQt5>=5.14.1',
        'pyqtgraph>=0.11.0',
        'pytz>=2019.3',
        'scipy>=1.5.3',
        'tinytag>=1.7.0'
    ],
    python_requires='>=3.6, <4',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)'
    ],
)
