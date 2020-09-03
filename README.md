# wikidump-indexer
Indexes the wikidump using SPIMI

* `pip install -r requirements.txt`
* `index.sh /path/to/dump/ /path/to/inverted_index_directory/ /path/to/stats_file/` to index the dump
* `search.sh /path/to/inverted_index_directory/ query` to query the dump
