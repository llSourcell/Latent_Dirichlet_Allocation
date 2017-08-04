import os
import random
import bisect
import stopwords


#GLOBAL VARIABLES

eng_dict = []
#location of your English dictionary
dict_file = open("/usr/share/dict/words",'r')
for line in dict_file:
    #I assume your dictionary's words are separated by whitespace,
    #but it it's commas you can do split(',')
    items = line.split()
    for word in items:
        eng_dict.append(word)
eng_dict = set(eng_dict)

#word_index serves as a two-way lookup table: given a word, return its index,
#and vice-versa. Also has key "n_words" which gives number of words in
#vocabulary.
word_index = {"n_words":0}
#The coefficients alpha and beta are derived from the multinomial distribution
#assumed by the model. alpha=0.1 and beta=0.0002 are generally good.
#The lower alpha, the fewer topics per document
#alpha should be low but nonzero so that words can group by document as well.
alpha = 0.1
#The lower beta, more extreme each topic's word frequencies
beta = 0.0002




def is_word(phrase):
    if len(phrase) < 3:
        return False
    if phrase in stopwords.STOP_WORDS:
        return False
    if phrase[0] == "\\":
        return False
    if phrase in eng_dict:
        return True
    return False


def get_fnames():
    #your function for creating a list of files to use
    names = []
    dir = "/Users/martin/Documents/Mudd/"
    exts = ["tex"]
    for root, dirs, files in os.walk(dir):
        for f in files:
            items = f.split('.')
            if len(items) > 1 and items[1] in exts:
                names.append(root+"/"+f)
    return names

def read_docs():
    #turn each document into a list of words
    docs = []
    fnames = get_fnames()
    for fname in fnames:
        docs.append(read_doc(fname))

    return docs

def read_doc(fname):
    #If you are using files that aren't plain text, you may have to change this
    f = open(fname, 'r')
    doc = []
    for line in f:
        if line[0] == "%":
            continue
        phrases = line.split()
        for phrase in phrases:
            p1 = phrase[-1]
            if p1 in stopwords.PUNCTUATION:
                phrase = phrase[:-1]
            phrase = phrase.lower()
            if is_word(phrase):
                if phrase not in word_index:
                    n_words = word_index["n_words"]
                    word_index[phrase] = n_words
                    word_index[n_words] = phrase
                    word_index["n_words"] += 1
                ind = word_index[phrase]
                doc.append(ind)
    return doc


def random_choice(probs):
    #given a list of probabilities, randomly return an index i according to
    #that index's probability.
    partials = []
    psum = 0.
    for p in probs:
        psum += p
        partials.append(psum)

    choice = random.random()*psum
    #bisect_right does binary search to find minimal k where partials[k]>choice
    return bisect.bisect_right(partials, choice)


def probs(v, nkm, nkr, nk, n_topics):
    #get something proportional to the
    #probability for word n to be in
    #each topic k
    #given that there are n_topics topics. The word is vth from vocabulary.
    #nkm is number of words from this document in kth topic
    #nkr is number of times rth word from vocab appears in kth topic
    #nk is number of words in kth topic
    n_words = word_index["n_words"]
    res = [0]*n_topics   #a probability to be in each topic

    for k in range(n_topics):
        res[k] = (nkm[k]+alpha)*(nkr[k][v]+beta)/(nk[k]+n_words*beta)
    return res



def get_topics(iters, w_counts, docs, n_topics):
    #returns total number of words in each topic and relative distribution of
    #words in topic compared to distribution across all documents
    n_words = word_index["n_words"]
    zs = []
    nkr = [[0]*n_words for _ in range(n_topics)] #(k,r)th element is number of
    #times rth word from vocab appears in topic k
    nkm = [[0]*n_topics for _ in range(len(docs))]
    #(m,k)th element is number of words in document m are in kth topic
    nk  = [0]*n_topics #number of words in each topic

    n_words_total = 0 #number of words in all documents, INCLUDING repetition
    for i in range(len(docs)):
        zs.append([])
        for j in range(len(docs[i])):
            topic = random.randint(0,n_topics-1)
            zs[i].append(topic)
            ind = docs[i][j]
            nkm[i][topic] += 1
            nkr[topic][ind] += 1
            nk[topic] += 1
            n_words_total += 1
    for it in range(iters):
        print "Iteration",it
        for i in range(len(docs)):
            for j in range(len(docs[i])):
                ind = docs[i][j]
                k = zs[i][j]
                nkm[i][k] -= 1
                nkr[k][ind] -= 1
                nk[k] -= 1
                ps = probs(ind, nkm[i], nkr, nk, n_topics)
                newk = random_choice(ps)
                nkm[i][newk] += 1
                nkr[newk][ind] += 1
                nk[newk] += 1
                zs[i][j] = newk

    for k in range(n_topics):
        for v in range(n_words):
            nkr[k][v] /= nk[k]+0.
            nkr[k][v] -= (w_counts[v]+ 0.)/n_words_total
    return [[nk[k],nkr[k]] for k in range(n_topics)]


def display_topics(topics):
    #take output of topics and make it look pretty
    relevant = 10	#I only care about 10 most frequent words in topic
    n_words = word_index["n_words"]
    for nk,t in topics:
        top = [[-1,0]]*relevant
        for i in range(n_words):
            for j in range(relevant):
                if t[i] > top[j][1]:
                    top[j+1:] = top[j:-1]
                    top[j] = [word_index[i],t[i]]
                    break
        print "\n"+"==TOPIC==", " with number of words =", nk
        for rank in top:
            print rank

def main():
    docs = read_docs()
    n_topics = 12 #number of topics
    n_words = word_index["n_words"]
    w_counts = [0]*n_words
    #Number of iterations should probably be about 10 for decent convergence
    #each iteration iterates over all meaningful words in each document, so this
    #could be expensive for large document sets
    iters = 10
    for doc in docs:
        for word in doc:
            w_counts[word] += 1
    topics = get_topics(iters, w_counts, docs , n_topics)
    display_topics(topics)


if __name__ == "__main__":
    main()
