import requests
from bs4 import BeautifulSoup
import pandas as pd
from string import ascii_letters, digits
import argparse
from tqdm import tqdm


def make_soup(url, headers=None, features='lxml'):
    result = requests.get(url, headers=headers)
    if result.status_code != 200:
        print("Error - Status code:", result.status_code)
        return None
    src = result.content
    soup = BeautifulSoup(src, features=features)
    return soup


def format_filename(s):
    valid_chars = f"-_.() {ascii_letters}{digits}"
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_')
    return f"{filename}.csv"


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Export a TV Show (episode titles, ratings, description, etc.) from IMDb to .csv')
    parser.add_argument('url', type=str, help='URL to the IMDb list. Format: https://www.imdb.com/list/lsXXXXXXXXX/')
    args = parser.parse_args()

    # Paste link / check title "https://www.imdb.com/list/ls006660717/"
    url = args.url
    headers = {"Accept-Language": "en-US,en;q=0.5"}
    soup = make_soup(url, headers=headers)
    print('------------------------------------------------------------------')
    print(soup.title.text)
    print('------------------------------------------------------------------')

    wrapper = soup.find('div', class_='title_wrapper')
    title = wrapper.find('h1')
    file = format_filename(title.text.strip())
    # print(file)

    titleID = url.split('/')[4]
    # print(titleID)

    sayn = soup.find('div', class_='seasons-and-year-nav')
    max_season = int(sayn.find('a').text)
    # print(max_season)

    df = pd.DataFrame(columns=["season", "episode", "release", "title", "rating", "description"])

    for i in tqdm(range(max_season), bar_format='{l_bar}{bar:33}| {n_fmt}/{total_fmt} Seasons [{elapsed}<{remaining}]{bar:-33b}'):
        url = f"https://www.imdb.com/title/{titleID}/episodes?season={i+1}"
        soup = soup = make_soup(url, headers=headers)
        # print(soup.title.text)

        odd = soup.find_all('div', class_='list_item odd')
        even = soup.find_all('div', class_='list_item even')
        episodes = list(sum(list(zip(odd, even)), ()))
        if len(odd) != len(even):
            episodes.append(odd[-1])
        # print(len(episodes))

        for ep in episodes:
            # formatting
            a = list(filter(bool, ep.text.splitlines()))
            b = [c.strip() for c in a if c.strip() != '']
            # ['Sx, Epx', 'releasedate', 'title', 'rating']
            details = (b[:4])
            if len(details[3]) > 3:
                details[3] = ''
            # description
            details.append(b[-1])
            # split seasons and episode
            try:
                [season, episode] = details[0].split(', ')
            except ValueError:
                break
            final = [season[1:], episode[2:]] + details[1:]
            final_series = pd.Series(final, index=df.columns)
            df = df.append(final_series, ignore_index=True)

    df.to_csv(file, index=False)
    print(f"Saved as {file}")
