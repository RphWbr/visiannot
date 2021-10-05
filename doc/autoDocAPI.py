# -*- coding: utf-8 -*-

from inspect import getmembers, isclass, isfunction
from importlib import import_module
from sys import path, setrecursionlimit
from os import mkdir
from os.path import isdir, abspath
from shutil import rmtree


# global variable
INDEX_ROOT_NAME = "APIreference"
INDEX_ROOT_TITLE = "API Reference"


def writeSection(index_path, title, level=0, file_option='a'):
    title_length = len(title)

    if level == 0 or level == 1:
        section_line = '=' * title_length

    elif level == 2:
        section_line = '-' * title_length

    elif level == 3:
        section_line = '^' * title_length

    with open(index_path, file_option) as f:
        if level == 0:
            f.write(section_line)
            f.write('\n')

        f.write(title)
        f.write('\n')
        f.write(section_line)
        f.write('\n\n')


def writeTocTreeDirective(index_path):
    with open(index_path, 'a') as f:
        f.write(".. toctree::\n   :titlesonly:\n\n")


def writeTocTreeIndex(index_path, index_link):
    with open(index_path, 'a') as f:
        f.write('   ' + index_link + '/index\n')


def writeAutosummaryDirective(index_path):
    with open(index_path, 'a') as f:
        f.write(".. autosummary::\n")


def writeAutoclasssummDirective(index_path, class_full_name):
    with open(index_path, 'a') as f:
        f.write(".. autoclasssumm:: %s\n\n" % class_full_name)


def writeAutoModuleDirective(index_path, module_full_name):
    with open(index_path, 'a') as f:
        f.write(".. automodule:: %s\n\n" % module_full_name)


def writeAutoMember(index_path, member_full_name):
    with open(index_path, 'a') as f:
        f.write("   %s\n" % member_full_name)


def writeAutofunctionDirective(index_path, func_full_name):
    with open(index_path, 'a') as f:
        f.write(".. autofunction:: %s\n" % func_full_name)


def writeAutoclassDirective(index_path, class_full_name):
    with open(index_path, 'a') as f:
        f.write(".. autoclass:: %s\n" % class_full_name)
        f.write("   :members:\n")
        f.write("   :undoc-members:\n")
        f.write("   :show-inheritance:\n")
        f.write("   :private-members:\n\n")


def writeModuleSummary(
    index_path, package_full_name, member_list, title
):
    # check if any member to summarize
    if len(member_list) > 0:
        # write sub-title for functions
        writeSection(index_path, title, level=2)

        # write autosummary directive
        writeAutosummaryDirective(index_path)

        # loop on members
        for member_name in member_list:
            # add member to summary
            writeAutoMember(
                index_path, "%s.%s" % (package_full_name, member_name)
            )

        # write empty line in index file
        with open(index_path, 'a') as f:
            f.write('\n')


def writeAPIClasses(index_path, module_full_name, class_list):
    # loop on classes
    for class_name in class_list:
        # get full path to class
        class_full_name = "%s.%s" % (module_full_name, class_name)

        # write sub-title for class
        writeSection(index_path, "Class %s" % class_name, level=2)

        # write directive for autoclasssumm
        writeAutoclasssummDirective(index_path, class_full_name)

        # write directive for autoclass
        writeAutoclassDirective(index_path, class_full_name)


def writeAPIFunctions(index_path, module_full_name, func_list):
    # check if any function to document
    if len(func_list) > 0:
        # write sub-title for functions
        writeSection(index_path, "Functions", level=2)

        # loop on functions
        for func_name in func_list:
            # write directive for autofunction
            writeAutofunctionDirective(
                index_path, "%s.%s" % (module_full_name, func_name)
            )


def writeModuleIndex(index_path, module, module_full_name):
    # get list of classes in the module
    class_list = getMembersDefinedInModule(module, isclass)

    # get list of functions in the module
    func_list = getMembersDefinedInModule(module, isfunction)

    # write automodule directive
    writeAutoModuleDirective(index_path, module_full_name)

    # write title of summary section
    writeSection(index_path, "Summary", level=1)

    # write summary of classes
    writeModuleSummary(
        index_path, module_full_name, class_list, "Classes"
    )

    # write summary of functions
    writeModuleSummary(
        index_path, module_full_name, func_list, "Functions"
    )

    # write title of API section
    writeSection(index_path, "API", level=1)

    # write documentation of classes
    writeAPIClasses(index_path, module_full_name, class_list)

    # write documentation for functions
    writeAPIFunctions(index_path, module_full_name, func_list)


def writePackageIndex(
    index_path, package, package_full_name, doc_dir
):
    # write directive for toc tree
    writeTocTreeDirective(index_path)

    # loop on sub-packages
    for sub_package_name in package.__all__:
        # write a link to sub-package index in the toc tree
        writeTocTreeIndex(index_path, sub_package_name)

        # recursive call
        generateIndexFilesRecursive(
            ".%s" % sub_package_name, package_full_name, doc_dir,
        )


def getMembersDefinedInModule(module, condition_function):
    # get list of members in the module
    member_list = getmembers(module, condition_function)

    # remove functions that are not defined in the current module
    member_list = [
        member[0] for member in member_list
        if hasattr(member[1], "__module__")
        and member[1].__module__ == module.__name__
    ]

    return member_list


def generateIndexFilesRecursive(
    package_name, package_root_name, doc_dir
):
    # import package
    package = import_module(package_name, package_root_name)

    # check if not at the package root
    if package_root_name is not None:
        # create documentation folder
        doc_dir = "%s/%s" % (doc_dir, package_name.replace('.', ''))
        if not isdir(doc_dir):
            mkdir(doc_dir)

    # get package full name
    if package_root_name is not None:
        package_full_name = package_root_name + package_name
    else:
        package_full_name = package_name

    # create index file
    index_path = "%s/index.rst" % doc_dir
    writeSection(index_path, package_full_name, file_option='w')

    # check if package indeed
    if hasattr(package, "__all__"):
        writePackageIndex(
            index_path, package, package_full_name, doc_dir
        )

    # module instead
    else:
        writeModuleIndex(index_path, package, package_full_name)


def generateIndexFiles(
    package_name, package_dir, doc_dir='source', text_top='', text_bottom='',
    flag_ignore_main=True
):
    path.insert(0, abspath(package_dir))
    setrecursionlimit(1500)

    # check if main index file must be appended
    appendMainIndexFile("%s/index.rst" % doc_dir)

    # get directory containing the index files
    doc_dir = "%s/%s" % (doc_dir, INDEX_ROOT_NAME)

    # delete directory if necessary
    if isdir(doc_dir):
        rmtree(doc_dir)

    # create directory
    mkdir(doc_dir)

    # create index file
    index_path = "%s/index.rst" % doc_dir
    writeSection(index_path, INDEX_ROOT_TITLE, file_option='w')

    # write top text
    if len(text_top) > 0:
        with open(index_path, 'a') as f:
            f.write(text_top)
            f.write('\n')

    # import package
    package = import_module(package_name)

    # write directive for toc tree
    writeTocTreeDirective(index_path)

    # loop on modules and sub-packages
    for sub_package_name in package.__all__:
        if flag_ignore_main and sub_package_name == "__main__":
            pass

        else:
            # write a link to sub-package index in the toc tree
            writeTocTreeIndex(index_path, sub_package_name)

            # create index files for sub-package
            generateIndexFilesRecursive(
                ".%s" % sub_package_name, package_name, doc_dir
            )

    # write bottom text
    if len(text_bottom) > 0:
        with open(index_path, 'a') as f:
            f.write(text_bottom)
            f.write('\n')


def appendMainIndexFile(index_path):
    with open(index_path, 'r') as f:
        content_list = f.readlines()
        if "   %s/index\n" % INDEX_ROOT_NAME not in content_list:
            start_ind = content_list.index(".. toctree::\n") + 1
            for i, content in enumerate(content_list[start_ind:]):
                if len(content) > 3 and content[:3] != '   ' or \
                        len(content) < 3:
                    break

            end_ind = start_ind + i
            if end_ind == len(content_list) - 1:
                if content_list[-1][-1:] != '\n':
                    content_list[-1] += '\n'
                end_ind += 1

            content_list.insert(end_ind, "   %s/index\n" % INDEX_ROOT_NAME)

    with open(index_path, 'w') as f:
        f.writelines(content_list)


if __name__ == "__main__":
    """
    in order to automatically generate APIreference index files,
    this script must be launched before generating documentation
    """

    text_top = "The package **visiannot** is made up of three sub-packages:\n"

    text_bottom = """
The sub-package **configuration** contains modules where are defined the
classes for the creation of the configuration GUI.

The sub-package **tools** contains modules with functions that may be used
outside of **ViSiAnnoT**. In particular, the modules **ToolsPyQt** and
**ToolsPyqtgraph** are an overlayer of **PyQt5** and **pyqtgraph**
respectively. They may be used in order to ease the creation of a GUI and
scientific graphics respectively. See chapters :ref:`toolspyqt` and
:ref:`toolspyqtgraph`.

The sub-package **visiannot** contains modules where are defined the classes
for the creation of the ViSiAnnoT GUI.

The summary of the modules can be found at the top of their respective page."""

    generateIndexFiles(
        "visiannot", "..", text_top=text_top, text_bottom=text_bottom
    )
