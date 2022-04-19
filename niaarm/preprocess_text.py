import nltk
from nltk import FreqDist
from nltk.corpus import stopwords

class ExtractedText(object):
    def __init__(self, tid, text, words, frequencies, tff, weights):
        self.tid = tid
        self.text = text
        self.words = words
        self.frequencies = frequencies
        self.tff = tff
        self.weights = weights

all_words = []

class TextPreprocessing:
    def __init__(self, document):
        self.document = document
        default_stopwords = set(nltk.corpus.stopwords.words('english'))

        # tokenize
        self.text = nltk.word_tokenize(self.document)

    def remove_singlechar(self, text):
        return nltk.word_tokenize(text)

    # optional
    def remove_numbers(self, text):
        return [word for word in text if not word.isnumeric()]

    def lowercase_words(self, text):
        return [word.lower() for word in text]

    def remove_stopwords(self, text):
        return [word for word in text if word not in default_stopwords]

    def remove_special_chars(self, text):
        return [word for word in text if (":" or "<" or ">" or "-" or "/" or "http" or "www" or ".." or "..." or "'") not in word]

    def calculate_frequencies(self, text):
        all_words_in_text = []
        all_frequencies_in_text = []
        fdist = FreqDist(text)
        if len(words) > 20:
            for word, frequency in fdist.most_common(200):
                all_words_in_text.append(word)
                all_frequencies_in_text.append(frequency)
                if word not in all_words:
                    all_words.append(word)
            return all_words_in_text, all_frequencies_in_text
        else:
            return "ERROR", "ERROR"
