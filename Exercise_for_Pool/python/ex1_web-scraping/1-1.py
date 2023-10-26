import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

# グルナビの一覧ページのURLを指定
mainurl = "空白"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}

data = {
    'ID': [],
    '店舗名': [],
    '電話番号': [],
    'メールアドレス': [],
    '都道府県': [],
    '市区町村': [],
    '番地': [],
    '建物名': [],
    'URL': [],
    'SSL': []
}
df = pd.DataFrame(data)

items = 50

id_num = 1
page = 1

while id_num <= items:
    url = mainurl + '?p=' + str(page)
    # 一覧ページの内容をダウンロード
    response = requests.get(url, headers=headers)

    # ページの内容をパース
    soup = BeautifulSoup(response.text, "html.parser")
    # 各店舗のURLを取得
    restaurant_links = soup.find_all("a", class_="style_titleLink__oiHVJ")

    # 各店舗の情報を取得
    for link in restaurant_links:
        if id_num > items:
            break
        try:
            restaurant_url = link["href"]  # 各店舗の詳細ページのURL
            restaurant_response = requests.get(restaurant_url)
            restaurant_soup = BeautifulSoup(
                restaurant_response.text, "html.parser")

            try:
                response = requests.head(link)
                ssl_enabled = response.url.startswith("https")
                if ssl_enabled == True:
                    is_ssl_enabled = "True"
                else:
                    is_ssl_enabled = "False"
            except Exception:
                is_ssl_enabled = "False"

            # 店舗情報を取得
            name = restaurant_soup.find("p", id="info-name").text
            address = restaurant_soup.find("span", class_="region").text
            phone = restaurant_soup.find("span", class_="number").text

            try:
                # 建物名が格納されている'locality'タグがあるとき
                building = restaurant_soup.find("span", class_="locality").text
            except Exception:
                building = ""

            pattern = r"([^\x01-\x7E]+?[都道府県])(.+?[^0-9])(\d.*)$"
            matches = re.search(pattern, address)
            if matches:
                prefecture = matches.group(1)
                city = matches.group(2)
                street = matches.group(3)
            else:
                prefecture = address
                city = ""
                street = ""

            # データを辞書に格納
            new_data = {
                'ID': int(id_num),
                '店舗名': name,
                '電話番号': phone,
                'メールアドレス': " ",
                '都道府県': prefecture,
                '市区町村': city,
                '番地': street,
                '建物名': building,
                'URL': link,
                'SSL': is_ssl_enabled
            }

            # リストに新しいデータを追加
            data_list = [new_data]

            # データフレームに追加
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)

            # IDの更新
            id_num += 1

        except Exception:
            pass
    page += 1

# CSVファイルにデータフレームを保存
df.to_csv('restaurant_info.csv', index=False)
