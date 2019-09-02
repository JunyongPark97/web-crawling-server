from django.utils import timezone
from crawler.models import *
from urllib.request import urlopen
from bs4 import BeautifulSoup
import time


def jade_tab_list_provider(main_url):
    tab_list = []
    html = urlopen(main_url)
    source = BeautifulSoup(html, 'html.parser')
    for a in source.find_all('div', {"class": "nav"}):
        for b in a.find_all('li', {"class": "cateMenu"}):
            for url in b.find_all('a'):
                if url['href'].startswith('/shop/shopbrand.html?xcode'):
                    tab_list.append(main_url + url['href'])
    return tab_list


# page 1개씩 밖에 없기 때문에 tab_list와 page_list는 동일
# 추후 변경 가능성 있음

def jade_page_list_provider(tab_list):
    page_list = []
    for i in range(len(tab_list)):
        page_list.append(tab_list[i])
    return page_list


def jade_product_list_provider(main_url, page_list):
    product_list = []
    for i in range(len(page_list)):
        html = urlopen(page_list[i])
        source = BeautifulSoup(html, 'html.parser')
        for a in source.find_all('div', {"class": 'item-list'}):
            for b in a.find_all('dt', {"class": "thumb"}):
                for url in b.find_all('a'):
                    product_list.append(main_url + url['href'])
    product_list = list(set(product_list))
    return product_list[:5]


def jade_info_crawler(product_list):
    all_info_list = []
    for i in range(len(product_list)):
        info_list = []
        # TODO : best 상품인지 아닌지 현재로써는 모름
        # Best 상품인지 아닌지에 대한 정보 담기
        is_best = False
        if product_list[i].startswith('http://www.jadebag.co.kr/shop/shopbrand.html?xcode=003&type=O'):
            is_best = True
        info_list.append(is_best)

        html = urlopen(product_list[i])
        source = BeautifulSoup(html, 'html.parser')

        # 가방 url 담기
        info_list.append(product_list[i])

        # 가격 정보 추출하기
        a = source.find('div', {"class": "table-opt"})
        price = a.find('span', {"id": "pricevalue"})
        info_list.append(price.get_text())

        # 색상 정보 추출하기
        color_list = []
        for a in source.find_all('div', {"class": "table-opt"}):
            for b in a.find_all('select', {"id": "MK_p_s_0"}):
                for c in b.find_all('option'):
                    color_list.append(c.get_text())
        color_list = [s for s in color_list if '옵션' not in s]

        info_list.append(color_list)

        # 현재 상품 판매 중인지 아닌지에 대한 정보를 통해 filtering
        on_sale_list = []
        for color in color_list:
            on_sale = True
            if "품절" in color:
                on_sale = False
            on_sale_list.append(on_sale)
        info_list.append(on_sale_list)

        # 단일색 / 중복색 정보 담기
        is_mono = True
        if len(color_list) > 1:
            is_mono = False
        info_list.append(is_mono)

        # 이미지 source html 정보 추출하기
        a = source.find('div', {"class": "thumb"})
        info_list.append('http://www.jadebag.co.kr' + a.find('img')['src'])

        # 크롤링된 시간 정보 담기
        info_list.append(timezone.now())

        # 상품 이름 정보 담기
        for a in source.find_all('div', {"class": "info"}):
            for b in a.find_all('div', {"class": "dname"}):
                name = b.find('h3').get_text()
                info_list.append(name)

        # 모든 정보 담기
        all_info_list.append(info_list)

        # 서버 과부하를 위해 10s 간 멈춤
        time.sleep(10)

    print(all_info_list)
    return all_info_list


# model table 에 집어넣기
def jade_make_model_table(all_info_list):
    for i in range(len(all_info_list)):
        p, _ = Product.objects.get_or_create(shopping_mall=3, image_url=all_info_list[i][6], product_name=all_info_list[i][8],
                                             bag_url=all_info_list[i][1], is_best=all_info_list[i][0], price=all_info_list[i][2],
                                             crawled_date=all_info_list[i][7])
        # p = Product.objects.get(pk=i+1)
        for j in range(len(all_info_list[i][3])):
            q, _ = ColorTab.objects.update_or_create(product=p, is_mono=all_info_list[i][5], on_sale=all_info_list[i][4][j],
                                                     colors=all_info_list[i][3][j])
            colortab_list = []
            colortab_list.append(q.colors)
            for k in range(len(colortab_list)):
                colortag_list = []
                print(colortab_list[k])
                if any(c in colortab_list[k] for c in ('레드', '와인', '브릭', '버건디', '빨강')):
                    colortag_list.append(1)
                elif any(c in colortab_list[k] for c in ('살구', '코랄', '핑크')):
                    colortag_list.append(2)
                elif any(c in colortab_list[k] for c in ('오렌지', '귤')):
                    colortag_list.append(3)
                elif any(c in colortab_list[k] for c in ('골드', '머스타드', '노란', '노랑', '옐로')):
                    colortag_list.append(4)
                elif any(c in colortab_list[k] for c in ('베이지', '타프베이지', '코코아')):
                    colortag_list.append(5)
                elif any(c in colortab_list[k] for c in ('녹', '그린', '카키', '타프', '올리브', '라임', '비취')):
                    colortag_list.append(6)
                elif any(c in colortab_list[k] for c in ('아쿠아', '세레니티', '블루', '청', '민트', '청록', '하늘')):
                    colortag_list.append(7)
                elif any(c in colortab_list[k] for c in ('네이비', '진파랑', '곤색')):
                    colortag_list.append(8)
                elif any(c in colortab_list[k] for c in ('보라', '퍼플', '보르도', '보로도')):
                    colortag_list.append(9)
                elif any(c in colortab_list[k] for c in ('에땅', '머드', '에토프', '밤색', '브라운', '탄', '카멜', '캬라멜', '모카', '탑브라운', '초콜렛')):
                    colortag_list.append(10)
                elif any(c in colortab_list[k] for c in ('블랙', '검정')):
                    colortag_list.append(11)
                elif any(c in colortab_list[k] for c in ('아이보리', '아이', '화이트', '크림', '하얀')):
                    colortag_list.append(12)
                elif any(c in colortab_list[k] for c in ('실버', '회색', '그레이', '차콜')):
                    colortag_list.append(13)
                elif any(c in colortab_list[k] for c in ('멀티', '다중', '뱀피', '지브라', '호피')):
                    colortag_list.append(99)
                else:
                    colortag_list.append(0)

                print(colortag_list)
                for m in range(len(colortag_list)):
                    ColorTag.objects.update_or_create(colortab=q, color=colortag_list[m])

