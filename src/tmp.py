import pickle
stopwords = set()

with open('stopwords.txt', 'r') as f:
    word = f.readline().strip()
    while word:
        stopwords.add(word)
        word = f.readline().strip()

with open('stopwords.pickle', 'wb+') as f:
    pickle.dump(stopwords, f)
