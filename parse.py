import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import datetime
import sqlite3 

# Список со страницами отзывов на три фильма, на каждой 256 страниц
# films_to_parse = ['https://letterboxd.com/film/anora/reviews/page/',
#                   'https://letterboxd.com/film/poor-things-2023/reviews/page/',
#                   'https://letterboxd.com/film/poor-things-2023/reviews/page/']

films_to_parse = ['https://letterboxd.com/film/poor-things-2023/reviews/page/',
                  'https://letterboxd.com/film/the-substance/reviews/page/']


def parse_review(soup: BeautifulSoup) -> dict:
    lang = soup.find('div', {'class': 'js-review-body'}).get('lang')
    if lang != 'en':
        return
    try:
        text = soup.find('div', {'class': 'js-review-body'}).get_text().replace('\n', '')
        author = soup.find('span', {'itemprop': 'name'}).get_text().strip()
        film = soup.find('span', {'class': 'film-title-wrapper'}).get_text().strip()
        date = soup.find('section', {'class': 'film-viewing-info-wrapper'}).find('meta').get('content')
        rating = soup.find('span', {'class': 'rating'}).get('class')[-1].split('-')[-1]
    except AttributeError:
        return
    return {'text': text,
            'author': author,
            'film': film,
            'date': date,
            'rating': rating}


def save_review(dicti: dict):
    if not dicti:
        return
    con = sqlite3.connect("/Users/mac/Desktop/vscode/project_letterboxd_analysis/letterboxd_project.sqlite")
    cur = con.cursor()
    # print(dicti)
    # cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # print("Tables in DB:", cur.fetchall())
    cur.execute('SELECT id FROM films WHERE name = ?', (dicti['film'],))
    film_id = cur.fetchone()[0]
    # print(film_id)
    que = 'INSERT into reviews(text,author,film_id,date,rating) VALUES(?,?,?,?,?)'
    try:
        cur.execute(que, (dicti['text'], dicti['author'], film_id, dicti['date'], dicti['rating'],))
    except sqlite3.IntegrityError:
        return
    con.commit()
    con.close()

pages = []
for film in films_to_parse:
    for i in tqdm(range(256)):
        page = requests.get(film + str(i) + '/').text
        pages.append(page)

for page in tqdm(pages):
    soup = BeautifulSoup(page, 'html.parser')
    reviews = soup.find_all('li', {'class': 'film-detail'})
    for review in reviews:
        review_href = review.find('div', {'class': "film-detail-content"})
        review_page = requests.get(
            'https://letterboxd.com' + review_href.find('a', {'class': 'context'}).get('href')).text
        soup_page = BeautifulSoup(review_page, 'html.parser')
        data = parse_review(soup_page)
        save_review(data)