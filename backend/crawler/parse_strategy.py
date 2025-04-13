# --- START OF FILE crawler.py ---

from dotenv import load_dotenv
import os
import asyncio
import json
from urllib.parse import quote_plus
from typing import List, Dict, Any, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
# from playwright.sync_api import sync_playwright # Not used directly here

class EcommerceRecommender:
    def __init__(self, search_engines=None, captcha_key: Optional[str] = None):
        load_dotenv()
        self.search_engines = search_engines or [
            {
                "name": "Amazon",
                "url": "https://www.amazon.com/s?k=",
                "config": {
                    "wait_for": "div.s-result-item", # Helps ensure results grid starts loading
                     "js": """
                        // Random scroll behavior (keep for potential anti-bot)
                        for (let i = 0; i < 3; i++) { // Reduced scrolls
                            window.scrollBy(0, Math.floor(Math.random() * 400) + 200);
                            await new Promise(r => setTimeout(r, Math.floor(Math.random() * 700) + 300));
                        }
                     """
                }
            },
            {
                "name": "AliExpress",
                "url": "https://www.aliexpress.com/wholesale?SearchText=",
                "config": {
                    "wait_for": "a.search-card-item", # Try waiting for the card link itself
                    "js": """
                       // Random scroll behavior (keep for potential anti-bot)
                       for (let i = 0; i < 3; i++) { // Reduced scrolls
                           window.scrollBy(0, Math.floor(Math.random() * 400) + 200);
                           await new Promise(r => setTimeout(r, Math.floor(Math.random() * 700) + 300));
                       }
                    """
                }
            }
        ]
        self.crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            magic=True,
            simulate_user=True
        )

        self.browser_config = BrowserConfig(
            headless=True,
            use_managed_browser=True,
            use_persistent_context=False, # Set to False initially
            user_data_dir=None,
            browser_type="chromium",
            proxy=None,
        )

    def generate_search_urls(self, query: str) -> List[str]:
        """Generate search URLs for each search engine."""
        return [engine["url"] + quote_plus(query) for engine in self.search_engines]

    def _parse_amazon_bs(self, html_content: str) -> list[dict]:
        """Parses Amazon search results HTML using BeautifulSoup."""
        soup = BeautifulSoup(html_content, "html.parser")
        products = []
        # Limit to first 10 results for example
        search_items = soup.select("div.s-result-item[data-asin]:not([data-asin=''])")[:10]
        print(f"[Amazon Parser] Found {len(search_items)} potential items.")

        for item in search_items:
            product_name = "N/A"
            price = "N/A"
            rating = "N/A"
            reviews = "N/A"
            url = "N/A"
            seller = "N/A" # Seller info is harder to get reliably from Amazon search results page

            try:
                product_name = item.find('h2', class_='a-size-base-plus a-spacing-none a-color-base a-text-normal').get_text(strip=True)

                # Price
                price_tag = item.select_one(".a-price")
                if price_tag:
                    whole = price_tag.select_one(".a-price-whole")
                    fraction = price_tag.select_one(".a-price-fraction")
                    symbol = price_tag.select_one(".a-price-symbol")
                    if whole and fraction:
                         price_str = f"{whole.get_text(strip=True).rstrip('.')}."\
                                     f"{fraction.get_text(strip=True)}"
                         if symbol:
                             price = f"{symbol.get_text(strip=True)}{price_str}"
                         else:
                             price = price_str # Assuming dollars if symbol missing
                    else:
                         # Sometimes price is in a different span, e.g., .a-offscreen
                         offscreen_price = price_tag.select_one("span.a-offscreen")
                         if offscreen_price:
                             price = offscreen_price.get_text(strip=True)

                # Rating
                rating_tag = item.select_one("i.a-icon-star-small") # Select the star icon container
                if rating_tag:
                    rating_text_tag = rating_tag.select_one("span.a-icon-alt")
                    if rating_text_tag:
                        rating = rating_text_tag.get_text(strip=True)


                # Reviews Count
                reviews_tag = item.select_one("span.a-size-base") # Often the reviews count is here
                if reviews_tag:
                     # Check if the text contains digits, as this class is used elsewhere
                     text = reviews_tag.get_text(strip=True).replace(',', '') # Remove commas for isdigit
                     if text.isdigit():
                           reviews = reviews_tag.get_text(strip=True) # Keep original format with comma


                # URL
                url_tag = item.select_one("a.a-link-normal.s-no-outline")
                if url_tag and url_tag.has_attr('href'):
                    href = url_tag['href']
                    if href.startswith('/'):
                        url = "https://www.amazon.com" + href
                    else:
                         url = href # Should ideally resolve relative URLs if needed

                product = {
                    "product_name": product_name,
                    "price": price,
                    "rating": rating,
                    "reviews": reviews,
                    "url": url,
                    "seller": seller # Still N/A for Amazon search page
                }
                products.append(product)

            except Exception as e:
                print(f"Error parsing Amazon item: {e}")
                # Optional: append placeholder or log more details
                # import traceback; print(traceback.format_exc())

        return products

    def _parse_aliexpress_bs(self, html_content: str) -> list[dict]:
        """Parses AliExpress search results HTML using BeautifulSoup."""
        soup = BeautifulSoup(html_content, "html.parser")
        products = []
        # Limit to first 10 results for example
        search_items = soup.select("a.search-card-item")[:10]
        print(f"[AliExpress Parser] Found {len(search_items)} potential items.")

        for item in search_items:
            product_name = "N/A"
            price = "N/A"
            rating = "N/A"
            reviews = "N/A" # AliExpress often shows "sold" count instead of reviews count here
            url = "N/A"
            seller = "N/A"

            try:
                # Product Name
                name_tag = item.select_one("h3.kc_j0")
                if name_tag:
                    product_name = name_tag.get_text(strip=True)

                # Price
                price_tag = item.select_one("div.kc_k1")
                if price_tag:
                    price = price_tag.get_text(separator='', strip=True)
                    price = ' '.join(price.split()) # Basic cleanup

                # Rating & Reviews/Sales Count (Combined logic as they are in same div)
                rating_spans = item.select("div.kc_j7 span.kc_jv")
                if rating_spans:
                     # Check first span for rating
                     potential_rating = rating_spans[0].get_text(strip=True)
                     # Basic check if it looks like a rating number (e.g., "4.7", "4,7")
                     if potential_rating.replace(',', '').replace('.', '', 1).isdigit():
                         rating = potential_rating
                     # Check last span for sales count
                     if len(rating_spans) > 0:
                         sales_text = rating_spans[-1].get_text(strip=True)
                         if "vendidos" in sales_text.lower() or "sold" in sales_text.lower() or "ventes" in sales_text.lower():
                              reviews = sales_text # Keep the full text like "1.000+ vendidos"
                         # If rating wasn't found in first span, maybe it's in the last one? (Less likely)
                         elif rating == "N/A" and sales_text.replace(',', '').replace('.', '', 1).isdigit():
                              rating = sales_text


                # URL
                href = item.get('href')
                if href:
                    if href.startswith("//"):
                        url = "https:" + href
                    elif href.startswith("/"):
                         url = "https://www.aliexpress.com" + href # Adjust base URL if needed
                    else:
                        url = href

                # Seller
                seller_tag = item.select_one("span.io_ip a.io_ir")
                if seller_tag:
                    seller = seller_tag.get_text(strip=True)

                product = {
                    "product_name": product_name,
                    "price": price,
                    "rating": rating,
                    "reviews": reviews, # Note: Likely sales count
                    "url": url,
                    "seller": seller
                }
                products.append(product)

            except Exception as e:
                print(f"Error parsing AliExpress item: {e}")
                # Optional: append placeholder or log more details
                # import traceback; print(traceback.format_exc())

        return products

    async def _parse_site_html(self, crawler, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetches HTML using the crawler and parses it using site-specific BS logic."""
        products = []
        engine_name = config["name"]
        try:
            print(f"\n--- Fetching HTML for {engine_name} ---")
            print(f"URL: {url}")

            result = await crawler.arun(
                url=url,
                js_code=config["config"].get("js", ""),
                wait_for=config["config"].get("wait_for", "body"), # Updated wait_for
                wait_timeout=60000, # Increased timeout (60 seconds)
                bypass_cache=self.crawl_config.cache_mode == CacheMode.BYPASS,
                magic=self.crawl_config.magic,
                simulate_user=self.crawl_config.simulate_user
            )

            if result and result.html:
                print(f"Successfully fetched HTML for {engine_name} (Length: {len(result.html)}).")
                print(f"Parsing HTML using BeautifulSoup for {engine_name}...")

                # --- Site-Specific Parsing ---
                if engine_name == "Amazon":
                    # save HTML for debugging Amazon selectors
                    # with open("amazon_results.html", "w", encoding="utf-8") as f:
                    #     f.write(result.html)
                    products = self._parse_amazon_bs(result.html)
                elif engine_name == "AliExpress":
                     # Save HTML for debugging AliExpress selectors
                     with open("search_results.html", "w", encoding="utf-8") as f:
                        f.write(result.html)
                     print("Saved AliExpress HTML to search_results.html")
                     products = self._parse_aliexpress_bs(result.html)
                else:
                    print(f"Warning: No BeautifulSoup parser defined for engine: {engine_name}")

                print(f"Parsed {len(products)} products for {engine_name}.")

            elif result and not result.html:
                 print(f"Crawler ran for {engine_name} but returned no HTML content.")
            else:
                 print(f"Crawler returned no result object for {engine_name}.")

        except asyncio.TimeoutError:
            print(f"Error: Timeout occurred during crawl for {engine_name} at {url}")
        except Exception as e:
            print(f"Error during HTML fetching or parsing for {engine_name}: {str(e)}")
            import traceback
            print(traceback.format_exc())

        print(f"--- Finished processing for {engine_name}, returning {len(products)} products ---")
        return products

    async def crawl_site(self, url: str, engine_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawls a single site and extracts products using BeautifulSoup."""
        engine_name = engine_config["name"]
        try:
            async with AsyncWebCrawler(
                verbose=True,
                proxy=self.browser_config.proxy,
                config=self.browser_config
            ) as crawler:
                # Call the refactored parsing method
                products = await self._parse_site_html(crawler, url, engine_config)
                if products:
                    # print(f"Extraction successful for {engine_name}, found {len(products)} products") # Already printed in _parse_site_html
                    return self._add_source(products, engine_name)
                else:
                    print(f"No products extracted via parsing for {engine_name}")
                    return []
        except Exception as e:
            print(f"Failed to initialize or run crawler for {engine_name}: {str(e)}")
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
            task = asyncio.create_task(self.crawl_site(url, engine_config))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                print(f"Error occurred in a crawl task: {result}")
                # Optionally log the full traceback if needed
                # import traceback
                # print(traceback.format_exc())
            elif isinstance(result, list):
                all_products.extend(result)
            else:
                print(f"Warning: Unexpected result type from gather: {type(result)}")


        print(f"\nTotal products found across all sites: {len(all_products)}")
        return all_products

    def _add_source(self, products: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
        """Add source information to products."""
        if isinstance(products, list):
            for product in products:
                if isinstance(product, dict):
                    product['source'] = source
        return products

async def main():
    recommender = EcommerceRecommender()
    user_query = input("What are you looking to buy? ")

    print(f"\nSearching for '{user_query}' on {[e['name'] for e in recommender.search_engines]}...")
    products = await recommender.crawl_for_products(user_query)

    if products:
        print(f"\n--- Top {min(len(products), 10)} Results ---")
        for i, product in enumerate(products[:20], 1):
            print(f"\n{i}. {product.get('product_name', 'N/A')}")
            print(f"   Source: {product.get('source', 'N/A')}")
            print(f"   Price: {product.get('price', 'N/A')}")
            print(f"   Rating: {product.get('rating', 'N/A')}")
            print(f"   Reviews/Sold: {product.get('reviews', 'N/A')}") # Clarified label
            print(f"   Seller: {product.get('seller', 'N/A')}")
             # Ensure URL is treated as string for printing if it's a Pydantic HttpUrl (less likely now)
            url = product.get('url')
            print(f"   URL: {str(url) if url else 'N/A'}")
    else:
        print("\nNo products found matching your query. Try refining your search.")

if __name__ == "__main__":
    asyncio.run(main())

# --- END OF FILE crawler.py ---