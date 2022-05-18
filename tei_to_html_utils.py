# !/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-
import os
import zipfile
from os.path import basename, join as os_path_join
from io import StringIO
from xml.etree import ElementTree
from xml.dom import minidom


def prettify_beta(xml_string):
    f = StringIO(xml_string)  # io.StringIO volt
    tree = ElementTree.parse(f)
    root = tree.getroot()
    teixml_as_string = ElementTree.tostring(root, encoding="unicode")
    xmlstr = minidom.parseString(teixml_as_string).toprettyxml(newl='\n', encoding='utf-8')
    xmlstr = os.linesep.join(s for s in xmlstr.decode("utf-8").splitlines() if s.strip())
    return xmlstr


def file_gen_from_zip(zip_archive):
    with zipfile.ZipFile(zip_archive) as zipObj:
        for filename in sorted(zipObj.namelist()):
            if not os.path.isdir(filename):
                yield zipObj, filename


def zip_dir(path, ziph):
    # https://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory-in-python
    # Adapted from: http://www.devshed.com/c/a/Python/Python-UnZipped/
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os_path_join(root, file))


def zip_dirs(dirs, zip_name):
    zipf = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
    for portal_to_zip in dirs:
        # zip_from_folder = 'SAMPLE_ARCHIVE/'
        zip_dir(portal_to_zip, zipf)  # ('tmp/', zipf)
    zipf.close()


def create_new_tag_with_string(beauty_xml, tag_string, tag_name, tag_attrs, append_to=None):
    """Helper function to create a new XML tag containing string in it.
        If provided append the newly created tag to a parent tag
    """
    the_new_tag = beauty_xml.new_tag(tag_name)
    the_new_tag.attrs = tag_attrs
    the_new_tag.string = tag_string.strip()
    if append_to is not None:
        append_to.append(the_new_tag)  # BS.TAG.append() not list!
    else:
        return the_new_tag