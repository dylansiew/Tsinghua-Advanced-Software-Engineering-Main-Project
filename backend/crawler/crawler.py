from dotenv import load_dotenv
import os
import asyncio
import json
from urllib.parse import quote_plus
from typing import List, Dict, Any, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from ProductList import ProductList
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class EcommerceRecommender:
    def __init__(self, search_engines=None, captcha_key: Optional[str] = None):
        load_dotenv()
        self.search_engines = search_engines or [
            {
                "name": "Amazon", 
                "url": "https://www.amazon.com/s?k=",
                "config": {
                    "wait_for": "div.s-result-item",
                    "js": """
                        // Random scroll behavior
                        for (let i = 0; i < 5; i++) {
                            window.scrollBy(0, Math.floor(Math.random() * 300) + 100);
                            await new Promise(r => setTimeout(r, Math.floor(Math.random() * 1000) + 500));
                        }
                        
                        // Move mouse randomly (when not in headless)
                        if (document.createEvent) {
                            for (let i = 0; i < 3; i++) {
                                const evt = document.createEvent('MouseEvents');
                                const x = Math.floor(Math.random() * window.innerWidth);
                                const y = Math.floor(Math.random() * window.innerHeight);
                                evt.initMouseEvent('mousemove', true, true, window, 0, 0, 0, x, y, false, false, false, false, 0, null);
                                document.dispatchEvent(evt);
                                await new Promise(r => setTimeout(r, Math.floor(Math.random() * 500) + 200));
                            }
                        }
                    """
                }
            }
        ]

        instructions = """Extract product listings from the search results. For each product, extract:
            - product_name (text)
            - price (with currency)
            - rating (out of 5 if available)
            - reviews (count if available)
            - url (product page)
            - seller (if available)
            Return as a JSON array."""
            
        product_schema = ProductList.model_json_schema()

        self.llm_strategy = LLMExtractionStrategy(
            llm_config = LLMConfig(provider="openai/gpt-o3-mini", api_token=os.getenv('OPENAI_API_KEY')),
            instruction=instructions,
            schema=None, #product_schema
            extraction_type="schema",
            chunk_token_threshold=100,
            overlap_rate=0.0,
            apply_chunking=True,
            input_format="html", # or "markdown", "fit_markdown"
            extra_args={"temperature": 0.0, "max_tokens": 10000}
        )

        # Explicitly set extraction strategy in config
        self.crawl_config = CrawlerRunConfig(
            extraction_strategy=self.llm_strategy,
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            magic=True,
            simulate_user=True
        )
        
        self.browser_config = BrowserConfig(
            headless=True,
            use_managed_browser=True,
            use_persistent_context=True,
            user_data_dir=None,
            browser_type="chromium",
            proxy=None
        )
        
    def generate_search_urls(self, query: str) -> List[str]:
        """Generate search URLs for each search engine."""
        return [engine["url"] + quote_plus(query) for engine in self.search_engines]
    
    async def crawl_site(self, url: str, engine_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            async with AsyncWebCrawler(
                verbose=True,
                proxy=None,
                config=self.browser_config
            ) as crawler:
                products = await self._try_llm_extraction(crawler, url, engine_config)
                if products and len(products) > 0:
                    print(f"LLM extraction successful for {engine_config['name']}, found {len(products)} products")
                    return self._add_source(products, engine_config["name"])
                else:
                    print(f"No products extracted for {engine_config['name']}")
                    return []
        except Exception as e:
            print(f"Failed to initialize crawler for {engine_config['name']}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    async def _try_llm_extraction(self, crawler, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            print(f"Starting LLM extraction for {url}")
            
            result = await crawler.arun(
                config=self.crawl_config,
                url=url,
                js_code=config["config"].get("js", ""),
                extraction_strategy=self.llm_strategy,  # Explicitly pass the strategy
                wait_for=config["config"].get("wait_for", 5),
                wait_timeout=300000,
                bypass_cache=True,
                magic=True,
                simulate_user=True
            )

            if result and result.html:
                soup = BeautifulSoup(result.html, "html.parser")
                search_items = soup.select("div.s-result-item[data-asin]:not([data-asin=''])")[:10]

            products = []
            for item in search_items:
                product_name = item.find('h2', class_='a-size-base-plus a-spacing-none a-color-base a-text-normal').get_text(strip=True)
                price = item.select_one(".a-price .a-price-whole").get_text(strip=True) if item.select_one(".a-price .a-price-whole") else "N/A"
                rating = item.select_one(".a-icon-alt").get_text(strip=True) if item.select_one(".a-icon-alt") else "N/A"
                reviews = item.select_one(".a-size-base").get_text(strip=True) if item.select_one(".a-size-base") else "N/A"
                url = "https://www.amazon.com" + item.select_one("h2 a.a-text-normal")["href"] if item.select_one("h2 a.a-text-normal") else "N/A"
                
                product = {
                    "product_name": product_name,
                    "price": price,
                    "rating": rating,
                    "reviews": reviews,
                    "url": url
                }
                products.append(product)

            return products
        
        except Exception as e:
            print(f"LLM extraction failed: {str(e)}")
            import traceback
            print(traceback.format_exc())
        return []

    async def crawl_for_products(self, query: str) -> List[Dict[str, Any]]:
        """Crawl all configured e-commerce sites for products matching the query."""
        search_urls = self.generate_search_urls(query)
        
        all_products = []
        
        tasks = []
        for i, url in enumerate(search_urls):
            engine_config = self.search_engines[i]
            task = self.crawl_site(url, engine_config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"Error in crawl task: {result}")
                continue
            all_products.extend(result)
        
        print(f"Found {len(all_products)} products")
        return all_products

    def _add_source(self, products: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
        """Add source information to products."""
        if isinstance(products, list):
            for product in products:
                if isinstance(product, dict):
                    product['source'] = source
            return products
        return []

async def main():
    recommender = EcommerceRecommender()
    
    user_query = input("What are you looking to buy? ")
    
    # Generate and display results
    products = await recommender.crawl_for_products(user_query)
    
    if products:
        print(f"\nFound {len(products)} products:")
        for i, product in enumerate(products[:10], 1):  # Show the first 10 products
            print(f"\n{i}. {product.get('product_name', 'No name')}")
            print(f"   Price: {product.get('price', 'N/A')}")
            print(f"   Rating: {product.get('rating', 'N/A')}")
            print(f"   Source: {product.get('source', 'N/A')}")
    else:
        print("\nNo products found. Try a different search term.")

if __name__ == "__main__":
    asyncio.run(main())