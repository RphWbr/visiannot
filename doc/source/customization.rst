.. _customization:

=============
Customization
=============

As seen in :ref:`run`, it is possible to call a function to automatically update the configuration before launching the GUIs::

    $ python3 -m visiannot -c path/to/config.ini -u visiannot.configuration.configUpdateExamples.updateDataAndAnnotationDirectory

The option ``-c`` specifies the path to the configuration file to load. Then, with the option ``-u``, we give the path to a function in **visiannot** package that updates the loaded configuration dictionary.