# import modules
from lxml import html
import re
import requests
import pandas as pd
from datetime import datetime


def get_number_from_string(s):
    p = '[\d]+[.,\d]+|[\d]*[.][\d]+|[\d]+'
    r = []
    if re.search(p, s) is not None:
        for catch in re.finditer(p, s):
            r.append(int(catch[0].replace(',','')))
    return r if len(r)>1 else r[0]


if __name__ == '__main__':
    # get html and tree
    result_df = pd.DataFrame(columns=["ArtistName", "PaintingName", "PriceGBP", "PriceUSD", "EstimatesGBP",
                                      "EstimatesUSD", "ImageURL", "SaleDate"])
    html_page_link = '../candidateEvalData/webpage.html'
    page = html.parse(html_page_link)
    result_df["PaintingName"] = [page.xpath('//meta[@name="og:description"]/@content')[0]]
    result_df["PriceGBP"] = [
        get_number_from_string(page.xpath("//span[contains(@id, 'PriceRealizedPrimary')]/text()")[0])]
    result_df["PriceUSD"] = [
        get_number_from_string(page.xpath("//div[contains(@id, 'PriceRealizedSecondary')]/text()")[0])]
    result_df["EstimatesGBP"] = [
        get_number_from_string(page.xpath("//span[contains(@id, 'PriceEstimatedPrimary')]/text()")[0])]
    result_df["EstimatesUSD"] = [get_number_from_string(
        page.xpath("//span[contains(@id, 'PriceEstimatedSecondary')]/text()")[0].strip('(').strip(')'))]
    result_df["ImageURL"] = [page.xpath('//img[@id="imgLotImage"]/@src')[0]]
    sale_date = page.xpath("//span[contains(@id, 'SaleDate')]/text()")[0]
    result_df["SaleDate"] = [str(datetime.strptime(sale_date.strip().strip(','), '%d %B %Y').date())]
    result_df["ArtistName"] = [page.xpath('//h1[@class="lotName"]/text()')[0].split('(')[0].strip()]
    for i in result_df.columns:
        try:
            result_df[i] = result_df[i].map(str.strip)
        except TypeError:
            pass
    result_df.to_csv('out.csv')
