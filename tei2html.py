# !/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-
import glob
import argparse
import os
import zipfile
from bs4 import BeautifulSoup
from pathlib import Path
from multiprocessing import Pool

from tei_to_html_utils import file_gen_from_zip, create_new_tag_with_string

HTML = '<html><head itemscope itemtype="http://schema.org/NewsArticle"></head></html>'


HI_DICT = {
    'bold': 'b',
    'italic': 'i',
    'underline': 'u',
    'strikeout': 'strike',
    'superscript': 'sup',
    'subscript': 'sub'
        }

FREE = {
    'cell': 'td',
    'row': 'tr',
    'ref': 'a',
    'facs': 'a',
    'list': 'ul',
    'item': 'li',
    'floatingText': 'div',
    'div': 'div',
    'table': 'table',
    'figure': 'figure',
    'p': 'p',
    'quote': 'blockquote'
}

FREE_ATTRS = {
    'target': 'href',
    'facs': 'a',
    'type': 'class',
    'rend': 'class'}
    # tag.attrs['resp'] = 'script'



# <head itemscope itemtype="http://schema.org/Article">
#   <meta itemprop="name" content="The Name or Title Here">
#   <meta itemprop="description" content="This is the page description">
#   <link itemprop="image" href="http://www.example.com/image.jpg">
# </head>


def fill_meta_block(input_bs, out_html):
    xenodata = input_bs.find('xenoData').find('rdf:Description')
    head = out_html.head
    for x in xenodata.find_all():
        schema_org_meta = out_html.new_tag('meta', attrs={'itemprop': x.name, 'content': x.text.strip()})
        head.append(schema_org_meta)


def change_body_tags(html_body):
    for tag in html_body.find_all():
        if tag.name == 'hi':
            tag.name = HI_DICT.get(tag.attrs['rend'], 'em')
            tag.attrs = {}
        elif tag.name == 'p' and tag.attrs.get('rend', None) == 'head':
            tag.name = 'h3'
            tag.attrs = {}
        elif tag.name == 'head' and tag.attrs.get('type', None) is not None:
            rend = tag.attrs.get('type')
            if rend == 'title':
                tag.name = 'h1'
                tag.attrs = {}
            elif rend == 'subtitle':
                tag.name = 'h2'
                tag.attrs = {}
        else:
            tag_name = tag.name
            tag_attrs = tag.attrs
            isname = FREE.get(tag_name)
            if isname is not None:
                tag.name = isname
            else:
                print('WHAT?', tag_name)
            if tag_attrs != {}:
                new_attrs = {}
                for k, v in tag_attrs.items():
                    if k in FREE_ATTRS:
                        new_attrs[FREE_ATTRS[k]] = v
                    else:
                        print('WHAT?', k, v)
                        new_attrs[k] = v
                tag.attrs = new_attrs



def process_and_print_one_article(xml_file):
    bs_xml = BeautifulSoup(xml_file, features='xml')
    # bs_html = BeautifulSoup(str(bs_xml.body), features='html.parser')
    bs_html = BeautifulSoup(HTML, features='html.parser')
    bs_html.head.insert_after(bs_xml.body)
    fill_meta_block(bs_xml, bs_html)
    change_body_tags(bs_html.body)
    #print(bs_html)
    return bs_html
    # TODO: os.makedirs(os.path.dirname(new_fold_file), exist_ok=True)


def process_portal_zip_to_htmls(archive_path_fold, out_folder, selected, suf='_2022'):
    out_folder_path = Path(out_folder)
    for archive in glob.iglob(f'{archive_path_fold}/*.zip'):
        zipname = archive[archive.rfind('/') + 1:]
        if zipname in selected or selected == 'all':
            portal_name = zipname[:zipname.find('.')]
            # sketchfile_name = f'{sketchfile_folder}/{portal_name}_{suf}.xml'
            for z_obj, filepath in file_gen_from_zip(archive):
                with z_obj.open(filepath) as text_f:
                    uuid = filepath[filepath.find('/') + 1:filepath.find('.')]
                    filename_uuid = f'{uuid}.html'
                    article_as_html = process_and_print_one_article(text_f)
                    html_filename = out_folder_path / portal_name / filename_uuid
                    html_filename.parent.mkdir(parents=True, exist_ok=True)  # Create output dirs on the fly
                    with open(html_filename, 'w', encoding='UTF-8') as output_html:
                        print(article_as_html.prettify(), file=output_html)
                        # pretty_xml = prettify_beta(str(article_as_html))
                        # print(pretty_xml, file=output_html)


if __name__ == '__main__':
    """    parser = argparse.ArgumentParser()  # Add an argument
    parser.add_argument('--inp_zip_dir', type=str, required=True)
    parser.add_argument('--out_xml_dir', type=str, required=True)
    parser.add_argument('--selected_zips', type=str, required=False, default='all')
    args = parser.parse_args()
    process_portal_zip_to_htmls(args.inp_zip_dir, args.out_xml_dir, args.selected_zips)"""
    inp_zip_dir = '/media/eltedh/6EAB565C0EA732DB/TEI_zips'
    out_xml_dir = 'HTMLs'
    selected_zips = ['mosthallottam.zip']
    process_portal_zip_to_htmls(inp_zip_dir, out_xml_dir, selected_zips)

    # archive_path = '/media/eltedh/6EAB565C0EA732DB/TEI_zips'
    # archive_path = '/home/sarkozizsofia/TEI_zips'
    selected_archives = [
        # 'magyaridok.zip',
        # 'valasz.zip',
        # 'vs.zip',
        'mosthallottam.zip',
        # 'epiteszforum.zip',
        # 'maszol.zip',
        # 'utazomajom.zip',
        # 'hataratkelo.zip',
        # 'nnk.zip',
        # 'p888.zip',
        # 'telex.zip'
        # 'szekelyhon.zip',
        # 'transindex.zip'
        # 'abcug.zip',
        ##'budapestbeacon.zip'
        # 'termvil.zip'
    ]
