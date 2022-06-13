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


HTML = '<html><head itemscope itemtype="http://schema.org/NewsArticle"><style></style></script></head></html> '
# <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous">
# TODO CSS: note > hide
# https://www.w3schools.com/icons/tryit.asp?filename=trybs_ref_glyph_camera
# <div class="meta">
# <i style='font-size:24px' class='fas'>&#xf083;</i> https://www.w3schools.com/icons/icons_reference.asp

# .social-sharing-icons li.pinterest-share:before{
# 	content: '\f16d';
# }
# border-image-source: url(/media/diamonds.png);


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
    'quote': 'blockquote',
    'body': 'to_unwrap'
}

TAG_TO_UNWRAP = {'body'}

FREE_ATTRS = {
    'target': 'href',
    'facs': 'src',
    'type': 'type',
    'rend': 'class'}
    # tag.attrs['resp'] = 'script'


# <head itemscope itemtype="http://schema.org/Article">
#   <meta itemprop="name" content="The Name or Title Here">
#   <meta itemprop="description" content="This is the page description">
#   <link itemprop="image" href="http://www.example.com/image.jpg">
# </head>

META_KEYS = {'sch:datePublished': 'Közzététel dátuma:', 'sch:dateModified': 'Módosítás dátuma:',
             'sch:author': 'Szerzők:', 'sch:source': 'Forrás:', 'sch:articleSection': 'Rovat:',
             'sch:keywords': 'Kulcsszavak:', 'sch:url': 'URL:'}  # TODO: ezt kaphatná a main fv


def get_article_data(bs_xml):
    meta_d = {}
    for m_key in META_KEYS.keys():  # {'sch:articleSection', 'sch:keywords'}
        meta_val_list = [meta_val.text.strip() for meta_val in bs_xml.find_all(m_key)]
        if len(meta_val_list) > 0:
            if m_key == 'sch:datePublished':
                meta_d[META_KEYS[m_key]] = meta_val_list[0].replace('T', ' ')
            else:
                meta_d[META_KEYS[m_key]] = ', '.join(meta_val_list)
    return meta_d


def fill_meta_block(input_bs, out_html):
    xenodata = input_bs.find('xenoData').find('rdf:Description')
    head = out_html.head
    meta_for_human = out_html.new_tag('div', attrs={'class': 'meta'})
    # print(meta_for_human)
    meta_dict = get_article_data(input_bs)
    for mkey, mval in meta_dict.items():
        a_meta = out_html.new_tag('p')  # a_meta = out_html.new_tag('b')
        a_meta.string = f'{mkey} {mval}'
        meta_for_human.append(a_meta)
    """for m in meta_for_human.find_all():
        m.wrap(out_html.new_tag('p'))"""
    for x in xenodata.find_all():
        schema_org_meta = out_html.new_tag('meta', attrs={'itemprop': x.name, 'content': x.text.strip()})
        head.append(schema_org_meta)
    return meta_for_human


def validate_html(html_obj, url):
    #  <figure class="media_content" src="https://www.mosthallottam.hu/wp-content/uploads/2020/11/ev-rovara-2021.jpg">
    for fig in html_obj.find_all('figure'):
        # meta_for_human = out_html.new_tag('div', attrs={'class': 'meta'})
        if 'src' in fig.attrs.keys():
            # embedded_content
            """if fig.attrs['class'] == 'embedded_content':
                fig.name = 'iframe'"""
                #new_img = html_obj.new_tag('iframe', attrs={'src': fig['src']})
                #else:
            button = html_obj.new_tag('button', {'style': 'font-size:40px'})
            #button.string = '&#187;'
            #new_img = html_obj.new_tag('img', attrs={'src': fig['src']})#, 'target': '_blank'})
            new_img = html_obj.new_tag('a', attrs={'href': fig['src']})  # , 'target': '_blank'})
            #new_img = html_obj.new_tag('img')
            #<button style='font-size:24px'>Button <i class='fab fa-500px'></i></button>
            # <i class='fas fa-external-link-alt'></i>
            new_img.string = fig['src']
            #icon = html_obj.new_tag('a', attrs={'href': fig['src']}) #attrs={'class': 'fas fa-external-link-alt'})# <i class="fas fa-cat"></i>
            #new_img.append(icon)
            button.append(new_img)
            if fig.find() is not None:
                #fig.find().insert_before(new_img)
                fig.find().insert_before(button)
            else:
                # fig.append(new_img)
                fig.append(button)
            del fig['src']
    for p in html_obj.find_all('div', {'class': 'page'}):
        print(url)

    """if html_obj.find('div', {'class': 'frame'}) is not None: # and html_obj.find(True, {'class': 'embedded_content'}) is not None:
        print('>>>FRAME', url)
    if html_obj.find(True, {'class': 'embedded_content'}) is not None:
        print('>>>EMBED', url)
    if html_obj.find(True, {'class': 'lead'}) is not None:
        print('>>>LEAD', url)"""
            # print(url, fig)
# <figure rend="media_content">
# <figure rend="diagram">
# <figure rend="embedded_content">
# <floatingText type="social_media_content">
# <figure rend="embedded_social_media_content"
# <div type="page" "source"=#URL>


def change_body_tags(bs_html, f_uuid):
    html_body = bs_html.body
    for tag in html_body.find_all():
        if tag.name == 'hi':
            if 'rend' in tag.attrs.keys():
                tag.name = HI_DICT[tag.attrs['rend']]
            else:
                tag.name = 'em'
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
            if tag_name == 'div' and 'type' in tag_attrs.keys() and tag_attrs['type'] == 'feed':
                print('>>>FEED', f_uuid)
            isname = FREE.get(tag_name)
            if isname is not None:
                tag.name = isname
            if tag_attrs != {}:
                # <figure facs="https://ad.adverticum.net/t/?z=6653496&amp;g=6653497&amp;b=665349900&amp;h=%5BLOCATION%5D&amp;p=2" rend="embedded_content" resp="script" type="corrected">
                new_attrs = {}
                for k, v in tag_attrs.items():
                    if k in FREE_ATTRS:
                        new_attrs[FREE_ATTRS[k]] = v
                    else:
                        #print('WHAT?', k, v, tag)
                        new_attrs[k] = v
                tag.attrs = new_attrs
            if tag.name == 'div':
                if 'type' in tag.attrs.keys():
                    tag.attrs['class'] = tag.attrs['type']
                    del tag.attrs['type']
                    # <floatingText type='frame'>
                    # <floatingText type='lead'>

    for tag in html_body.find_all('to_unwrap'):
        tag.unwrap()
    validate_html(bs_html, f_uuid)


def process_and_print_one_article(xml_file, uu):
    bs_xml = BeautifulSoup(xml_file, features='xml')
    # bs_html = BeautifulSoup(str(bs_xml.body), features='html.parser')
    bs_html = BeautifulSoup(HTML, features='html.parser')
    css = open('tei2html.css', 'r')
    bs_html.style.string = css.read()
    bs_html.head.insert_after(bs_xml.body)
    meta_for_human_block = fill_meta_block(bs_xml, bs_html)
    change_body_tags(bs_html, uu)
    bs_html.h1.insert_after(meta_for_human_block)
    #print(bs_html)
    return bs_html


def process_portal_zip_to_htmls(archive_path_fold, out_folder, selected, suf='_2022'):
    print(archive_path_fold)
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
                    article_as_html = process_and_print_one_article(text_f, uuid)
                    html_filename = out_folder_path / portal_name / filename_uuid
                    html_filename.parent.mkdir(parents=True, exist_ok=True)  # Create output dirs on the fly
                    with open(html_filename, 'w', encoding='UTF-8') as output_html:
                        print(article_as_html.prettify(), file=output_html)
                        # pretty_xml = prettify_beta(str(article_as_html))
                        # print(pretty_xml, file=output_html)

# TODO: INFOGRAM: file:///home/eltedh/PycharmProjects/TEI2HTML/HTMLs/abcug/263ae88e-93e9-566f-ac11-df581b46af4b.html


if __name__ == '__main__':
    """    parser = argparse.ArgumentParser()  # Add an argument
    parser.add_argument('--inp_zip_dir', type=str, required=True)
    parser.add_argument('--out_xml_dir', type=str, required=True)
    parser.add_argument('--selected_zips', type=str, required=False, default='all')
    args = parser.parse_args()
    process_portal_zip_to_htmls(args.inp_zip_dir, args.out_xml_dir, args.selected_zips)"""
    #inp_zip_dir = '/home/dh/PycharmProjects/TEI2HTML'#
    inp_zip_dir = '/media/eltedh/6EAB565C0EA732DB/TEI_zips'
    out_xml_dir = 'HTMLs'
    selected_zips = ['telex.zip']  # 'mosthallottam.zip'] #
    #selected_zips = ['tei2html_test.zip']  # 'telex.zip']
    process_portal_zip_to_htmls(inp_zip_dir, out_xml_dir, selected_zips)

    # archive_path = '/media/eltedh/6EAB565C0EA732DB/TEI_zips'
    # archive_path = '/home/sarkozizsofia/TEI_zips'
    selected_archives = [
        # 'magyaridok.zip',
        # 'valasz.zip',
        # 'vs.zip',
        'vadhajtasok.zip'
        # 'mosthallottam.zip',
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
