from setuptools import setup

setup(
    name='visiannot',
    version='0.2.0',    
    description='Graphical user interface for visualization and annotation of video and signal data',
    url='',
    author='Raphael Weber',
    author_email='raphael.weber@univ-rennes1.fr',
    license='CeCILL',
    packages=['visiannot'],
    package_dir={'': 'visiannot'},
    install_requires=[
        'configobj',
        'opencv-python',
        'h5py',
        'numpy',
        'PyQt5',
        'pyqtgraph',
        'pytz',
        'scipy',
    ],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
