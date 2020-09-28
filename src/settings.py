BLOCK_SIZE = 1000000
DOC_BLOCK_SIZE = 2000
MERGED_BLOCK_SIZE = 10000

MAX_POSTING_LIST_SIZE = 100000

tok_reg = r'[^A-Za-z0-9]+'
infobox_reg = r"{{infobox((.|\n)*)}}\n"
categories_reg = r"\[\[category:(.*)\]\]"
references_reg = r"\{\{cite(.*?)\}\}<"
external_reg = r"==.*external links.*=="
links_reg = r"(https?://\S+)"
ignore_reg = r"[0-9]+[a-z]+[0-9a-z]*"

STATS_FILE = "STATS.txt"
