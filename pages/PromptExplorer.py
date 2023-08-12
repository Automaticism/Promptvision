import gensim
from gensim.corpora import Dictionary
from gensim.models import LdaModel, HdpModel
from gensim.utils import simple_preprocess
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import operator
import string
from gensim.parsing.preprocessing import remove_stopwords
import re

st.session_state.render_image = False


def preprocess_text(text):
    # Lowercase the text.
    text = text.lower()

    # Remove punctuation.
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Remove stop words.
    text = remove_stopwords(text)

    # Tokenize the text by splitting it into individual words.
    tokens = text.split()

    # Implement lemmatization or stemming here (if desired).

    return tokens


def perform_lda_topic_modeling(df, column, n_topics=10):
    # Pre-process the text data.
    texts = [preprocess_text(text) for text in df[column]]

    # Create a dictionary from the text data.
    dictionary = Dictionary(texts)

    # Create a corpus from the dictionary.
    corpus = [dictionary.doc2bow(text) for text in texts]

    # Train an LDA topic model on the corpus.
    model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=n_topics)

    # Print the topics in the model.
    st.write("LDA Topics:")
    for topic_id, topic in model.show_topics(
        num_topics=n_topics, num_words=10, formatted=False
    ):
        topic_words = [term for term, prob in topic]
        st.write(f"Topic {topic_id + 1}: {' '.join(topic_words)}")

    # Get the document-topic probabilities, word frequencies, and topic-word distributions.
    doc_topics = model.get_document_topics(corpus)

    # Visualize the word cloud
    word_ids_dict = dictionary.token2id
    word_freqs_dict = {
        word: dictionary.cfs[word_id] for word, word_id in word_ids_dict.items()
    }
    cloud = WordCloud(
        width=900, height=450, background_color="white"
    ).generate_from_frequencies(word_freqs_dict)
    st.image(cloud.to_array())

    # Plot topic-word distributions using matplotlib
    for topic_id in range(n_topics):
        topic = model.get_topic_terms(topicid=topic_id, topn=n_topics)
        topic_words = [dictionary[id] for id, _ in topic]
        topic_probs = [prob for _, prob in topic]
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.barh(topic_words, topic_probs)
        ax.invert_yaxis()
        ax.set_xlabel("Probability")
        ax.set_title(f"Topic {topic_id + 1}")
        st.pyplot(fig)


def perform_hdp_topic_modeling(df, column, n_topics=10):
    # Pre-process the text data.
    texts = [preprocess_text(text) for text in df[column]]

    # Create a dictionary from the text data.
    dictionary = Dictionary(texts)

    # Create a corpus from the dictionary.
    corpus = [dictionary.doc2bow(text) for text in texts]

    # Train an HDP topic model on the corpus.
    model = HdpModel(corpus=corpus, id2word=dictionary)

    # Print the topics in the model.
    st.write("HDP Topics:")

    # Get the document-topic probabilities using HDP's inference.
    doc_topics = model.inference(corpus)[0]
    topic_terms = model.get_topics()

    # Visualize the word cloud
    word_ids_dict = dictionary.token2id
    word_freqs_dict = {
        word: dictionary.cfs[word_id] for word, word_id in word_ids_dict.items()
    }
    cloud = WordCloud(
        width=900, height=450, background_color="white"
    ).generate_from_frequencies(word_freqs_dict)
    st.image(cloud.to_array())

    # Plot topic-word distributions using matplotlib
    for topic_id, topic in enumerate(topic_terms[:n_topics]):  # Limit the topics
        topic_words = [dictionary[id] for id in topic.argsort()[-n_topics:][::-1]]
        topic_probs = [topic[id] for id in topic.argsort()[-n_topics:][::-1]]
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.barh(topic_words, topic_probs)
        ax.invert_yaxis()
        ax.set_xlabel("Probability")
        ax.set_title(f"Topic {topic_id + 1}")
        st.pyplot(fig)


# Example usage
column = st.selectbox("Select a column to analyze:", st.session_state.df.columns)
model_type = st.selectbox("Select a model type:", ["lda", "hdp"])

if model_type == "lda":
    n_topics = st.slider("Select the number of topics:", 1, 20, 10)
    perform_lda_topic_modeling(st.session_state.df, column, n_topics=n_topics)
elif model_type == "hdp":
    n_topics = st.slider("Select the number of topics:", 1, 20, 10)
    perform_hdp_topic_modeling(st.session_state.df, column, n_topics=n_topics)
else:
    st.write