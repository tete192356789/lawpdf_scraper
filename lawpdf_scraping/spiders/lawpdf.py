import scrapy
from playwright.async_api import async_playwright
from scrapy_playwright.page import PageMethod

from lawpdf_scraping.items import LawpdfScrapingItem


class LawpdfSpider(scrapy.Spider):
    name = "lawpdf"
    allowed_domains = ["ratchakitcha.soc.go.th"]
    start_urls = ["https://ratchakitcha.soc.go.th/search-result#result"]
    current_page = 1
    page_limit = 10

    def __init__(self):
        self.thai_to_arabic = {
            "๐": "0",
            "๑": "1",
            "๒": "2",
            "๓": "3",
            "๔": "4",
            "๕": "5",
            "๖": "6",
            "๗": "7",
            "๘": "8",
            "๙": "9",
        }

    def thai_num_to_arabic(self, thai_num_str):
        arabic_num_str = "".join(
            self.thai_to_arabic.get(char, char) for char in thai_num_str
        )
        return arabic_num_str

    def start_requests(self):
        url = "https://ratchakitcha.soc.go.th/search-result#result"

        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod(
                        "wait_for_selector",
                        "div.col-lg-8.no-padding div.announce100.m-b-0.p-b-20.m-t-5 div.post-thumbnail-list.p-b-40 div.post-thumbnail-entry.blogBox.moreBox",
                    )
                ],
                errback=self.errback,
            ),
        )

    async def parse(self, response):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False
            )  # Set headless=True for background execution
            page = await browser.new_page()
            await page.goto(response.url)

            # Handle pagination (adjust selectors as needed)
            while self.current_page <= self.page_limit:
                for blog in response.css(
                    "div.col-lg-8.no-padding div.announce100.m-b-0.p-b-20.m-t-5 div.post-thumbnail-list.p-b-40 div.post-thumbnail-entry.blogBox.moreBox"
                ):
                    item = LawpdfScrapingItem()

                    name = blog.css("div.post-thumbnail-content a.m-b-10 ::text").get()
                    post_date = blog.css(
                        "div.post-thumbnail-content div.m-t-10 span.post-date ::text"
                    ).get()
                    post_category = blog.css(
                        "div.post-thumbnail-content div.m-t-10 span.post-category  ::text"
                    ).get()
                    file_urls = blog.css(
                        "div.post-thumbnail-content  a.m-b-10 ::attr(href)"
                    ).get()

                    item["name"] = name
                    item["post_date"] = post_date
                    item["post_category"] = post_category
                    item["file_urls"] = file_urls
                    yield item

                # Click "Next" button if available (adjust selector)
                next_button = await page.query_selector(
                    "xpath=//div[@class='announce100 m-b-0 p-b-20 m-t-5']/div[@class='row pull-right p-b-20']/ul[@class='page-numbers pagination pagination-flat']/li[@class='page-item current']/following-sibling::li[1]"
                )
                if next_button:
                    await next_button.click()
                    await page.wait_for_timeout(
                        2000
                    )  # Adjust wait time if needed for page load

                    content = await page.content()

                    response = scrapy.http.HtmlResponse(
                        url=page.url, body=content, encoding="utf-8"
                    )
                else:
                    break

                self.current_page += 1

            await browser.close()

        # page = response.meta["playwright_page"]
        # page_num = 1

        # while page_num < 3:
        # for blog in response.css(
        #     "div.col-lg-8.no-padding div.announce100.m-b-0.p-b-20.m-t-5 div.post-thumbnail-list.p-b-40 div.post-thumbnail-entry.blogBox.moreBox"
        # ):
        #     item = LawpdfScrapingItem()

        #     name = blog.css("div.post-thumbnail-content a.m-b-10 ::text").get()
        #     post_date = blog.css(
        #         "div.post-thumbnail-content div.m-t-10 span.post-date ::text"
        #     ).get()
        #     post_category = blog.css(
        #         "div.post-thumbnail-content div.m-t-10 span.post-category  ::text"
        #     ).get()
        #     file_urls = blog.css(
        #         "div.post-thumbnail-content  a.m-b-10 ::attr(href)"
        #     ).get()

        #     item["name"] = name
        #     item["post_date"] = post_date
        #     item["post_category"] = post_category
        #     item["file_urls"] = file_urls
        #     yield item

        #     next_button = await page.query_selector_all(
        #         "xpath=//div[@class='announce100 m-b-0 p-b-20 m-t-5']/div[@class='row pull-right p-b-20']/ul[@class='page-numbers pagination pagination-flat']/li[@class='page-item current']/following-sibling::li[1]"
        #     )

        #     if next_button:
        #         self.logger.info(f"Clicking next button to go to page {page_num + 1}")
        #         await next_button[0].click()
        #         # await page.wait_for_load_state("networkidle")

        #         await page.wait_for_selector(
        #             "div.col-lg-8.no-padding div.announce100.m-b-0.p-b-20.m-t-5 div.post-thumbnail-list.p-b-40 div.post-thumbnail-entry.blogBox.moreBox"
        #         )

        #         page_num += 1
        #         content = await page.content()

        #         response = scrapy.http.HtmlResponse(
        #             url=page.url, body=content, encoding="utf-8"
        #         )

        #     else:
        #         self.logger.info("No next button found. Ending pagination.")
        #         break
        # await page.close()

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
