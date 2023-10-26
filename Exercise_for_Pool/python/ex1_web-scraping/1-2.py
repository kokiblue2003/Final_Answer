import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import requests


# SSL情報を取得するための関数を作成

def check_ssl(link):
    try:
        response = requests.head(link)
        ssl_enabled = response.url.startswith("https")
        if ssl_enabled == True:
            return "True"
        else:
            return "False"
    except Exception:
        return False


# ウェブドライバーの設定
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
driver = webdriver.Chrome(options=chrome_options)

# 保存データのリストを作成
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

# IDの初期値
id_num = int(1)

# ページの初期値
page = 1

# グルナビの一覧ページのURLを指定
mainurl = "https://r.gnavi.co.jp/area/jp/kods00066/rs/"

# スクレイピングするページ数を設定
items =50

# タイムアウト時間を設定（秒）
timeout_duration = 5

while id_num < items:
    # ページのURLを指定
    url = mainurl + "?p=" + str(page)

    # iページを開く
    driver.get(url)
    driver.execute_script("return document.readyState === 'complete'")
    link_elements = driver.find_elements(
        By.CLASS_NAME, "style_titleLink__oiHVJ")
    link_text_list = [link.get_attribute("href") for link in link_elements]

    # 各店舗の情報を取得
    for link in link_text_list:
        driver.set_page_load_timeout(timeout_duration)
        if id_num > items:
            break
        try:
            driver.get(link)

            # 読み込みが遅く店舗情報が上手く取得できない場合は以下で待ち時間を設定
            # driver.implicitly_wait(3)

            # SSL情報を取得
            is_ssl_enabled = check_ssl(link)

            # 店舗情報を取得
            name = driver.find_element(By.ID, "info-name").text
            phone = driver.find_element(By.CLASS_NAME, "number").text
            address = driver.find_element(By.CLASS_NAME, "region").text

            try:
                # 建物名が格納されている'locality'タグがあるとき
                building = driver.find_element(By.CLASS_NAME, 'locality').text
            except NoSuchElementException:
                building = ""

            # 都道府県、市区町村、番地の正規表現パターン
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
            pass  # 例外が発生したとき

    page += 1

# ブラウザを閉じる
driver.quit()

# CSVファイルにデータフレームを保存
df.to_csv('restaurant_info.csv', index=False)
