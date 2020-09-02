BLOCK_SIZE = 4000
DOC_BLOCK_SIZE = 4000

tok_reg = r'[^A-Za-z0-9]+'
infobox_reg = r"{{infobox((.|\n)*)}}\n"
categories_reg = r"\[\[category:(.*)\]\]"
references_reg = r"\{\{cite(.*?)\}\}<"
external_reg = r"==.*external links.*=="
links_reg = r"(https?://\S+)"
