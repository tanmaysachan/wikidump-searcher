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
                f.write("{} {}\n".format(key, ' '.join(value)))

    def get_term_count(self):
        return self.term_count

    def dump_remaining(self):
        self.dump_block()
        self.init_next_block()
        
        self.dump_docblock()
        self.init_next_docblock()
    
    # Implementation of SPIMI algorithm for indexing

    def merge_blocks(self):
        done = False # Triggered when all blocks get EOF

        file_iters = []

        for block in range(self.total_block_count):
            block_file_name = "block_" + str(block)
            file_iters.append(open(os.path.join(self.path, block_file_name), "r"))
        
        heap = []
        entries = []
        for f_iter in file_iters:
            line = f_iter.readline().strip().split(' ')
            entries.append(line)
            heapq.heappush(heap, line[0])

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
                    self.merged_index[least_elem] += entries[i][1:]
                    # Increment file pointer
                    try:
                        entries[i] = file_iters[i].readline().strip().split(' ')
                        heapq.heappush(heap, entries[i][0])
                        cnt += 1
                    except:
                        pass

            if token_count_merged_index > settings.MERGED_BLOCK_SIZE:
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
