import os

from app import celery
import matplotlib.pyplot as plt
import nltk
import pymorphy2
import re
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from collections import OrderedDict

def parse_pdf(static, year):
    if os.path.exists(f"{static}/reports/report{year}.txt"):
        return
    with open(f"{static}/reports/report{year}.pdf", 'rb') as rd:
        with open(f"{static}/reports/report{year}.txt", "wb+") as fd:
            resource_manager = PDFResourceManager()
            converter = TextConverter(resource_manager, fd)
            page_interpreter = PDFPageInterpreter(resource_manager, converter)
            pages = PDFPage.get_pages(rd,
                                      caching=True,
                                      check_extractable=True)
            for page in pages:
                page_interpreter.process_page(page)
            converter.close()


def tokenize_ru(static, year):
    read_path = f"{static}/reports/report{year}.txt"
    write_path = f"{static}/reports/report_tokenized{year}.txt"
    if os.path.exists(write_path):
        with open(write_path, 'r') as fd:
            words = fd.read()
            words_filtered = words.split(' ')
    else:
        with open(read_path, 'r') as fd:
            text = fd.read()
        words = nltk.tokenize.word_tokenize(text)
        stop_words = nltk.corpus.stopwords.words('russian')
        stop_words.extend(
            ['что', 'также', 'тоже', 'это', '%', 'так', 'вот', 'быть', 'как', 'в', '”', '“', '–', 'к', '.', 'на',
             '...'])
        stop_words = set(stop_words)
        words_filtered = []
        for w in words:
            if w not in stop_words:
                s = re.sub(r'\d+', ' ', w)
                s = re.sub(r'(\w)-(\w)', r'\1\2', s)
                if re.match(r'^(?:\w|-)*[a-яё](?:\w|-)*$', s):
                    words_filtered.append(s)
        with open(write_path, 'wb+') as fd:
            fd.write(' '.join(words_filtered).encode('utf-8'))
    return words_filtered


def normalize(year, words, static):
    path = f"{static}/reports/report_normalized{year}.txt"
    if not os.path.exists(path):
        with open(path, 'wb+') as fd:
            morph = pymorphy2.MorphAnalyzer()
            base_words = [morph.parse(token)[0].normal_form for token in words]
            fd.write(' '.join(base_words).encode('utf-8'))
    else:
        with open(path, 'r') as fd:
            base_words = fd.read()
            base_words = base_words.split(' ')
    return base_words


def data_for_graph(static, words, year, norm):
    plt.figure(figsize=(15, 8))
    if norm:
        plt.title("График зависимости размера нормализованного словаря от общего числа слов в тексте")
        save_path = f"{static}/reports/fig_norm{year}"
    else:
        plt.title("График зависимости размера словаря от общего числа слов в тексте")
        save_path = f"{static}/reports/fig_denorm{year}"
    if os.path.exists(save_path):
        return
    used_words = []
    func = [0]
    for word in words:
        if word not in used_words:
            used_words.append(word)
        func.append(len(used_words))
    points_x = []
    points_y = []

    for i in range(0, len(func), 1):
        points_x.append(i)
        points_y.append(func[i])
    plt.plot(points_x, points_y, color='r', linestyle='-')
    plt.ylabel('Размер словаря')
    plt.savefig(save_path)
    return


def graph(static, words, base_words, year):
    data_for_graph(static, words, year, norm=False)
    data_for_graph(static, base_words, year, norm=True)
    zipf_path = f"{static}/reports/fig_zipf{year}"

    frequency = nltk.FreqDist(base_words)
    if os.path.exists(zipf_path):
        return frequency.most_common(50)
    order = OrderedDict(sorted(frequency.items(), key=lambda t: t[1], reverse=True))
    n = 50
    y_pos = range(n)
    s = 1
    plt.figure(figsize=(15, 6))
    expected_zipf = [i / (j + 1) ** s for j, i in zip(y_pos, list(order.values())[:n])]
    plt.bar(y_pos, list(order.values())[:n], color='g',
            alpha=0.5)
    plt.plot(y_pos, expected_zipf, color='r', linestyle='-',
             linewidth=2, alpha=0.5)
    plt.ylabel('Частота')
    plt.xlabel('Ранг')
    plt.xlim([0, n])
    plt.title(f"Топ {n} слов")
    plt.savefig(zipf_path)
    return frequency.most_common(50)


def create_zipf_table(frequencies):
    """
    Takes the list created by _top_word_frequencies
    and inserts it into a list of dictionaries,
    along with the Zipfian data.
    """

    zipf_table = []

    top_frequency = frequencies[0][1]

    for index, item in enumerate(frequencies, start=1):
        relative_frequency = "1/{}".format(index)
        zipf_frequency = top_frequency * (1 / index)
        difference_actual = item[1] - zipf_frequency
        difference_percent = (item[1] / zipf_frequency) * 100

        zipf_table.append({"word": item[0],
                           "actual_freq": item[1],
                           "relative_freq": relative_frequency,
                           "zipf_freq": zipf_frequency,
                           "diff_actual": difference_actual,
                           "diff_percent": difference_percent})

    return zipf_table


@celery.task(bind=True)
def process_report(self, static, year):
    message = "Идёт преобразование pdf файла в текстовый."
    self.update_state(state='Обработка',
                      meta={'current': 0, 'total': 100,
                            'status': message})
    parse_pdf(static, year)
    message = "Загрузка дополнительных модулей NLTK."
    self.update_state(state='Обработка',
                      meta={'current': 20, 'total': 100,
                            'status': message})
    if not os.path.exists(f"{static}/nltk_data"):
        nltk_path = f"{static}/nltk_data"
        os.mkdir(nltk_path)
        nltk.download('punkt',download_dir=nltk_path)
        nltk.download('stopwords',download_dir=nltk_path)
        nltk.download('averaged_perceptron_tagger',download_dir=nltk_path)
        nltk.download('wordnet',download_dir=nltk_path)

    message = "Удаление стоп-слов текста."
    self.update_state(state='Обработка',
                      meta={'current': 40, 'total': 100,
                            'status': message})
    words = tokenize_ru(static, year)

    message = "Нормализация слов."
    self.update_state(state='Обработка',
                      meta={'current': 60, 'total': 100,
                            'status': message})
    base_words = normalize(static=static, year=year, words=words)
    message = "Построение графиков"
    self.update_state(state='Обработка',
                      meta={'current': 80, 'total': 100,
                            'status': message})
    common = graph(static, words, base_words, year)
    return {"current": 100, "total": 100, "status": "Обработка завершена",
            "year": year,
            "common": create_zipf_table(common)}
