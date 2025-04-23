import asyncio

from crawl4ai import AsyncWebCrawler


async def simple_crawl():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://www.nbcnews.com/business")
        print(result.markdown[:500])  

async def main():
    await simple_crawl()

if __name__ == "__main__":
    asyncio.run(main())