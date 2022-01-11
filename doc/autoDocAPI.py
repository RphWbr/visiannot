# -*- coding: utf-8 -*-

"""
Script for automatic generation of API reference indexes, it must be launched
before generating Sphinx documentation

:author: Raphaël Weber
"""

from inspect import getmembers, isclass, isfunction, ismodule
from importlib import import_module
from sys import path, setrecursionlimit
from os import mkdir
from os.path import isdir, abspath
from shutil import rmtree


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


def writeAutoModuleDirective(index_path, module_full_name):
    with open(index_path, 'a') as f:
        f.write(".. automodule:: %s\n\n" % module_full_name)


def writeAutoMember(index_path, member_full_name):
    with open(index_path, 'a') as f:
        f.write("   %s\n" % member_full_name)


def writeAutofunctionDirective(index_path, module_full_name, func_list):
    with open(index_path, 'a') as f:
        for func_name in func_list:
            f.write(
                ".. autofunction:: %s.%s\n" % (module_full_name, func_name)
            )

        f.write("\n")


def writeAutodataDirective(index_path, module_full_name, data_list):
    with open(index_path, 'a') as f:
        for data_name in data_list:
            f.write(".. autodata:: %s.%s\n" % (module_full_name, data_name))

        f.write("\n")


def writeAutoclassDirective(index_path, class_full_name):
    with open(index_path, 'a') as f:
        f.write(".. autoclass:: %s\n" % class_full_name)
        f.write("   :members:\n")
        f.write("   :undoc-members:\n")
        f.write("   :show-inheritance:\n")
        f.write("   :private-members:\n")
        f.write("\n")


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


def writeAPIData(index_path, module_full_name, data_list):
    # check if any data to document
    if len(data_list) > 0:
        # write sub-title for data
        writeSection(index_path, "Data", level=2)

        # write directive for autodata
        writeAutodataDirective(
            index_path, module_full_name, data_list
        )


def writeAPIClasses(index_path, module_full_name, class_list):
    # loop on classes
    for class_name in class_list:
        # get full path to class
        class_full_name = "%s.%s" % (module_full_name, class_name)

        # write sub-title for class
        writeSection(index_path, "Class %s" % class_name, level=2)

        # write directive for autoclass
        writeAutoclassDirective(index_path, class_full_name)


def writeAPIFunctions(index_path, module_full_name, func_list):
    # check if any function to document
    if len(func_list) > 0:
        # write sub-title for functions
        writeSection(index_path, "Functions", level=2)

        # write directive for autofunction
        writeAutofunctionDirective(
            index_path, module_full_name, func_list
        )


def writeModuleIndex(index_path, module, module_full_name):
    # get list of global variables in the module
    data_list = getMembersDefinedInModule(module, '')

    # get list of classes in the module
    class_list = getMembersDefinedInModule(module, isclass)

    # get list of functions in the module
    func_list = getMembersDefinedInModule(module, isfunction)

    # write title of summary section
    writeSection(index_path, "Summary", level=1)

    # write automodule directive
    writeAutoModuleDirective(index_path, module_full_name)

    # write summary of global variables
    writeModuleSummary(
        index_path, module_full_name, data_list, "Data"
    )

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

    # write documentation for functions
    writeAPIData(index_path, module_full_name, data_list)

    # write documentation of classes
    writeAPIClasses(index_path, module_full_name, class_list)

    # write documentation for functions
    writeAPIFunctions(index_path, module_full_name, func_list)


def writePackageIndex(
    index_path, package, package_full_name, out_dir
):
    # write directive for toc tree
    writeTocTreeDirective(index_path)

    # loop on sub-packages
    for sub_package_name in package.__all__:
        # write a link to sub-package index in the toc tree
        writeTocTreeIndex(index_path, sub_package_name)

        # recursive call
        generateIndexFilesRecursive(
            ".%s" % sub_package_name, package_full_name, out_dir
        )


def getMembersDefinedInModule(module, condition_function):
    """
    condition_function may be any 'isXXX' function of the module inspect,
    ``None`` (get everything) or '' (get global variables)
    """

    if isinstance(condition_function, str):
        # get list of all members in the module that are not part of a module
        # and remove modules (=> so that we only keep global variables)
        # and remove standard global variables
        member_list = [
            member[0] for member in getmembers(module)
            if not hasattr(member[1], "__module__") and not ismodule(member[1])
            and member[0] not in [
                "__builtins__", "__cached__", "__doc__", "__file__",
                "__name__", "__package__"
            ]
        ]

    else:
        # get list of members with respect to condition function
        # and remove functions that are not defined in the current module
        member_list = [
            member[0] for member in getmembers(module, condition_function)
            if hasattr(member[1], "__module__")
            and member[1].__module__ == module.__name__
        ]

    return member_list


def generateIndexFilesRecursive(
    package_name, package_root_name, out_dir
):
    # import package
    package = import_module(package_name, package_root_name)

    # check if not at the package root
    if package_root_name is not None:
        # create index directory
        out_dir = "%s/%s" % (out_dir, package_name.replace('.', ''))
        if not isdir(out_dir):
            mkdir(out_dir)

    # get package full name
    if package_root_name is not None:
        package_full_name = package_root_name + package_name
    else:
        package_full_name = package_name

    # create index file
    index_path = "%s/index.rst" % out_dir
    writeSection(index_path, package_full_name, file_option='w')

    # check if package indeed
    if hasattr(package, "__all__"):
        writePackageIndex(
            index_path, package, package_full_name, out_dir
        )

    # module instead
    else:
        writeModuleIndex(index_path, package, package_full_name)


def generateIndexFiles(
    package_name, doc_dir, package_dir=None, output_name="APIreference",
    chapter_title="API reference", flag_include_main=False
):
    if package_dir is not None:
        path.insert(0, abspath(package_dir))

    setrecursionlimit(1500)

    # append API reference to toctree directive in main index file of the
    # documentation
    appendMainIndexFile("%s/index.rst" % doc_dir, output_name)

    # get output directory where to store the index files
    out_dir = "%s/%s" % (doc_dir, output_name)

    # delete directory if necessary
    if isdir(out_dir):
        rmtree(out_dir)

    # create directory
    mkdir(out_dir)

    # create index file
    index_path = "%s/index.rst" % out_dir
    writeSection(index_path, chapter_title, file_option='w')

    # import package
    package = import_module(package_name)

    # write directive for toc tree
    writeTocTreeDirective(index_path)

    # loop on modules and sub-packages
    for sub_package_name in package.__all__:
        if not flag_include_main and sub_package_name == "__main__":
            pass

        else:
            # write a link to sub-package index in the toc tree
            writeTocTreeIndex(index_path, sub_package_name)

            # create index files for sub-package
            generateIndexFilesRecursive(
                ".%s" % sub_package_name, package_name, out_dir
            )


def appendMainIndexFile(main_index_path, api_ref_name):
    with open(main_index_path, 'r') as f:
        content_list = f.readlines()
        if "   %s/index\n" % api_ref_name not in content_list:
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

            content_list.insert(end_ind, "   %s/index\n" % api_ref_name)

    with open(main_index_path, 'w') as f:
        f.writelines(content_list)


if __name__ == "__main__":
    generateIndexFiles("visiannot", "source")
