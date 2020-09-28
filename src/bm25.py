import os
from math import log2
from datetime import datetime

import settings

class BM25:
    def __init__(self, index_path="", doccount=1, tokcount=0, k1=1.5, b=0.75):
        self.path = index_path

        self.doccount = doccount
        self.average_doc_length = tokcount/doccount

        # free parameters for BM-25
        self.k1 = k1
        self.b = b

        self.terms = {}
        self.terms_list = [] # easier for maintaining linear sort

        self.index_blocks_to_check = set()

        self.doc_blocks_to_check = set()
        self.relevant_docids = set()

        self.docid_to_title = {}
        self.docid_to_length = {}

        self.docid_to_score = {}

        self.term_to_tags = {}

        self.term_penalty = {}

    def get_block_path(self, block_number):
        return os.path.join(self.path, "index_" + str(block_number))

    def get_doc_block_path(self, doc_block_number):
        return os.path.join(self.path, "dblock_" + str(doc_block_number))

    def process_terms(self, terms):
        # clear out terms from previous query
        self.terms = {}
        self.terms_list = []
        self.index_blocks_to_check = set()
        self.doc_blocks_to_check = set()
        self.relevant_docids = set()
        self.term_penalty = {}
        self.term_to_tags = {}
        self.docid_to_score = {}

        for term in terms:
            # handle fields
            _term = term
            if len(term) > 1 and term[1] == ':':
                _term = term[2:]
                try:
                    self.term_to_tags[_term] += term[0]
                except:
                    self.term_to_tags[_term] = term[0]

            self.terms[_term] = {}
            self.terms_list.append(_term)

        self.terms_list.sort()

        current_block = 0
        done = False

        init_block = self.get_block_path(current_block)
        term1 = ''
        with open(init_block, "r") as f:
            term1 = f.readline().split(' ')[0]

        while not done:
            next_block_path = self.get_block_path(current_block+1)

            # term1 = first term of block
            # term2 = first term of next block

            try:
                with open(next_block_path, "r") as f:
                    term2 = f.readline().split(' ')[0]
            # when next block doesn't exist, end the search
            except:
                term2 = 'z'*100 # random high indexed term
                done = True

            for term in self.terms_list:
                if term >= term1 and term < term2:
                    self.index_blocks_to_check.add(current_block)

            current_block += 1
            term1 = term2
        
        self.search_blocks()

    def search_blocks(self):
        # store index of term in terms_list
        print('yeet')

        list_tf_idfs = {}

        cur_ind = 0
        for block in sorted(self.index_blocks_to_check):
            block_path = self.get_block_path(block)

            with open(block_path, "r") as f:
                line = f.readline()
                while line and cur_ind < len(self.terms_list):
                    line = line.strip().split(' ')

                    while line[0] > self.terms_list[cur_ind]:
                        cur_ind += 1
                        if cur_ind >= len(self.terms_list):
                            break

                    if cur_ind >= len(self.terms_list):
                        break

                    if line[0] == self.terms_list[cur_ind]:
                        line = line[1:]
                        _term = self.terms_list[cur_ind]

                        for posting in line:
                            # parse content from index blocks
                            contents = posting.split(',')
                            docid = contents[0]
                            freq = int(contents[1])
                            tags = contents[2]

                            tf_idf = self.get_tf_idf(freq, self.get_idf(_term))

                            try:
                                list_tf_idfs[int(docid)] += tf_idf
                            except:
                                list_tf_idfs[int(docid)] = tf_idf

                            penalise_term = True
                            try:
                                for char in self.term_to_tags[_term]:
                                    if char in tags:
                                        # Increasing TF-IDF based on fields
                                        if char == 't':
                                            list_tf_idfs[int(docid)] += 10
                                        if char == 'i':
                                            list_tf_idfs[int(docid)] += 5
                                        penalise_term = False
                            except:
                                penalise_term = False

                            self.terms[self.terms_list[cur_ind]][int(docid)] = freq
                            self.relevant_docids.add(int(docid))

                            if penalise_term:
                                _term = self.terms_list[cur_ind]
                                try:
                                    self.term_penalty[_term].add(int(docid))
                                except:
                                    self.term_penalty[_term] = set()
                                    self.term_penalty[_term].add(int(docid))

                        cur_ind += 1

                    line = f.readline()

        cnt = 0
        for key, value in sorted(list_tf_idfs.items(), key=lambda x: x[1], reverse=True):
            cnt += 1
            if cnt > 100:
                try:
                    self.relevant_docids.remove(key)
                except:
                    pass

        self.process_docids()

    def process_docids(self):
        self.relevant_docids = sorted(list(self.relevant_docids))
        cur_ind = 0

        for docid in self.relevant_docids:
            # add appropriate doc_block to check
            self.doc_blocks_to_check.add(docid//settings.DOC_BLOCK_SIZE)

        for doc_block in sorted(self.doc_blocks_to_check):
            doc_block_path = self.get_doc_block_path(doc_block)
            with open(doc_block_path, "r") as f:
                line = f.readline()
                while line and cur_ind < len(self.relevant_docids):
                    line = line.strip().split(' ')

                    if line[0] == str(self.relevant_docids[cur_ind]):
                        # parse content from dblocks
                        self.docid_to_title[self.relevant_docids[cur_ind]] = ' '.join(line[2:])
                        self.docid_to_length[self.relevant_docids[cur_ind]] = int(line[1])

                        cur_ind += 1

                    line = f.readline()

        print('process_docids done = ', datetime.now())

    def get_idf(self, term):
        return log2(((self.doccount - len(self.terms[term]) + 0.5)/ \
               (len(self.terms[term]) + 0.5)) + 1)

    def get_tf_idf(self, tf, idf):
        return tf*idf

    def rank_docs(self):
        for docid in self.relevant_docids:
            self.docid_to_score[docid] = 0
            
            score = 0
            for term in self.terms:
                # Get TF and IDF of the term
                try:
                    TF = self.terms[term][docid]
                except:
                    continue

                try:
                    IDF = self.get_idf(term)

                    to_add = ((IDF * TF * (self.k1 + 1)) / \
                             (TF + (self.k1 * (1 - self.b + (self.b * \
                             (self.docid_to_length[docid]/ \
                              self.average_doc_length))))))
                except:
                    continue

                try:
                    if docid in self.term_penalty[term]:
                        score += to_add/2
                    else:
                        score += to_add
                except:
                    score += to_add

            self.docid_to_score[docid] = score

        print('rank_docs done = ', datetime.now())

    def get_top_n(self, n=10):
        # get ranks
        self.rank_docs()
        result = []
        
        for docid, score in sorted(self.docid_to_score.items(),
                                   key=lambda item: item[1], reverse=True):
            result.append(docid)
            if len(result) >= n:
                break

        return [str(docid) + ', ' + self.docid_to_title[docid] for docid in result]
