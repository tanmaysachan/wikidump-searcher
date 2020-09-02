import os
import settings

class InvertedIndex():
    def __init__(self, path):
        self.path = path

        self.cur_block_id = 0
        self.cur_block_name = "block_" + str(self.cur_block_id)
        
        self.cur_docblock_id = 0
        self.cur_docblock_name = "dblock_" + str(self.cur_docblock_id)

        self.index = {}
        self.doc_map = {}

        self.cur_token_count = 0
        self.cur_doc_count = 0

        self.term_count = 0

    def add_term(self, term, docid, frequency, tags):
        try:
            self.index[term].append(str(frequency) + "," + str(docid) + "," + tags)
        except:
            self.index[term] = [str(frequency) + "," + str(docid) + "," + tags]

            self.term_count += 1
            self.cur_token_count += 1

            if self.cur_token_count > settings.BLOCK_SIZE:
                self.dump_block()
                self.init_next_block()


    def add_doc(self, docid, title):
        self.doc_map[docid] = title
        self.cur_doc_count += 1
        
        if self.cur_doc_count > settings.DOC_BLOCK_SIZE:
            self.dump_docblock()
            self.init_next_docblock()

    def init_next_block(self):
        self.cur_block_id += 1
        self.cur_block_name = "block_" + str(self.cur_block_id)
        self.cur_token_count = 0
        self.index = {}

    def dump_block(self):
        block_path = os.path.join(self.path, self.cur_block_name)

        with open(block_path, "w+") as f:
            for key, value in sorted(self.index.items()):
                f.write("{} {}\n".format(key, value))

    def init_next_docblock(self):
        self.cur_docblock_id += 1
        self.cur_docblock_name = "dblock_" + str(self.cur_docblock_id)
        self.cur_doc_count = 0
        self.doc_map = {}

    def dump_docblock(self):
        docblock_path = os.path.join(self.path, self.cur_docblock_name)

        with open(docblock_path, "w+") as f:
            for key, value in sorted(self.doc_map.items()):
                f.write("{} {}\n".format(key, value))

    def get_term_count(self):
        return self.term_count

    def dump_remaining(self):
        self.dump_block()
        self.init_next_block()
        
        self.dump_docblock()
        self.init_next_docblock()

    def merge_blocks(self):


    def cleanup(self):
        self.dump_remaining()
        merge_blocks()
