# !/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-
import glob
from bs4 import BeautifulSoup
from pathlib import Path

from tei_to_html_utils import file_gen_from_zip

HTML = '<html><head itemscope itemtype="http://schema.org/NewsArticle"><style></style></script></head></html> '

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

META_KEYS = {'sch:datePublished': 'Közzététel dátuma:', 'sch:dateModified': 'Módosítás dátuma:',
             'sch:author': 'Szerző:', 'sch:source': 'Forrás:', 'sch:articleSection': 'Rovat:',
             'sch:keywords': 'Kulcsszavak:', 'sch:url': 'URL:'}


def get_article_data(bsxml):
    meta_d = {}
    for m_key in META_KEYS.keys():
        meta_val_list = [meta_val.text.strip() for meta_val in bsxml.find_all(m_key)]
        if len(meta_val_list) > 0:
            if m_key == 'sch:datePublished':
                meta_d[META_KEYS[m_key]] = meta_val_list[0].replace('T', ' ')
            else:
                meta_d[META_KEYS[m_key]] = ', '.join(meta_val_list)
    if bsxml.find('div', {'type': 'page'}) is not None:
        urls = [u.attrs['source'] for u in bsxml.find_all('div', {'type': 'page'})]
        meta_d['URL:'] = urls
    return meta_d


def fill_meta_block(input_bs, out_html):
    xenodata = input_bs.find('xenoData').find('rdf:Description')
    head = out_html.head
    meta_for_human = out_html.new_tag('div', attrs={'class': 'meta'})
    meta_dict = get_article_data(input_bs)
    for mkey, mval in meta_dict.items():
        a_meta = out_html.new_tag('p')
        if mkey == 'URL:':
            if not isinstance(mval, list):
                mval = [mval]
            a_meta.append('URL:')
            for url in mval:
                one_page_href = out_html.new_tag('a', attrs={'href': url})
                one_page_href.string = url
                a_meta.extend([out_html.new_tag('br'), one_page_href])
        else:
            a_meta.string = f'{mkey} {mval}'
        meta_for_human.append(a_meta)
    for x in xenodata.find_all():
        schema_org_meta = out_html.new_tag('meta', attrs={'itemprop': x.name, 'content': x.text.strip()})
        head.append(schema_org_meta)
    return meta_for_human


def validate_html(html_obj):
    for fig in html_obj.find_all('figure'):
        if 'src' in fig.attrs.keys():
            # embedded_content
            button = html_obj.new_tag('button', {'style': 'font-size:40px'})
            new_img = html_obj.new_tag('a', attrs={'href': fig['src']})
            new_img.string = fig['src']
            button.string = 'A linken található erőforrás nem része az archívumnak, ezért nem kerül megjelenítésre.'
            button.append(new_img)
            if fig.find() is not None:
                fig.find().insert_before(button)
            else:
                fig.append(button)
            del fig['src']
    for page in html_obj.find_all('div', {'class': 'page'}):
        page.attrs['data-href'] = page.attrs['source']
        del page.attrs['source']

# <figure class="media_content" resp="script" type="corrected">
# <figure class="media_content" src="https://www.mosthallottam.hu/wp-content/uploads/2020/11/ev-rovara-2021.jpg">


def change_body_tags(bs_html):
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
            isname = FREE.get(tag_name)
            if isname is not None:
                tag.name = isname
            if tag_attrs != {}:
                # <figure facs="https://ad.adverticum.net/t/?z=6653496&amp;g=6653497&amp;b=665349900&amp;h
                # =%5BLOCATION%5D&amp;p=2" rend="embedded_content" resp="script" type="corrected">
                new_attrs = {}
                for k, v in tag_attrs.items():
                    if k in FREE_ATTRS:
                        new_attrs[FREE_ATTRS[k]] = v
                    else:
                        new_attrs[k] = v
                tag.attrs = new_attrs
            if tag.name == 'div':
                if 'type' in tag.attrs.keys():
                    tag.attrs['class'] = tag.attrs['type']
                    del tag.attrs['type']
    for tag in html_body.find_all('to_unwrap'):
        tag.unwrap()
    validate_html(bs_html)


def tei_to_html(xml_file, u):
    bs_xml = BeautifulSoup(xml_file, features='xml')
    bs_html = BeautifulSoup(HTML, features='html.parser')
    css = open('tei2html.css', 'r')
    bs_html.style.string = css.read()
    meta_for_human_block = fill_meta_block(bs_xml, bs_html)
    bs_html.head.insert_after(bs_xml.body)
    change_body_tags(bs_html)
    bs_html.h1.insert_after(meta_for_human_block)
    return bs_html


def process_portal_zip_to_htmls(archive_path_fold, out_folder, selected):
    print(archive_path_fold)
    out_folder_path = Path(out_folder)
    for archive in glob.iglob(f'{archive_path_fold}/*.zip'):
        zipname = archive[archive.rfind('/') + 1:]
        if zipname in selected or selected == 'all':
            portal_name = zipname[:zipname.find('.')]
            for z_obj, filepath in file_gen_from_zip(archive):
                with z_obj.open(filepath) as text_f:
                    uuid = filepath[filepath.find('/') + 1:filepath.find('.')]
                    filename_uuid = f'{uuid}.html'
                    article_as_html = tei_to_html(text_f, uuid)
                    html_filename = out_folder_path / portal_name / filename_uuid
                    html_filename.parent.mkdir(parents=True, exist_ok=True)
                    with open(html_filename, 'w', encoding='UTF-8') as output_html:
                        print(article_as_html.prettify(), file=output_html)


if __name__ == '__main__':
    """    parser = argparse.ArgumentParser()  # Add an argument
    parser.add_argument('--inp_zip_dir', type=str, required=True)
    parser.add_argument('--out_xml_dir', type=str, required=True)
    parser.add_argument('--selected_zips', type=str, required=False, default='all')
    args = parser.parse_args()
    process_portal_zip_to_htmls(args.inp_zip_dir, args.out_xml_dir, args.selected_zips)"""
    # inp_zip_dir = '/home/dh/PycharmProjects/TEI2HTML'#
    inp_zip_dir = '/media/eltedh/6EAB565C0EA732DB/TEI_zips'
    out_xml_dir = 'HTMLs'
    selected_zips = ['abcug.zip']#'p444_pagetest.zip'] # # # 'mosthallottam.zip'] #
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
