import numpy as np
import nltk
# nltk.download('punkt')
from nltk.stem.porter import PorterStemmer
stemmer = PorterStemmer()

def tokenize(sentence):
    """
    Split sentence into an array of words/tokens.
    A token can be a word, punctuation character, or number.
    """
    return nltk.word_tokenize(sentence)

def stem(word):
    """
    Perform stemming to find the root form of the word.
    Example:
    word = "organizes"
    stemmed_word = stem(word)
    -> "organ"
    """
    return stemmer.stem(word.lower())

def bag_of_words(tokenized_sentence, words):
    """
    Return a bag of words array:
    1 for each known word that exists in the tokenized sentence, 0 otherwise.
    Example:
    tokenized_sentence = ["hello", "how", "are", "you"]
    words = ["hi", "hello", "I", "you", "bye", "thank", "cool"]
    bag = [0, 1, 0, 1, 0, 0, 0]
    """
    # Stem each word
    sentence_words = [stem(word) for word in tokenized_sentence]
    # Initialize bag with 0 for each word
    bag = np.zeros(len(words), dtype=np.float32)
    for idx, w in enumerate(words):
        if w in sentence_words: 
            bag[idx] = 1

    return bag
