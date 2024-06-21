import scrapy
from scrapy_playwright.page import PageMethod

from lawpdf_scraping.items import LawpdfScrapingItem


class LawpdfSpider(scrapy.Spider):
    name = "lawpdf"
    # allowed_domains = ["library.coj.go.th"]
    # start_urls = [
    #     "https://library.coj.go.th/th/constitution-database.html?keyword=&option=all"
    # ]

    def start_requests(self):
        url = "https://library.coj.go.th/th/constitution-database.html?keyword=&option=all"

        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods={
                    "wait_for_selector": PageMethod(
                        "wait_for_selector", "ul.list-page.home-list-news.mt-4 span"
                    ),
                    "click": PageMethod(
                        "click",
                        ".paging button.btn-purple.last",
                    ), 
                },
                errback=self.errback,
            ),
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        await page.close()

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

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
