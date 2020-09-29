import os
import settings
import heapq

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

        self.total_block_count = 0

        self.merged_index = {}
        self.cur_merged_index_id = 0
        self.cur_merged_index_name = "index_" + str(self.cur_merged_index_id)

        self.total_doc_count = 0

        self.total_token_count = 0

    def set_total_token_count(self, tok_count):
        self.total_token_count = tok_count

    def add_term(self, term, docid, frequency, tags):
        try:
            self.index[term].append(str(docid) + "," + str(frequency) + "," + tags)
        except:
            self.index[term] = [str(docid) + "," + str(frequency) + "," + tags]

            self.term_count += 1
            self.cur_token_count += 1

            if self.cur_token_count >= settings.BLOCK_SIZE:
                self.dump_block()
                self.init_next_block()


    def add_doc(self, docid, title, token_count):
        # Store token count followed by title for BM-25
        self.doc_map[docid] = str(token_count) + ' ' + title
        self.total_doc_count += 1
        self.cur_doc_count += 1
        
        if self.cur_doc_count >= settings.DOC_BLOCK_SIZE:
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
                f.write("{} {}\n".format(key, ' '.join(value)))

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
    
    # Implementation of SPIMI algorithm for indexing

    def merge_blocks(self, block_count=-1):
        print("merging blocks...")

        if block_count == -1:
            block_count = 1000000

        done = False # Triggered when all blocks get EOF

        file_iters = []

        for block in range(block_count):
            block_file_name = "block_" + str(block)

            try:
                file_iters.append(open(os.path.join(self.path, block_file_name), "r"))
            except:
                break
        
        heap = []
        entries = []
        for f_iter in file_iters:
            line = f_iter.readline().strip().split(' ')
            title = line[0]
            if len(line) <= settings.MAX_POSTING_LIST_SIZE:
                entries.append(line)
            else:
                to_append = [line[0]]
                for elem in line[1:]:
                    contents = elem.split(',')
                    # append element only if term freq more than 1,
                    # or if term in a field
                    if int(contents[1]) > 1 or len(contents[2]) != 0:
                        to_append.append(elem)

                entries.append(to_append)
            heapq.heappush(heap, title)

        token_count_merged_index = 0

        while not done:
            while len(heap) > 0 and heap[0] == '':
                heapq.heappop(heap)

            try:
                least_elem = heapq.heappop(heap)
            except:
                # Heap empty, clean up
                print('finishing...')
                for i in file_iters:
                    if i:
                        i.close()
                break

            while len(heap) > 0 and heap[0] == least_elem:
                heapq.heappop(heap)

            self.merged_index[least_elem] = []
            token_count_merged_index += 1

            files_touched = False

            for i in range(len(entries)):
                if entries[i][0] == least_elem:
                    files_touched = True

                    # Append the posting list
                    # if number of postings greater than this, IDF is essentially 0

                    if len(entries[i][1:]) <= settings.MAX_POSTING_LIST_SIZE:
                        self.merged_index[least_elem] += entries[i][1:]
                    else:
                        for elem in entries[i][1:]:
                            contents = elem.split(',')
                            # append element only if term freq more than 1,
                            # or if term in a field
                            if int(contents[1]) > 1 or len(contents[2]) != 0:
                                self.merged_index[least_elem].append(elem)
                        continue
                    # Increment file pointer
                    try:
                        entries[i] = file_iters[i].readline().strip().split(' ')
                        heapq.heappush(heap, entries[i][0])
                    except:
                        pass

            if token_count_merged_index >= settings.MERGED_BLOCK_SIZE:
                print("dumping tokens...")
                self.dump_merged_index_blocks()
                self.init_next_merged_index_block()
                token_count_merged_index = 0

            if not files_touched:
                # Finish if no files affected, error
                print('something went wrong')
                for i in file_iters:
                    if i:
                        i.close()
                done = True

    def init_next_merged_index_block(self):
        self.cur_merged_index_id += 1
        self.cur_merged_index_name = "index_" + str(self.cur_merged_index_id)
        self.merged_index = {}

    def dump_merged_index_blocks(self):
        merged_block_path = os.path.join(self.path, self.cur_merged_index_name)

        print('creating file {}'.format(merged_block_path))
        with open(merged_block_path, "w+") as f:
            for key, value in sorted(self.merged_index.items()):
                # Store doc count for each term
                f.write("{} {}\n".format(key, ' '.join(value)))

    def cleanup(self):
        self.dump_remaining()
        self.total_block_count = self.cur_block_id
        print("TOTAL BLOCKS CREATED " + str(self.total_block_count))
        self.merge_blocks()
        # Dump remaining merged indexes
        self.dump_merged_index_blocks()

        for block in range(self.total_block_count):
            # Remove all blocks
            os.remove(os.path.join(self.path, "block_" + str(block)))

        # generate stat file for implementation of BM-25
        stat_file = os.path.join(self.path, settings.STATS_FILE)
        with open(stat_file, "w+") as f:
            f.write("NUM_DOCS=" + str(self.total_doc_count) + '\n')
            f.write("TOKEN_COUNT=" + str(self.total_token_count) + '\n')
            f.write("BLOCKS_CREATED=" + str(self.total_block_count) + '\n')
            f.write("MERGED_BLOCKS_CREATED=" + str(self.cur_merged_index_id) + '\n')
            f.write("DOC_BLOCKS_CREATED=" + str(self.cur_docblock_id) + '\n')
