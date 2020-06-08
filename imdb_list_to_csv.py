import requests
from bs4 import BeautifulSoup
import pandas as pd
from string import ascii_letters, digits
import argparse
# from tqdm import tqdm


def make_soup(url, headers=None, features='lxml'):
    result = requests.get(url, headers=headers)
    src = result.content
    soup = BeautifulSoup(src, features=features)
    return soup


def format_filename(s):
    valid_chars = f"-_.() {ascii_letters}{digits}"
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_')
    return f"{filename}.csv"


def check(x):
    if x:
        return x.text.strip()
    else:
        return ""


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Export an IMDb list as .csv')
    parser.add_argument('url', type=str, help='URL to the IMDb list. Format: https://www.imdb.com/list/lsXXXXXXXXX/')
    args = parser.parse_args()

    # Paste link / check title "https://www.imdb.com/list/ls006660717/"
    url = args.url
    headers = {"Accept-Language": "en-US,en;q=0.5"}
    soup = make_soup(url, headers=headers)
    print('------------------------------------------------------------------')
    print(soup.title.text)
    print('------------------------------------------------------------------')

    # Prepare dataframe
    df = pd.DataFrame(columns=["Title", "Certificate", "Runtime", "Genres", "IMDb-rating", "Metascore",
                               "Description", "Directors", "Stars", "Votes", "Gross"])

    # File name (list title)
    list_title = soup.find('h1', class_='header list-name')
    file = format_filename(list_title.text.strip())

    continue_ = True
    page = 1

    # for all pages
    while (continue_):
        # make request
        url_temp = f"{url}?page={page}"
        print(url_temp)
        soup = make_soup(url_temp, headers=headers)

        # check if there is a next page
        next_ = soup.find('a', class_="flat-button lister-page-next next-page")
        if next_ is None:
            continue_ = False
        else:
            page += 1

        # find all list items
        items = soup.find_all('div', class_='lister-item-content')

        for item in items:
            # title, certificate, runtime, genres, rating, metascore
            title = check(item.h3.a)
            certificate = check(item.find('span', class_='certificate'))
            runtime = check(item.find('span', class_='runtime'))
            genres = check(item.find('span', class_='genre'))
            rating = check(item.find('span', class_='ipl-rating-star__rating'))
            metascore = check(item.find('span', class_="metascore favorable"))

            # description, directors, stars
            p = item.find_all('p')
            description = check(p[1])

            splitted = p[2].text.split('|')
            try:
                directors, stars = splitted
            except ValueError:
                if splitted[0].startswith('Director:'):
                    directors = splitted[0]
                    stars = ""
                elif splitted[0].startswith('Stars:'):
                    stars = splitted[0]
                    directors = ""
                else:
                    stars = ""
                    directors = ""
            directors = directors.strip()[10:].replace("\n", "")
            stars = stars.strip()[6:].replace("\n", "")

            # votes, gross
            p3_spans = p[3].find_all('span')

            try:
                votes = p3_spans[1]['data-value']
            except IndexError:
                votes = ""

            try:
                gross = p3_spans[4]['data-value'].replace(",", "")
            except IndexError:
                gross = ""

            fields = [title, certificate, runtime, genres, rating,
                      metascore, description, directors, stars, votes, gross]
            data = pd.Series(fields, index=df.columns)
            df = df.append(data, ignore_index=True)

    df.to_csv(file, index=False)
    print('------------------------------------------------------------------')
    print(f"Done! Saved as {file}")
