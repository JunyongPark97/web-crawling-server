from django.utils import timezone
from crawler.models import *
from urllib.request import urlopen
from urllib import error
from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError, MaxRetryError
from bs4 import BeautifulSoup
import time


def wconcept_tab_list_provider(main_url):
    tab_list = []
    html = urlopen(main_url)
    source = BeautifulSoup(html, 'html.parser')
    for a in source.find_all('div', {"class": "lnb_wrap lnb_depth"}):
        for b in a.find_all('dd'):
            for url in b.find_all('a'):
                if url['href'].startswith('/Women/00400'):
                    tab_list.append('https://www.wconcept.co.kr' + url['href'])
    return tab_list[:4]


def wconcept_page_list_provider(tab_list):
    page_list = []
    for i in range(len(tab_list)):
        html = urlopen(tab_list[i])
        source = BeautifulSoup(html, 'html.parser')
        for a in source.find_all('ul', {"class": "pagination"}):
            last_pag_num = 1
            for b in a.find_all('li', {"class": "last"}):
                for url in b.find_all('a'):
                    if url['href'].split('=')[-1] != '#none':
                        last_pag_num = url['data-page']
                    for j in range(int(last_pag_num)):
                        page_list.append(tab_list[i] + '?page=' + str(j+1))
    page_list = sorted(list(set(page_list)))
    return page_list


def wconcept_product_list_provider(main_url, page_list):
    product_list = []
    for i in range(len(page_list)):
        html = urlopen(page_list[i])
        source = BeautifulSoup(html, 'html.parser')
        for a in source.find_all('div', {"class": "thumbnail_list"}):
            for url in a.find_all('a'):
                if url['href'].startswith('/Product'):
                    product_list.append('https://www.wconcept.co.kr' + url['href'])
    return product_list


# def wconcept_update_database(product_list):
#     queryset = Product.objects.filter(shopping_mall=7)
#     if queryset.count() == 0:
#         pass
#     else:
#         origin_list = []
#         for bag in queryset:
#             origin_list.append(bag.bag_url)
#         for origin in origin_list:
#             if origin not in product_list:
#                 p = Product.objects.get(bag_url=origin)
#                 p.is_valid = False
#                 p.save()


def wconcept_info_crawler(product_list):
    all_info_list = []
    for i in range(len(product_list)):
        info_list = []
        try:
            html = urlopen(product_list[i])
            source = BeautifulSoup(html, 'html.parser')

            # Best ???????????? ???????????? ?????? ?????? ??????
            # is_best = False
            # info_list.append(is_best)

            # ?????? url ??????
            info_list.append(product_list[i])

            # ?????? ?????? ????????????
            price_list = []
            for a in source.find_all('div', {"class": "price_wrap"}):
                for b in a.find_all('dd', {"class": "sale"}):
                    for c in b.find_all('em'):
                        price = c.get_text()
                        price = price.replace('\n', '').replace('\r', '').replace('\t', '')
                        price_list.append(price)
            price = price_list[0]
            info_list.append(price)

            # ?????? ?????? ????????????
            color_list = []
            for a_1 in source.find_all('div', {"class": "select-list-selected"}):
                for b_1 in a_1.find_all('ul', {"class": "select-list"}):
                    for color in b_1.find_all('a', {"class" : "select-list-link"}):
                        color_list.append(color.get_text())
            # for a_2 in source.find_all('div', {"class": "h_group"}):
            #     for b_2 in a_2.find_all('h3', {"class": "product"}):
            #         name = b_2.get_text()
            #         if '-' in name:
            #             color_list.append("".join(name).split('-')[-3:-1])
            #         elif '[' in name:
            #             left_index = name.index('[')
            #             right_index = name.index(']')
            #             if right_index - left_index < 6:
            #                 color_list.append(name[left_index+1:right_index])
            #         else:
            #             color_list.append("".join(name).split(' ')[-1])
            color_list = [s for s in color_list if 'ONE' not in s]
            color_list = [s for s in color_list if '??????' not in s]
            color_list = [s for s in color_list if 'chain' not in s]
            color_list = [s for s in color_list if 'FREE' not in s]
            color_list = sorted(list(set(color_list)))
            info_list.append(color_list)

            # ?????? ?????? ?????? ????????? ???????????? ?????? ????????? ?????? filtering
            on_sale_list = []
            for color in color_list:
                on_sale = True
                if "??????" in color:
                    on_sale = False
                on_sale_list.append(on_sale)
            info_list.append(on_sale_list)

            # ????????? / ????????? ?????? ??????
            is_mono = True
            if len(color_list) > 1:
                is_mono = False
            info_list.append(is_mono)

            # ????????? source html ?????? ????????????
            a = source.find('div', {"class": "img_goods"})
            img_source = a.find('div', {"class": "img_area"})
            info_list.append('https:' + img_source.find('img')['src'])

            # ???????????? ?????? ?????? ??????
            info_list.append(timezone.now())

            # ?????? ?????? ?????? ??????
            name_list = []
            for a_1 in source.find_all('div', {"class": "h_group"}):
                for b in a_1.find_all('h3', {"class": "product"}):
                    name = b.get_text()
                    name_list.append(name)
            info_list.append(name_list[0])

            # ?????? ?????? ??????
            all_info_list.append(info_list)

            # ?????? ???????????? ?????? 10s ??? ??????
            time.sleep(10)
        except (ConnectionResetError, error.URLError, error.HTTPError, ConnectionRefusedError, ConnectionError, NewConnectionError, MaxRetryError):
            print("Connection Error")
    print(all_info_list)
    return all_info_list


# bag image url??? ???????????? ?????? product ???????????? best ?????? ?????????
def wconcept_update_product_list(all_info_list):
    remove_list = []
    for i in range(len(all_info_list)-1):
        for j in range(len(all_info_list)-i-1):
            if all_info_list[i][5] == all_info_list[i+j+1][5]:
                if all_info_list[i][0] == 0:
                    remove_list.append(i)
                else:
                    remove_list.append(i+j+1)
    remove_list = sorted(list(set(remove_list)))
    count = 0
    for i in range(len(remove_list)):
        del all_info_list[remove_list[i] - count]
        count = count + 1

    return all_info_list


# update database by using bag image url
def wconcept_update_database(all_info_list):
    queryset = BagImage.objects.filter(product__shopping_mall=7)
    if queryset.count() == 0:
        pass
    else:
        origin_list = []
        new_crawled_list = []
        for i in range(len(all_info_list)):
            new_crawled_list.append(all_info_list[i][5])
        for bag in queryset:
            origin_list.append(bag.image_url)
        for origin in origin_list:
            if origin not in new_crawled_list:
                p = Product.objects.filter(bag_image__image_url=origin).first()
                p.is_valid = False
                p.save()
            else:
                p = Product.objects.filter(bag_image__image_url=origin).first()
                p.is_valid = True
                p.save()


# model table ??? ????????????
def wconcept_make_model_table(all_info_list):
    for i in range(len(all_info_list)):
        p, _ = Product.objects.update_or_create(shopping_mall=7, product_name=all_info_list[i][7],
                                                defaults={'bag_url': all_info_list[i][0], 'price': all_info_list[i][1]})

        img, _ = BagImage.objects.update_or_create(product=p, defaults={'image_url': all_info_list[i][5]})

        if len(all_info_list[i][2]):
            for j in range(len(all_info_list[i][2])):
                q, _ = ColorTab.objects.update_or_create(product=p, colors=all_info_list[i][2][j],
                                                         defaults={'is_mono': all_info_list[i][4], 'on_sale': all_info_list[i][3][j]})
                colortab_list = []
                colortab_list.append(q.colors)
                for k in range(len(colortab_list)):
                    colortag_list = []
                    if any(c in colortab_list[k] for c in ('??????', 'Burgundy', 'BURGUNDY', 'cherrypink', 'Grapefruit', 'Red', 'RED', 'red')):
                        colortag_list.append(1)
                    if any(c in colortab_list[k] for c in ('magenta', 'Pink', 'Rosegold', 'PINK', 'pink', 'CORAL')):
                        colortag_list.append(2)
                    if any(c in colortab_list[k] for c in ('Orange', 'ORANGE', 'orange')):
                        colortag_list.append(3)
                    if any(c in colortab_list[k] for c in ('Lemon', 'LEMON', 'mustard', 'Gold', 'GOLD', 'YELLOW')):
                        colortag_list.append(4)
                    if any(c in colortab_list[k] for c in ('beige', 'BEIGE', 'Beige')):
                        colortag_list.append(5)
                    if any(c in colortab_list[k] for c in ('melon', 'PISTACHIO', 'GREEN', '??????', 'OLIVE', 'Green', 'green', 'mint', 'neon')):
                        colortag_list.append(6)
                    if any(c in colortab_list[k] for c in ('??????', 'Mint', 'BLUE', 'blue')):
                        colortag_list.append(7)
                    if any(c in colortab_list[k] for c in ('navy', 'Navy', 'NAVY')):
                        colortag_list.append(8)
                    if any(c in colortab_list[k] for c in ('mauve', 'purple', 'Lavender', 'PURPLE', 'IRIS', 'WINE', '??????')):
                        colortag_list.append(9)
                    if any(c in colortab_list[k] for c in ('?????????', 'caramel', 'Tan', 'MUSHROOM', 'ETOFFE', 'brown', 'Brown', 'BROWN')):
                        colortag_list.append(10)
                    if any(c in colortab_list[k] for c in ('BLACK', 'Black', 'black', '??????')):
                        colortag_list.append(11)
                    if any(c in colortab_list[k] for c in ('cream', 'CREAM', 'white', 'ivory', 'Ivory', 'IVORY', 'WHITE', '?????????', '????????????')):
                        colortag_list.append(12)
                    if any(c in colortab_list[k] for c in ('Silver', 'GRAY', 'grey', 'gray', 'GREY', '?????????')):
                        colortag_list.append(13)
                    if any(c in colortab_list[k] for c in ('multiple', 'MULTIPLE')):
                        colortag_list.append(99)
                    if len(colortag_list) == 0:
                        colortag_list.append(0)

                    print(colortag_list)
                    for m in range(len(colortag_list)):
                        ColorTag.objects.update_or_create(colortab=q, defaults={'color': colortag_list[m]})
        else:
            q, _ = ColorTab.objects.update_or_create(product=p,
                                                     defaults={'is_mono': all_info_list[i][4],
                                                               'on_sale': 1})

            ColorTag.objects.update_or_create(colortab=q, defaults={'color': 0})

