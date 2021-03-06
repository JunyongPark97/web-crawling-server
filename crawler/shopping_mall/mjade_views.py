from django.utils import timezone
from crawler.models import *
from urllib.request import urlopen
from urllib import parse
from urllib import error
from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError, MaxRetryError
from bs4 import BeautifulSoup
import time


def mjade_tab_list_provider(main_url):
    tab_list = []
    html = urlopen(main_url)
    source = BeautifulSoup(html, 'html.parser')
    for a in source.find_all('div', {"id": "sp-category-1-normal"}):
        for b in a.find_all('li', {"class": "nohave xans-record-"}):
            for url in b.find_all('a'):
                if url['href'].startswith('/product'):
                    tab_list.append(main_url + url['href'])
    return tab_list


def mjade_page_list_provider(tab_list):
    page_list = []
    for i in range(len(tab_list)):
        html = urlopen(tab_list[i])
        source = BeautifulSoup(html, 'html.parser')
        for a in source.find_all('div', {"layout": "sp-layout-fixed"}):
            for b in a.find_all('ul', {"class": "sp-pagination-arrow sp-right"}):
                for url in b.find_all('a', {"class": "last"}):
                    last_pag_num = 1
                    if url['href'].split('=')[-1] != '#none':
                        last_pag_num = url['href'].split('=')[-1]
                    for j in range(int(last_pag_num)):
                        page_list.append(tab_list[i] + '&page=' + str(j+1))
    page_list = sorted(list(set(page_list)))
    return page_list


def mjade_product_list_provider(main_url, page_list):
    product_list = []
    for i in range(len(page_list)):
        is_best = 0
        if page_list[i].startswith('https://mjade.co.kr/product/list.html?cate_no=145'):
            is_best = 1
        html = urlopen(page_list[i])
        source = BeautifulSoup(html, 'html.parser')
        for a in source.find_all('div', {"class": "sp-product-box"}):
            for b in a.find_all('div', {"class": "sp-product-item-thumb"}):
                for url in b.find_all('a', {"class": "sp-product-item-thumb-href"}):
                    if url['href'].startswith('/product'):
                        product_list.append([main_url + parse.quote(url['href']), is_best])
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


# def mjade_update_database(product_list):
#     queryset = Product.objects.filter(shopping_mall=11)
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


def mjade_info_crawler(product_list):
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
            price_list = []
            for a in source.find_all('div', {"class": "sp-detail-baseinfo"}):
                for b in a.find_all('strong', {"id": "span_product_price_text"}):
                    price = b.get_text()
                    price = price.replace('\n', '').replace('\r', '').replace('\t', '')
                    price_list.append(price)
            price = price_list[0]
            info_list.append(price)

            # ?????? ?????? ????????????
            color_list = []
            for a in source.find_all('div', {"data-title": "??????"}):
                for b in a.find_all('select', {"option_title": "??????"}):
                    for c in b.find_all('optgroup', {"label": "??????"}):
                        for d in c.find_all('option'):
                            color = d.get_text()
                            color_list.append(color)
            color_list = list(set(color_list))
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
            a = source.find('div', {"class": "keyImg"})
            img_source = a.find('div', {"class": "thumbnail"})
            info_list.append('http:' + img_source.find('img', {"class": "BigImage"})['src'])

            # ???????????? ?????? ?????? ??????
            info_list.append(timezone.now())

            # ?????? ?????? ?????? ??????
            for a in source.find_all('div', {"class": "sp-detail-title"}):
                for b in a.find_all('div', {"class": "sp-detail-title-name"}):
                    name = b.get_text()
                    name = name.replace('\n', '').replace('\r', '').replace('\t', '')
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
def mjade_update_product_list(all_info_list):
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
def mjade_update_database(all_info_list):
    queryset = BagImage.objects.filter(product__shopping_mall=11)
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
def mjade_make_model_table(all_info_list):
    for i in range(len(all_info_list)):
        p, _ = Product.objects.update_or_create(shopping_mall=11, product_name=all_info_list[i][8],
                                                defaults={'bag_url': all_info_list[i][1],
                                                          'is_best': all_info_list[i][0], 'price': all_info_list[i][2]})

        img, _ = BagImage.objects.update_or_create(product=p, defaults={'image_url': all_info_list[i][6]})

        for j in range(len(all_info_list[i][3])):
            q, _ = ColorTab.objects.update_or_create(product=p, colors=all_info_list[i][3][j],
                                                     defaults={'is_mono': all_info_list[i][5], 'on_sale': all_info_list[i][4][j]})
            colortab_list = []
            colortab_list.append(q.colors)
            for k in range(len(colortab_list)):
                colortag_list = []
                if any(c in colortab_list[k] for c in ('??????', '??????', '??????', '?????????', '??????')):
                    colortag_list.append(1)
                if any(c in colortab_list[k] for c in ('??????', '??????', '??????', '??????')):
                    colortag_list.append(2)
                if any(c in colortab_list[k] for c in ('?????????', '???')):
                    colortag_list.append(3)
                if any(c in colortab_list[k] for c in ('??????', '????????????', '??????', '??????', '??????')):
                    colortag_list.append(4)
                if any(c in colortab_list[k] for c in ('?????????', '???????????????', '?????????')):
                    colortag_list.append(5)
                if any(c in colortab_list[k] for c in ('???', '??????', '??????', '?????????', '??????', '??????')):
                    colortag_list.append(6)
                if any(c in colortab_list[k] for c in ('??????', '?????????', '????????????', '??????', '???', '??????', '??????', '??????')):
                    colortag_list.append(7)
                if any(c in colortab_list[k] for c in ('?????????', '?????????', '??????')):
                    colortag_list.append(8)
                if any(c in colortab_list[k] for c in ('????????????', '??????', '??????', '?????????', '?????????')):
                    colortag_list.append(9)
                if any(c in colortab_list[k] for c in ('??????', '??????', '??????', '??????', '??????', '?????????', '??????', '?????????', '???', '??????', '?????????', '??????', '????????????', '?????????')):
                    colortag_list.append(10)
                if any(c in colortab_list[k] for c in ('??????', '??????')):
                    colortag_list.append(11)
                if any(c in colortab_list[k] for c in ('????????????', '??????', '?????????', '??????', '??????')):
                    colortag_list.append(12)
                if any(c in colortab_list[k] for c in ('??????', '??????', '?????????', '??????')):
                    colortag_list.append(13)
                if any(c in colortab_list[k] for c in ('??????', '??????', '??????', '?????????', '??????', '?????????')):
                    colortag_list.append(99)
                if len(colortag_list) == 0:
                    colortag_list.append(0)

                print(colortag_list)
                for m in range(len(colortag_list)):
                    ColorTag.objects.update_or_create(colortab=q, color=colortag_list[m],
                                                      defaults={'color': colortag_list[m]})

