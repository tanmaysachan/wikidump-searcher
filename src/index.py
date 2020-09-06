import os
import indexer

if __name__ == '__main__':

    indexer = indexer.Indexer(index_path='./inverted_index/')

    path = '/home/tani/wikidump/'
    
    for filename in os.listdir(path):
        if filename.startswith('wikidump') and \
           not filename.endswith('bz2'):
            print('parsing {}...'.format(filename))
            indexer.parse_data(os.path.join(path, filename))

    indexer.finish_indexing()
