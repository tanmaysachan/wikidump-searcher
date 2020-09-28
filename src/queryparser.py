import os
import Stemmer
import pickle

import settings
import bm25

class QueryParser:
    def __init__(self, index_path=""):
        self.path = index_path
        
        self.doccount = 0
        self.token_count = 0

        self.init_counts()

        self.ranker = bm25.BM25(index_path=self.path, doccount=self.doccount,
                                tokcount=self.token_count)

        self.stopwords = set()
        self.init_stopwords()

        self.stemmer = Stemmer.Stemmer('english')
        
    def init_counts(self):
        with open(os.path.join(self.path, settings.STATS_FILE), "r") as f:
            line = f.readline()
            while line:
                line = line.split('=')
                if line[0] == 'NUM_DOCS':
                    self.doccount = int(line[1].strip())

                if line[0] == 'TOKEN_COUNT':
                    self.token_count = int(line[1].strip())
                
                line = f.readline()

    def init_stopwords(self):
        try:
            with open('stopwords.pickle', 'rb') as f:
                self.stopwords = pickle.load(f)
        except:
            print('stopwords.pickle not found, no stopwords loaded...')


    def parse_query(self, query, num_results=10):
        # have query_type as none/fields/regular
        query_type = 'none'
        if len(query) > 1 and query[1] == ':' and query[0] in 'tlrbic':
            query_type = 'fields'
        
        elif (len(query) > 1 and query[1] != ':') or (len(query) <= 1):
            query_type = 'regular'

        print(query_type)
        if query_type == 'none':
            return ["invalid query"]

        elif query_type == 'regular':
            _query = set(query.lower().split(' '))
            _query = _query - self.stopwords
            _query = [self.stemmer.stemWord(term) for term in _query]

            self.ranker.process_terms(list(_query))
            return self.ranker.get_top_n(n=num_results)

        elif query_type == 'fields':
            _query = query.lower().split(' ')

            _query_terms = []
            for i in range(len(_query)):
                if _query[i][1] == ':':
                    cur_tag = _query[i][0]
                    if cur_tag not in 'tlrbic':
                        return ["invalid query"]
                    if _query[i][2:] not in self.stopwords:
                        _query_terms.append(_query[i])
                else:
                    _query[i] = cur_tag + ':' + _query[i]
                    if _query[i][2:] not in self.stopwords:
                        _query_terms.append(_query[i])
            self.ranker.process_terms(list(_query_terms))
            return self.ranker.get_top_n(n=num_results)
