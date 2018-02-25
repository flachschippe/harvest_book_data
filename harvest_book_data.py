#!/usr/bin/python3
# -*- coding: utf-8 -*-

from lxml import html
import json
import requests
import sys
import re
from bs4 import BeautifulSoup
from pygraphml import Graph
from pygraphml import GraphMLParser


def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

BASE_URL_DNB = 'https://portal.dnb.de'
QUERY = "luhmann"

QUERY_FORMAT_STRING = BASE_URL_DNB + '/opac.htm?query={0}&method=simpleSearch&cqlMode=true'
QUERY_FORMAT_STRING_2 = BASE_URL_DNB + '/opac.htm?method=showNextResultSite&cqlMode=true&currentResultId={0}%26any&currentPosition={1}'

def get_data_from_book_info_link (book_data, response, field_name):
    tree = html.fromstring(response.content)
    field_data = tree.xpath('//td/strong[text() = "{}"]/../../td/a/text()'.format(field_name))
    field_array = []
    for field in field_data:
        field_array.append(field.replace("\n","").replace("\r","").replace("\t","").replace("*", ""))

    book_data[field_name] = field_array


def get_data_from_book_info (book_data, response, field_name):
    tree = html.fromstring(response.content)
    field_data = tree.xpath('//td/strong[text() = "{}"]/../../td/text()'.format(field_name))
    field_string = ""
    for field in field_data:
        field_string = field_string + field.replace("\n","").replace("\r","").replace("\t","")

    book_data[field_name] = field_string

if __name__ == "__main__":
    book_data = {}
    currentPosition = 0;
    query_string = QUERY_FORMAT_STRING.format(QUERY);
    file_handles = {};
    graph = Graph();
    parser = GraphMLParser()
    filename = "book_data_" + QUERY + ".graphml"
    # map for collecting nodes
    nodes = {}
    while(True):
        page = requests.get(query_string)
        tree = html.fromstring(page.content)

        links = tree.xpath('//table[@id="searchresult"]//a/@href')

        if(len(links) == 0):
            break;

        for link in links:
            book_info_response = requests.get(BASE_URL_DNB + link)
            get_data_from_book_info(book_data, book_info_response, "Titel")
            get_data_from_book_info(book_data, book_info_response, "Person(en)")
            get_data_from_book_info_link(book_data, book_info_response, "Schlagwörter")

            if(len(book_data['Schlagwörter']) > 0):
                for v in book_data.values():             
                    print(v)

                for s in book_data['Schlagwörter']:
                    node = None
                    if s not in nodes:
                        node = graph.add_node (s)
                        nodes[s] = node
                    else:
                        node = nodes[s]

                s1 = book_data['Schlagwörter'][0]
                for s in book_data['Schlagwörter']:
                    if s != s1:
                        edge = graph.add_edge(nodes[s1], nodes[s])
                        edge['label'] = book_data['Titel']
                parser.write(graph, filename)


        query_string = QUERY_FORMAT_STRING_2.format(QUERY,str(currentPosition))
        currentPosition += len(links);
