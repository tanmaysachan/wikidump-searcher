import os
import sys
import datetime
import math

import queryparser

if __name__ == '__main__':
    query_parser = queryparser.QueryParser(index_path='./inverted_index/')
    
    queries = []
    result_count = []
    with open("queries.txt", "r") as f:
        line = f.readline()
        while line:
            line = line.strip()
            num_results = int(line.split(',')[0])
            query = (' '.join(line.split(',')[1:])).strip()
            queries.append(query)
            result_count.append(num_results)

            line = f.readline()

    cur = 0
    with open("queries_op.txt", "w+") as f:
        for query in queries:
            now = datetime.datetime.now()
            print(now)
            results = query_parser.parse_query(query, num_results=result_count[cur])
            end = datetime.datetime.now()
            for result in results:
                f.write(result + '\n')

            f.write(str((end-now).seconds) + ' ' + str(((end-now).seconds/result_count[cur])))
            f.write('\n\n')
            cur += 1
