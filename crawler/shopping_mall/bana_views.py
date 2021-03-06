from django.utils import timezone
from crawler.models import *
from urllib.request import urlopen
from urllib import error
from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError, MaxRetryError
from bs4 import BeautifulSoup
import time


def bana_tab_list_provider(main_url):
    tab_list = []
    html = urlopen(main_url)
    source = BeautifulSoup(html, 'html.parser')
    for a in source.find_all('div', {"class": "topMenu"}):
        for url in a.find_all('a'):
            if url['href'].startswith('/shop/goods/goods_list.php?&category'):
                if not url['href'].startswith('/shop/goods/goods_list.php?&category=018') or \
                        url['href'].startswith('/shop/goods/goods_list.php?&category=031') or \
                        url['href'].startswith('/shop/goods/goods_list.php?&category=0280') or \
                        url['href'].startswith('/shop/goods/goods_list.php?&category=0200'):
                    tab_list.append(main_url + url['href'])
    return tab_list


def bana_page_list_provider(tab_list):
    page_num_list = []
    page_list = []
    for i in range(len(tab_list)):
        html = urlopen(tab_list[i])
        source = BeautifulSoup(html, 'html.parser')
        for a in source.find_all('div', {"class": "nav"}):
            for b in a.find_all('span', {"class": "link"}):
                page_num_list.append(b.get_text())
        last_pag_num = page_num_list[-1]
        for j in range(int(last_pag_num)):
            page_list.append(tab_list[i] + '&page=' + str(j+1))
    page_list = sorted(page_list)
    return page_list


def bana_product_list_provider(main_url, page_list):
    product_list = []
    for i in range(len(page_list)):
        is_best = 0
        if page_list[i].startswith('http://www.banabanamall.com/shop/goods/goods_list.php?category=022'):
            is_best = 1
        html = urlopen(page_list[i])
        source = BeautifulSoup(html, 'html.parser')
        for a in source.find_all('div', {"class": 'container'}):
            for b in a.find_all('div', {"class": "img"}):
                for url in b.find_all('a'):
                    product_list.append([main_url + '/shop/' + url['href'][2:], is_best])
    # remove_list = []
    # for i in range(len(product_list)):
    #     for j in range(len(product_list)-i-1):
    #         if product_list[i][0] == product_list[i+j+1][0]:
    #             remove_list.append(i)
    #
    # count = 0
    # for i in range(len(remove_list)):
    #     del product_list[remove_list[i] - count]
    #     count = count + 1
    return product_list


# def bana_update_database(product_list):
#     queryset = Product.objects.filter(shopping_mall=4)
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


def bana_info_crawler(product_list):
    all_info_list = []
    for i in range(len(product_list)):
        info_list = []
        try:
            # Best ???????????? ???????????? ?????? ?????? ??????
            is_best = False
            if product_list[i][1] == 1:
                is_best = True
            info_list.append(is_best)

            html = urlopen(product_list[i][0])
            source = BeautifulSoup(html, 'html.parser')

            # ?????? url ??????
            info_list.append(product_list[i][0])

            # ?????? ?????? ????????????
            a = source.find('table', {"class": "goods_spec"})
            price = a.find('font', {"id": "price"})
            info_list.append(price.get_text())

            # ?????? ?????? ???????????? (????????? ????????? ???????????? ????????? ?????????!)
            # ?????? ????????? ?????? if ????????? ??????
            color_list = []
            if source.find_all('select', {"name": "opt[]"}):
                for colortab in source.find_all('select', {"name": "opt[]"}):
                    for color in colortab.find_all('option'):
                        color_list.append(color.get_text().replace('\n', '').replace('\r', '').replace('\t', '').replace(' ',''))
            else:
                for a in source.find_all('div', {"class": "left"}):
                    for b in a.find_all('div', {"class": "bold w24 goodsnm"}):
                        name = b.get_text()
                        color = name.split()[-1]
                        color_list.append(color)

            color_list = [s for s in color_list if '??????' not in s]
            color_list = list(set(color_list))
            info_list.append(color_list)

            # ?????? ?????? ?????? ????????? ???????????? ?????? ????????? ?????? filtering
            on_sale = True
            for a in source.find_all(('div', {"class": "left"})):
                for b in a.find_all('table', {"class": "goods_spec"}):
                    for sale in b.find_all('b'):
                        if '??????' in sale.get_text():
                            on_sale = False
            info_list.append(on_sale)

            # ????????? / ????????? ?????? ??????
            is_mono = True
            if len(color_list) > 1:
                is_mono = False
            info_list.append(is_mono)

            # ????????? source html ?????? ????????????
            new_html = 'http://www.banabanamall.com/shop//goods/goods_popup_large.php?' + product_list[i][0].split('?')[-1]
            html = urlopen(new_html)
            source_in = BeautifulSoup(html, 'html.parser')
            for a in source_in.find_all('img', {"id": "objImg"}):
                info_list.append('http://www.banabanamall.com/shop/' + a['src'][2:])

            # ???????????? ?????? ?????? ??????
            info_list.append(timezone.now())

            # ?????? ?????? ?????? ??????
            for a in source.find_all('div', {"class": "left"}):
                for b in a.find_all('div', {"class": "bold w24 goodsnm"}):
                    name = b.get_text()
                    info_list.append(name)

            # ?????? ?????? ??????
            all_info_list.append(info_list)

            # ?????? ???????????? ?????? 10s ??? ??????
            time.sleep(10)
        except (ConnectionResetError, error.URLError, error.HTTPError, ConnectionRefusedError, ConnectionError, NewConnectionError, MaxRetryError):
            print("Connection Error")
    print(all_info_list)
    return all_info_list


# bag image url??? ???????????? ?????? product ???????????? best ?????? ?????????
def bana_update_product_list(all_info_list):
    remove_list = []
    for i in range(len(all_info_list)-1):
        for j in range(len(all_info_list)-i-1):
            if all_info_list[i][6] == all_info_list[i+j+1][6]:
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
def bana_update_database(all_info_list):
    queryset = BagImage.objects.filter(product__shopping_mall=4)
    if queryset.count() == 0:
        pass
    else:
        origin_list = []
        new_crawled_list = []
        for i in range(len(all_info_list)):
            new_crawled_list.append(all_info_list[i][6])
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
def bana_make_model_table(all_info_list):
    for i in range(len(all_info_list)):
        p, _ = Product.objects.update_or_create(shopping_mall=4, product_name=all_info_list[i][8],
                                                defaults={'bag_url': all_info_list[i][1],
                                                          'is_best': all_info_list[i][0], 'price': all_info_list[i][2]})

        img, _ = BagImage.objects.update_or_create(product=p, defaults={'image_url': all_info_list[i][6]})
        for j in range(len(all_info_list[i][3])):
            q, _ = ColorTab.objects.update_or_create(product=p, colors=all_info_list[i][3][j],
                                                     defaults={'is_mono': all_info_list[i][5], 'on_sale': all_info_list[i][4]})
            colortab_list = []
            colortab_list.append(q.colors)
            for k in range(len(colortab_list)):
                colortag_list = []
                if any(c in colortab_list[k] for c in ('??????', '??????', '??????', '?????????', '??????')):
                    colortag_list.append(1)
                if any(c in colortab_list[k] for c in ('??????', '??????', '??????', '??????', '?????????')):
                    colortag_list.append(2)
                if any(c in colortab_list[k] for c in ('?????????', '???', '?????????')):
                    colortag_list.append(3)
                if any(c in colortab_list[k] for c in ('??????', '????????????', '??????', '??????', '??????')):
                    colortag_list.append(4)
                if any(c in colortab_list[k] for c in ('?????????', '???????????????', '?????????', '?????????')):
                    colortag_list.append(5)
                if any(c in colortab_list[k] for c in ('???', '??????', '??????', '?????????', '??????', '??????')):
                    colortag_list.append(6)
                if any(c in colortab_list[k] for c in ('??????', '?????????', '????????????', '??????', '???', '??????', '??????', '??????', '?????????')):
                    colortag_list.append(7)
                if any(c in colortab_list[k] for c in ('?????????', '?????????', '??????')):
                    colortag_list.append(8)
                if any(c in colortab_list[k] for c in ('??????', '??????', '?????????', '?????????', '?????????', '????????????')):
                    colortag_list.append(9)
                if any(c in colortab_list[k] for c in ('??????', '??????', '??????', '??????', '?????????', '??????', '?????????', '???', '??????', '?????????', '??????', '????????????', '?????????')):
                    colortag_list.append(10)
                if any(c in colortab_list[k] for c in ('??????', '??????')):
                    colortag_list.append(11)
                if any(c in colortab_list[k] for c in ('????????????', '??????', '?????????', '??????', '??????')):
                    colortag_list.append(12)
                if any(c in colortab_list[k] for c in ('??????', '??????', '?????????', '??????')):
                    colortag_list.append(13)
                if any(c in colortab_list[k] for c in ('????????????', '??????', '??????', '??????', '??????')):
                    colortag_list.append(99)
                if len(colortag_list) == 0:
                    colortag_list.append(0)

                print(colortag_list)
                for m in range(len(colortag_list)):
                    ColorTag.objects.update_or_create(colortab=q, color=colortag_list[m],
                                                      defaults={'color': colortag_list[m]})
