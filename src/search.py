import os
import sys

import queryparser

if __name__ == '__main__':
    query_parser = queryparser.QueryParser(index_path='./inverted_index/')
    
    query = sys.argv[1]
    results = query_parser.parse_query(query)
    
    print(results)
