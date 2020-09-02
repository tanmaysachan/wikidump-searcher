import invertedindex
import settings
from settings import tok_reg, infobox_reg, categories_reg, references_reg, external_reg, links_reg

import os
import re
import xml.sax.handler
import Stemmer

class Indexer(xml.sax.handler.ContentHandler):
    def __init__(self, data_path="", index_path=""):

        self.index = invertedindex.InvertedIndex(index_path)

        self.parser = xml.sax.make_parser()
        self.parser.setFeature(xml.sax.handler.feature_namespaces, 0)

        self.parser.setContentHandler(self)

        self.current_docid = 0
        self.current_content = ''
        self.current_title = ''

        self.path = data_path

        self.all_token_count = 0

        self.stopwords = set()
        # init_stopwords()

        self.stemmer = Stemmer.Stemmer('english')

        self.tok_reg = re.compile(tok_reg)
        self.infobox_reg = re.compile(infobox_reg)
        self.categories_reg = re.compile(categories_reg)
        self.references_reg = re.compile(references_reg)
        self.external_reg = re.compile(external_reg)
        self.links_reg = re.compile(links_reg)

        self.local_term_map = {}

    def startElement(self, name, attrs):
        self.active_tag = name

    def endElement(self, name):
        if name == 'page':
            self.index_content()

            self.current_docid += 1
            self.current_title = ''
            self.current_content = ''

    def characters(self, content):
        if self.active_tag == 'title':
            self.current_title += content.lower()
        else:
            self.current_content += content.lower()

    def parse_data(self):
        self.parser.parse(self.path)
        print('finished indexing...')
        self.cleanup()

        return (self.all_token_count, self.index.get_term_count())

    # clean text
    def clean(self, text, remove_stopwords=True, stem=True):

        text = set(text)

        if remove_stopwords:
            text = text - self.stopwords

        stemmed_text = []
        for tok in text:
            if stem:
                stemmed_text.append(self.stemmer.stemWord(tok))
            else:
                stemmed_text.append(tok)

        return stemmed_text

    def add_tag_to_terms(self, tokenized_text, tag, tokenize=True):
        for content in tokenized_text:
            if tokenize == False:
                _content = [content]
            else:
                _content = self.clean(set(tok for tok in self.tok_reg.split(content) if tok != ''))
            
            for tok in _content:
                try:
                    if tag not in self.local_term_map[tok]:
                        self.local_term_map[tok] += tag
                except:
                    self.local_term_map[tok] = '1,' + tag

    # Main class to index parsed content
    def index_content(self):
        self.local_term_map = {}

        
        content = self.clean(set(tok for tok in self.tok_reg.split(self.current_content)
                            if tok != ''))

        self.all_token_count += len(content)

        for tok in content:
            if tok not in self.local_term_map:
                self.local_term_map[tok] = 1
            else:
                self.local_term_map[tok] += 1

        for key in self.local_term_map:
            self.local_term_map[key] = str(self.local_term_map[key]) + ','

        title = self.clean(set(tok for tok in self.tok_reg.split(self.current_title) if tok != ''),
                           remove_stopwords=True,
                           stem=False) # Don't stem the title

        self.all_token_count += len(title)

        for tok in title:
            try:
                self.local_term_map[tok] = str(self.local_term_map[tok]) + 't'
            except:
                self.local_term_map[tok] = '1,t'

        # parse infobox
        infobox = self.infobox_reg.findall(self.current_content)

        # infoboxes can be recursive, so parse depth
        infobox_data = []
        for cont in infobox:
            dep = 1
            _cont = cont[0]
            for i in range(len(_cont)):
                if _cont[i] == '{' and _cont[i + 1] == '{':
                    i += 1
                    dep += 1
                if _cont[i] == '}' and _cont[i + 1] == '}':
                    i += 1
                    dep -= 1
                    if dep == 0:
                        infobox_data.append(_cont[:i - 1])
                        break

        self.add_tag_to_terms(infobox_data, 'i')

        # parse categories
        categories = self.categories_reg.findall(self.current_content)
        self.add_tag_to_terms(categories, 'c')

        # parse references
        references = self.references_reg.findall(self.current_content)
        self.add_tag_to_terms(references, 'r')

        # parse external links
        content = self.external_reg.split(self.current_content)
        links = []
        if len(content) > 1:
            content = content[1].split("\n")
            for l in content:
                if l and l[0] == "*":
                    _links = self.links_reg.findall(l)
                    for link in _links:
                        links.append(link)

        self.add_tag_to_terms(links, 'l', tokenize=False) # Don't tokenize links

        self.index.add_doc(self.current_docid, self.current_title.strip())
        for key in self.local_term_map:
            fields = self.local_term_map[key].split(',')
            self.index.add_term(key, self.current_docid, int(fields[0]), fields[1])
    
    def cleanup(self):
        self.index.cleanup()

if __name__ == '__main__':
    # for testing
    indexer = Indexer(data_path='/mnt/c/Users/Tanmay/Documents/IRE/wikidump.xml',
                      index_path='./inverted_index/')

    indexer.parse_data()
