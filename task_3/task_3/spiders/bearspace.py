import scrapy
import requests
from ..items import ArtworkItem
import re
import logging


class ArtworkSpider(scrapy.Spider):
    """
    Parses the www.bearspace.co.uk for the artworks available for purchase.
    The straightforward (and probably more correct) way of finding links to artworks would be starting from
    https://www.bearspace.co.uk/purchase, but i hoped that there is an api from which i could get all the necessary info
    There is an ugly https://www.bearspace.co.uk/_api/wix-ecommerce-storefront-web API, that provides the list of
    artworks, but it doesnt contain dimensions or media. I decided to continue with it anyway, maybe it will show that
    i can look into those broken APIs, so maybe its not so crucial for a test task. Could as well go for the sitemap
    spider.
    """
    name = "available_artworks"
    api_url_part_1 = 'https://www.bearspace.co.uk/_api/wix-ecommerce-storefront-web/api?o=getFilteredProducts&s=WixStoresWebClient&q=query,getFilteredProducts($mainCollectionId:String!,$filters:ProductFilters,$sort:ProductSort,$offset:Int,$limit:Int,$withOptions:Boolean,=,false,$withPriceRange:Boolean,=,false){catalog{category(categoryId:$mainCollectionId){numOfProducts,productsWithMetaData(filters:$filters,limit:$limit,sort:$sort,offset:$offset,onlyVisible:true){totalCount,list{id,options{id,key,title,@include(if:$withOptions),optionType,@include(if:$withOptions),selections,@include(if:$withOptions){id,value,description,key,linkedMediaItems{url,fullUrl,thumbnailFullUrl:fullUrl(width:50,height:50),mediaType,width,height,index,title,videoFiles{url,width,height,format,quality}}}}productItems,@include(if:$withOptions){id,optionsSelections,price,formattedPrice,formattedComparePrice,availableForPreOrder,inventory{status,quantity}isVisible,pricePerUnit,formattedPricePerUnit}customTextFields(limit:1){title}productType,ribbon,price,comparePrice,sku,isInStock,urlPart,formattedComparePrice,formattedPrice,pricePerUnit,formattedPricePerUnit,pricePerUnitData{baseQuantity,baseMeasurementUnit}itemDiscount{discountRuleName,priceAfterDiscount}digitalProductFileItems{fileType}name,media{url,index,width,mediaType,altText,title,height}isManageProductItems,productItemsPreOrderAvailability,isTrackingInventory,inventory{status,quantity,availableForPreOrder,preOrderInfoView{limit}}subscriptionPlans{list{id,visible}}priceRange(withSubscriptionPriceRange:true),@include(if:$withPriceRange){fromPriceFormatted}discount{mode,value}}}}}}&v=%7B%22mainCollectionId%22%3A%2200000000-000000-000000-000000000001%22%2C%22offset%22%3A'
    api_url_part_2 = '0%2C%22limit%22%3A20%2C%22sort%22%3Anull%2C%22filters%22%3Anull%2C%22withOptions%22%3Afalse%2C%22withPriceRange%22%3Afalse%7D'
    re_single_dimension = re.compile(r"[\d]+[.]*[,]*[ ]*[\d]*\/*[\d]*")
    base_url = 'https://www.bearspace.co.uk'

    def start_requests(self):
        # this url seems to contain auth tokens for something, and the one with id 1744 happens to be for listing the artworks
        auth_data = requests.get(r"https://www.bearspace.co.uk/_api/v2/dynamicmodel").json()['apps']
        auth_token = ''
        for v in auth_data:
            if auth_data[v]['intId'] == 1744:
                auth_token = auth_data[v]['instance']

        headers = {
            'Referer': 'https://www.bearspace.co.uk/_partials/wix-thunderbolt/dist/clientWorker.5252fea2.bundle.min.js',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Authorization': auth_token,
            'Content-Type': 'application/json; charset=utf-8',
        }
        i = 1
        urls = [
            # i guess it can be done with an f string, but the need to escape the curly braces breaks something in the request
            self.api_url_part_1 + f'{i}' + self.api_url_part_2]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_api_request, headers=headers, meta={'offset': i})

    def parse_api_request(self, response):
        data = response.json()

        # request next batch of artworks
        if data["data"]["catalog"]["category"]["productsWithMetaData"]["list"]:
            url = self.api_url_part_1 \
                  + f'{response.meta["offset"] + 1}' + \
                  self.api_url_part_2
            yield scrapy.Request(url=url, callback=self.parse_api_request, headers=response.request.headers,
                                 meta={'offset': response.meta['offset'] + 1})

        # parse artwork list
        for v in data["data"]["catalog"]["category"]["productsWithMetaData"]["list"]:
            if v['isInStock']:
                item = ArtworkItem()
                item['price_gbp'] = v['price']
                item['title'] = v['name']
                yield scrapy.Request(url=f'{self.base_url}/product-page/{v["urlPart"]}',
                                     callback=self.parse_product_page, meta={'item': item, })

    def parse_product_page(self, response):
        item = response.meta['item']
        description_lines = response.xpath('//pre[@data-hook="description"]/p//text()').getall()
        #TODO should cover cases where pre[@data-hook="description"] doesnt contain p tags for example
        # https://www.bearspace.co.uk/product-page/gcs-high-rise-jane-ward
        dims_found = False
        media_found = False
        # The description format doesnt have a constant structure. Sometimes dimensions come before media,
        # sometimes there isnt a media, Sometimes description is not devided into HTML tags (for example
        # https://www.bearspace.co.uk/product-page/gcs-high-rise-jane-ward
        # I tried to cover 2 cases, depending on whether media or dimensions come first.
        # it comes with a sacrifice of "media" containing unnecessary information if it comes after dimension,
        # since its unknown where the media text stops, and i think i saw media being split into multiple <p> tags.
        # So depending on the requirements and post-processing that we do we can either choose risk of loosing
        # some words from the media or haivng extra data there.
        # For example https://www.bearspace.co.uk/product-page/crossroads-by-olly-fathers
        # if it was more of a production env, maybe i would add some post processing or re-crawling of links where
        # data seems to be incorrect, build a dictionary of key word or stop-words to understand where the media
        # lays in unstructured text. Not sure how deep should i go into the scraped data quality in a test task.
        for l in description_lines:
            # From what i've seen dmensions always start with a number in a separate <p> tag
            if l[0].isdigit() and not dims_found:
                dims = self.re_single_dimension.findall(l)
                for i, d in enumerate(dims):
                    d = float(d.replace(',', '.'))
                    if d >= 2000 and len(dims) == 1:
                        logging.warning('Seems like we found a year instead of dimension. Skipping dimension search')
                        break
                    if i > 1:
                        break
                    if i == 0:
                        item['height_cm'] = d
                    elif i == 1:
                        item['width_cm'] = d
                    dims_found = True
                    if 'media' in item and item['media']:
                        media_found = True
            elif not media_found:
                item['media'] = (item.get('media', '') + ' ' + l).strip()

        item['url'] = response.url
        return item
