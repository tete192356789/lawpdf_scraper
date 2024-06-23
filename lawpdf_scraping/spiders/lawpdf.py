import scrapy
from scrapy_playwright.page import PageMethod
from playwright.async_api import async_playwright
from lawpdf_scraping.items import LawpdfScrapingItem
import logging
import json

class LawpdfSpider(scrapy.Spider):
    name = "lawpdf"
    # allowed_domains = ["library.coj.go.th"]
    start_urls = [
        "https://library.coj.go.th/th/constitution-database.html?keyword=&option=all"
    ]

    def start_requests(self):
        url = "https://library.coj.go.th/th/constitution-database.html?keyword=&option=all"



        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                        PageMethod('wait_for_selector', "xpath=//div[@class='paging']/button[@class='btn-purple last']/preceding-sibling::button[1]")
                    ],
                errback=self.errback,
            ),
        )
       

      

    async def parse(self, response):
        page = response.meta["playwright_page"]
        # await page.close()
        page_num =1
        while True:
            for blog in response.css(
                "article.col-lg-9.col-md-8.search-detail ul.list-page.home-list-news.mt-4 span"
            ):
                item = LawpdfScrapingItem()

                name = blog.css("li div.container span.font-title a ::text").get()

                inner_spans = blog.css(
                    "li div.container aside.download-list-news.mt-3 span.mr-4"
                )
                if len(inner_spans) < 2:
                    law_type = None
                    release_date = None
                else:
                    law_type = inner_spans[0].css(".mr-4::text").get()
                    release_date = inner_spans[1].css(".mr-4::text").get()

                link = blog.css(
                    "li div.container aside.download-list-news.mt-3 a ::attr(href)"
                ).get()

                if link is not None:
                    item["name"] = name
                    item["link"] = link
                    item["law_type"] = law_type
                    item["release_date"] = release_date
                    yield item
            
            next_button =  await page.query_selector_all("xpath=//div[@class='paging']/button[@class='btn-purple last']/preceding-sibling::button[1]")     
            
            if next_button:
                is_enabled = await next_button[0].is_enabled()
                if is_enabled:
                    self.logger.info(f"Clicking next button to go to page {page_num + 1}")
                    await next_button[0].click()
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_selector("article.col-lg-9.col-md-8.search-detail ul.list-page.home-list-news.mt-4 span")
                    page_num += 1
                    
                    # Update the response object with the new page content
                    content = await page.content()
                    response = scrapy.http.HtmlResponse(url=page.url, body=content, encoding='utf-8')
                else:
                    self.logger.info("Next button is not enabled. Ending pagination.")
                    break
            else:
                self.logger.info("No next button found. Ending pagination.")
                break
        await page.close()


    async def get_next_page_content(self,url):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set headless to False for debugging
            page = await browser.new_page()
            await page.goto(url)
            # Simulate clicking the "Next" button or navigating using element attributes
            next_page_button = await page.wait_for_selector("xpath=//div[@class='paging']/button[@class='btn-purple last']/preceding-sibling::button[1]")  # Replace with actual selector
            await next_page_button.click()
            await page.wait_for_timeout(2000)  # Wait for page to load
            await page.wait_for_selector("article.col-lg-9.col-md-8.search-detail ul.list-page.home-list-news.mt-4 span")
            
            content = await page.content()
            next_url = page.url
            for blog in page.css("article.col-lg-9.col-md-8.search-detail ul.list-page.home-list-news.mt-4 span"):
                item = LawpdfScrapingItem()

                name = blog.css("li div.container span.font-title a ::text").get()

                inner_spans = blog.css(
                    "li div.container aside.download-list-news.mt-3 span.mr-4"
                )
                if len(inner_spans) < 2:
                    law_type = None
                    release_date = None
                else:
                    law_type = inner_spans[0].css(".mr-4::text").get()
                    release_date = inner_spans[1].css(".mr-4::text").get()

                link = blog.css(
                    "li div.container aside.download-list-news.mt-3 a ::attr(href)"
                ).get()

                if link is not None:
                    item["name"] = name
                    item["link"] = link
                    item["law_type"] = law_type
                    item["release_date"] = release_date
                    yield item


            
            await browser.close()
            yield content, next_url

            

    async def parse_content(self, response):
        print('**********')
        print('parse_contenting')

        for blog in response.css(
            "article.col-lg-9.col-md-8.search-detail ul.list-page.home-list-news.mt-4 span"
        ):
            item = LawpdfScrapingItem()

            name = blog.css("li div.container span.font-title a ::text").get()

            inner_spans = blog.css(
                "li div.container aside.download-list-news.mt-3 span.mr-4"
            )
            if len(inner_spans) < 2:
                law_type = None
                release_date = None
            else:
                law_type = inner_spans[0].css(".mr-4::text").get()
                release_date = inner_spans[1].css(".mr-4::text").get()

            link = blog.css(
                "li div.container aside.download-list-news.mt-3 a ::attr(href)"
            ).get()

            if link is not None:
                item["name"] = name
                item["link"] = link
                item["law_type"] = law_type
                item["release_date"] = release_date
                print('****************')
                print('****************')
                print(name)
                print(link)
                print(law_type)
                print(release_date)
                yield item


    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
