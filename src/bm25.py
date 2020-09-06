import os
from math import log2

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

        for term in terms:
            self.terms[term] = {}
            self.terms_list.append(term)

        self.terms_list.sort()

        current_block = 0
        done = False
        while not done:
            block_path = self.get_block_path(current_block)
            next_block_path = self.get_block_path(current_block+1)

            # term1 = first term of block
            # term2 = first term of next block
            with open(block_path, "r") as f:
                term1 = f.readline().split(' ')[0]

            try:
                with open(next_block_path, "r") as f:
                    term2 = f.readline().split(' ')[0]
            # when next block doesn't exist, end the search
            except:
                term2 = 'z'*100 # random high indexed term
                done = True

            for term in self.terms:
                if term >= term1 and term < term2:
                    self.index_blocks_to_check.add(current_block)

            current_block += 1
        
        self.search_blocks()

    def search_blocks(self):
        # store index of term in terms_list
        cur_ind = 0
        for block in sorted(self.index_blocks_to_check):
            block_path = self.get_block_path(block)

            with open(block_path, "r") as f:
                line = f.readline()
                while line and cur_ind < len(self.terms_list):
                    line = line.strip().split(' ')

                    while line[0] > self.terms_list[cur_ind]:
                        cur_ind += 1

                    if line[0] == self.terms_list[cur_ind]:
                        line = line[1:]
                        for posting in line:
                            # parse content from index blocks
                            contents = posting.split(',')
                            docid = contents[0]
                            freq = contents[1]

                            self.terms[self.terms_list[cur_ind]][int(docid)] = int(freq)
                            self.relevant_docids.add(int(docid))

                        cur_ind += 1

                    line = f.readline()

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

                IDF = log2(((self.doccount - len(self.terms[term]) + 0.5)/ \
                      (len(self.terms[term]) + 0.5)) + 1)

                score += ((IDF * TF * (self.k1 + 1)) / \
                         (TF + (self.k1 * (1 - self.b + (self.b * \
                         (self.docid_to_length[docid]/ \
                          self.average_doc_length))))))

            self.docid_to_score[docid] = score

    def get_top_n(self, n=10):
        # get ranks
        self.rank_docs()
        result = []
        
        for docid, score in sorted(self.docid_to_score.items(),
                                   key=lambda item: item[1], reverse=True):
            result.append(docid)
            if len(result) >= n:
                break

        return [self.docid_to_title[docid] for docid in result]

if __name__ == '__main__':
    # testing BM-25
    bm = BM25(index_path='./inverted_index/', doccount=19797, tokcount=22924729)
    bm.process_terms(['world', 'cup'])
    print(bm.get_top_n())
