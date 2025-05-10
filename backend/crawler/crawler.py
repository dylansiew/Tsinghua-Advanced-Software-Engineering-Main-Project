import asyncio
import json
import os
import re
import traceback
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup, Tag
from crawl4ai import (AsyncWebCrawler, BrowserConfig, CacheMode,
                      CrawlerRunConfig)
from dotenv import load_dotenv


# --- Helper function to extract text with fallbacks ---
def _extract_text(item_soup: Tag, selectors: List[str], default: str = "N/A") -> str:
    """Tries multiple selectors to extract text, returning the first found."""
    for selector in selectors:
        try:
            element = item_soup.select_one(selector)
            if element:
                # Extract text from all children, handling nested tags
                text = element.get_text(separator=' ', strip=True)
                if text:
                    return ' '.join(text.split()) # Normalize whitespace
        except Exception:
            # print(f"Selector failed: {selector}") # Debugging
            continue # Ignore errors with a specific selector and try the next
    return default

# --- Helper function to extract attributes with fallbacks ---
def _extract_attribute(item_soup: Tag, selectors: List[str], attribute: str, base_url: Optional[str] = None, default: str = "N/A") -> str:
    """Tries multiple selectors to extract an attribute, returning the first found."""
    for selector in selectors:
        try:
            element = item_soup.select_one(selector)
            if element and element.has_attr(attribute):
                value = element[attribute].strip()
                if value:
                    # If it's a URL and a base_url is provided, make it absolute
                    if attribute == 'href' and base_url:
                        try:
                            # Handle cases like //example.com/path -> https://example.com/path
                            if value.startswith("//"):
                                scheme = base_url.split('://')[0]
                                value = scheme + ":" + value
                            # Handle cases where it might already be absolute but lacks scheme
                            if value.startswith("://"):
                                scheme = base_url.split('://')[0]
                                value = scheme + value
                            # Ensure base_url ends with / for proper joining of relative paths
                            if not base_url.endswith('/'):
                                base_url += '/'
                            return urljoin(base_url, value)
                        except ValueError:
                            # print(f"Warning: Could not construct absolute URL from base '{base_url}' and relative '{value}'")
                            return value # Keep original if join fails
                    return value
        except Exception:
            # print(f"Selector failed: {selector}") # Debugging
            continue # Ignore errors with a specific selector and try the next
    return default

class EcommerceRecommender:
    def __init__(self, search_engines=None, captcha_key: Optional[str] = None):
        load_dotenv()
        # OpenAI client removed as we are focusing on BS4 parsing
        # self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        # if not self.openai_api_key:
        #     raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        # self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)

        self.search_engines = search_engines or [
            {
                "name": "Amazon",
                "url": "https://www.amazon.com/s?k=",
                "base_url": "https://www.amazon.com",
                "item_selector": "div.s-result-item[data-asin]:not([data-asin=''])",
                "config": {
                    "wait_for": "div.s-result-item[data-asin]",
                    "js": """ /* Optional scroll JS */ """
                }
            },
            {
                "name": "AliExpress",
                "url": "https://www.aliexpress.com/wholesale?SearchText=",
                "base_url": "https://www.aliexpress.com",
                "item_selector": "a.search-card-item", # Main container link for each item
                "config": {
                     # Wait for elements likely containing key info
                    "wait_for": "a.search-card-item div[class*='price'], a.search-card-item h3",
                    "js": """ /* Optional scroll JS */ """
                }
            }
        ]
        self.crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            magic=True, # Keep magic, might help clean up minor inconsistencies
            simulate_user=True
        )

        self.browser_config = BrowserConfig(
            headless=True,
            use_managed_browser=True,
            use_persistent_context=False,
            user_data_dir=None,
            browser_type="chromium",
            proxy=None,
        )

    def generate_search_urls(self, query: str) -> List[str]:
        """Generate search URLs for each search engine."""
        return [engine["url"] + quote_plus(query) for engine in self.search_engines]

    def _parse_amazon_bs(self, html_content: str, base_url: str) -> list[dict]:
        """Parses Amazon search results HTML using BeautifulSoup with robust selectors."""
        soup = BeautifulSoup(html_content, "html.parser")
        products = []
        search_items = soup.select("div.s-result-item[data-asin]:not([data-asin=''])")[:10]
        print(f"[Amazon Parser] Found {len(search_items)} potential items using selector.")

        for item in search_items:
            product = {
                "product_name": "N/A",
                "price": "N/A",
                "rating": "N/A",
                "reviews": "N/A",
                "url": "N/A",
                "seller": "N/A",
                "source_method": "BeautifulSoup Selectors"
            }
            try:
                product_name = "N/A"
                title_container = item.select_one('div[data-cy="title-recipe"]')

                if title_container:
                    main_link = title_container.select_one('h2 a.a-link-normal')
                    if main_link:
                            product_name = main_link.get_text(separator=' ', strip=True)
                            # Basic cleanup: Remove the brand if it's duplicated at the start
                            brand_h2_outer = title_container.select_one('h2.a-size-mini span.a-size-medium')
                            if brand_h2_outer:
                                brand_text = brand_h2_outer.get_text(strip=True)
                                if product_name.startswith(brand_text):
                                    product_name = product_name[len(brand_text):].strip()

                    descriptive_h2 = title_container.select_one('h2.a-size-medium.a-color-base.a-text-normal')

                    if product_name == "N/A" and descriptive_h2:
                        # 1a. Try the direct span inside this H2 (often doesn't have extra classes)
                        title_span = descriptive_h2.select_one('span:not([class])') # Prefer span without class if available
                        if not title_span:
                             title_span = descriptive_h2.select_one('span') # Fallback to any span inside

                        if title_span:
                            product_name = title_span.get_text(separator=' ', strip=True)
                        else:
                            # 1b. If no span, get text of the H2 itself
                            product_name = descriptive_h2.get_text(separator=' ', strip=True)

                        # 1c. Check aria-label as a potential override if name is short/bad
                        if descriptive_h2.has_attr('aria-label') and (product_name == "N/A" or len(product_name) < 20):
                             aria_label_name = descriptive_h2['aria-label'].strip()
                             if len(aria_label_name) > len(product_name) + 5 or product_name == "N/A":
                                 product_name = aria_label_name
                                 
                if product_name == "N/A" or len(product_name) < 5: # Also check if name is suspiciously short
                    product_name = _extract_text(item, ['h2']) # Broadest fallback for H2 text

                # Final check: If we *only* got the brand name, reset to N/A as it's likely wrong
                if product_name != "N/A":
                     brand_check_h2 = item.select_one('h2.a-size-mini span.a-size-medium')
                     if brand_check_h2 and brand_check_h2.get_text(strip=True) == product_name:
                         # Only the brand name was likely captured, which is incorrect.
                         product_name = "N/A"

                product['product_name'] = ' '.join(product_name.split()) if product_name != "N/A" else "N/A"

                price_text = "N/A"
                price_text = _extract_text(item, ['.a-price span.a-offscreen'])

                if price_text == "N/A" or not re.search(r'\d', price_text):
                    potential_price_text = _extract_text(item, ['.a-price'])
                    if potential_price_text != "N/A" and re.search(r'[\$£€¥\d]', potential_price_text):
                        price_text = potential_price_text
                    elif price_text == "N/A":
                         secondary_offer_text = _extract_text(item, ['div[data-cy="secondary-offer-recipe"] span.a-color-base'])
                         if secondary_offer_text != "N/A" and re.search(r'[\$£€¥][\d,.]+', secondary_offer_text):
                              price_text = secondary_offer_text


                if price_text == "N/A" or not re.search(r'\d', price_text):
                    whole = _extract_text(item, ['.a-price span.a-price-whole'])
                    fraction = _extract_text(item, ['.a-price span.a-price-fraction'])
                    symbol = _extract_text(item, ['.a-price span.a-price-symbol'])
                    if whole != "N/A" and fraction != "N/A" and re.search(r'\d', whole) and re.search(r'\d', fraction):
                        price_str = f"{whole.rstrip('.').replace(',','')}.{fraction}"
                        currency_symbol = symbol if symbol != "N/A" else '$'
                        price_text = f"{currency_symbol}{price_str}"
                    else:
                        price_text = "N/A"

                if price_text != "N/A":
                    price_text_cleaned = re.sub(r'(List Price:|Range:|From|sponsored|\(.*\soffers\))', '', price_text, flags=re.IGNORECASE).strip()
                    match = re.search(r'([$£€¥]?)\s*([\d,]+\.?\d*)', price_text_cleaned)
                    if match:
                        symbol, number_str = match.groups()
                        symbol = symbol or '$'
                        number_str = number_str.replace(',', '')
                        try:
                            float_price = float(number_str)
                            product['price'] = f"{symbol}{float_price:.2f}"
                        except ValueError:
                             product['price'] = price_text_cleaned if price_text_cleaned else "N/A"
                    else:
                         if price_text_cleaned and not re.fullmatch(r'[$£€¥\s]+', price_text_cleaned):
                             product['price'] = price_text_cleaned
                         else:
                             product['price'] = "N/A"
                else:
                    product['price'] = "N/A"


                # --- Rating Fallbacks (Keep as before) ---
                product['rating'] = _extract_text(item, ['i.a-icon-star-small span.a-icon-alt'])
                if product['rating'] == "N/A":
                    rating_aria_tag = item.select_one('span[aria-label*="out of 5 stars"]')
                    if rating_aria_tag:
                        product['rating'] = rating_aria_tag.get('aria-label', "N/A").strip()

                # --- Reviews Count Fallbacks (Keep cleaned logic & formatting) ---
                reviews_link_text = _extract_text(item, ['a[href*="#customerReviews"] span.a-size-base'])
                reviews_num_str = "N/A"
                if reviews_link_text != "N/A":
                     cleaned_reviews = re.sub(r'[^\d]', '', reviews_link_text)
                     if cleaned_reviews.isdigit():
                         reviews_num_str = cleaned_reviews
                if reviews_num_str == "N/A":
                    fallback_reviews = _extract_text(item, ['#acrCustomerReviewText'])
                    if fallback_reviews != "N/A":
                         cleaned_reviews = re.sub(r'[^\d]', '', fallback_reviews)
                         if cleaned_reviews.isdigit():
                             reviews_num_str = cleaned_reviews
                try:
                    if reviews_num_str != "N/A" and reviews_num_str.isdigit():
                        product['reviews'] = f"{int(reviews_num_str):,}"
                    else:
                         product['reviews'] = reviews_num_str
                except ValueError:
                    product['reviews'] = reviews_num_str


                # --- URL Fallbacks --- (Keep as before)
                product['url'] = _extract_attribute(item, [
                    'h2 a.a-link-normal',
                    'a.s-product-image-container a.a-link-normal',
                    'a.a-link-normal.s-no-outline',
                    'a.a-link-normal',
                ], 'href', base_url)

                # Only append if we got *some* meaningful data (e.g., a name or URL)
                if product['product_name'] != "N/A" or product['url'] != "N/A":
                    products.append(product)
                else:
                    print(f"Skipping item, insufficient data extracted: {item.get('data-asin', 'NO ASIN')}")


            except Exception as e:
                print(f"Error parsing Amazon item: {e} - ASIN: {item.get('data-asin', 'NO ASIN')}")
                # print(traceback.format_exc()) # Keep commented unless debugging deeply

        return products
    
    def _parse_aliexpress_bs(self, html_content: str, base_url: str) -> list[dict]:
        """Parses AliExpress search results HTML using BeautifulSoup."""
        soup = BeautifulSoup(html_content, "html.parser")
        products = []
        search_items = soup.select("div.search-item-card-wrapper-gallery")[:10]
        print(f"[AliExpress Parser] Found {len(search_items)} potential item wrappers using 'div.search-item-card-wrapper-gallery'.")

        if not search_items:
             search_items = soup.select("a.search-card-item")[:10]
             print(f"[AliExpress Parser]: Found {len(search_items)} items using 'a.search-card-item'.")

        for item_wrapper in search_items:
            item = item_wrapper.select_one('a.search-card-item')
            if not item:
                item = item_wrapper

            product = {
                "product_name": "N/A",
                "price": "N/A",
                "rating": "N/A",
                "reviews": "N/A",
                "url": "N/A",
                "seller": "N/A",
                "source_method": "BeautifulSoup Selectors"
            }
            try:
                # product name
                item.find('h2', class_='a-size-base-plus a-spacing-none a-color-base a-text-normal')
                product['product_name'] = _extract_text(item, [
                    'h2[class_="a-size-base-plus a-spacing-none a-color-base a-text-normal"]', 'h3.kc_j0', 'h3[class*="title"]', 'h1[class*="title"]',
                    'div[class*="title--wrap"] > div[class*="title--"]', 'h3',
                ])

                # price
                price_text = "N/A"
                price_selectors = [
                    'div.kc_k1', 'div[class*="price--current"]', 'div[class*="price-sale"]',
                    'div[class*="price"] span[class*="priceTheMaximum"]', 'div[class*="price"]',
                ]
                for selector in price_selectors:
                    price_container = item.select_one(selector)
                    if price_container:
                        # Get text directly from children/spans, joining without extra spaces
                        price_parts = [span.get_text(strip=True) for span in price_container.find_all(recursive=False) if span.get_text(strip=True)]
                        if not price_parts: # Fallback if structure differs
                             price_parts = [t.strip() for t in price_container.find_all(text=True, recursive=True) if t.strip()]

                        if price_parts:
                            raw_price = "".join(price_parts)
                            # Use regex to extract currency symbol and number cleanly
                            match = re.search(r'([€$£¥]?)\s*([\d.,]+)\s*([€$£¥]?)', raw_price.replace(' ', '')) # Remove spaces first
                            if match:
                                 symbol_before, number_str, symbol_after = match.groups()
                                 # Normalize number format (use '.' as decimal separator)
                                 if ',' in number_str and '.' in number_str: # Handle thousands separator e.g., 1.234,56
                                     number_str = number_str.replace('.', '').replace(',', '.')
                                 elif ',' in number_str: # Handle comma decimal e.g., 9,45
                                     number_str = number_str.replace(',', '.')

                                 # Attempt to convert to float for validation/potential calculation
                                 try:
                                     float_price = float(number_str)
                                     # Determine currency symbol (prefer symbol before number)
                                     symbol = symbol_before or symbol_after or '€' # Default to Euro if none found/needed
                                     price_text = f"{symbol}{float_price:.2f}" # Format to 2 decimal places
                                 except ValueError:
                                     price_text = raw_price # Fallback to raw if conversion fails
                            else:
                                price_text = raw_price # Fallback if regex fails
                            break # Found price, exit selector loop
                product['price'] = price_text


                # ratings
                rating_container_selector = 'div.kc_j7'
                rating_text = "N/A"
                reviews_text = "N/A"

                container = item.select_one(rating_container_selector)
                if container:
                    # Rating: Try extracting from star widths
                    star_container = container.select_one('div.kc_k3')
                    if star_container:
                        star_divs = star_container.select('div.kc_k5') # The inner divs with width style
                        total_width = 0
                        star_count = 0
                        max_width_per_star = 10.0 # Assume 10px is a full star based on sample
                        valid_calculation = True
                        if star_divs:
                            star_count = len(star_divs)
                            for star_div in star_divs:
                                style = star_div.get('style')
                                if style:
                                    match = re.search(r'width:\s*([\d.]+)px', style)
                                    if match:
                                        try:
                                            width = float(match.group(1))
                                            total_width += min(width, max_width_per_star) # Add width, capped at max
                                        except ValueError:
                                            valid_calculation = False; break
                                    else: valid_calculation = False; break # Style found but no width?
                                else: valid_calculation = False; break # No style attribute found

                            if valid_calculation and star_count > 0:
                                # Calculate rating: (total filled width / total possible width) * 5 stars
                                calculated_rating = (total_width / (star_count * max_width_per_star)) * 5.0
                                rating_text = f"{calculated_rating:.1f}" # Format to one decimal place
                            #else: rating_text = "N/A (Calc Error)" # Optional: Indicate calculation failed

                    sales_span = container.select_one('span.kc_jv')
                    if sales_span:
                        text = sales_span.get_text(strip=True)
                        # Extract number and descriptive part (like 'vendidos', 'sold', '+')
                        sales_match = re.search(r'([\d.,\+]+)\s*(.*)', text, re.IGNORECASE)
                        if sales_match:
                            reviews_text = sales_match.group(1) + " " + sales_match.group(2).strip()
                        else:
                            reviews_text = text # Fallback to original text

                        # Check if this span contains a numerical rating if stars failed
                        if rating_text == "N/A" and re.match(r"^\d[,.]?\d?$", text.replace(',', '.')):
                             rating_text = text.replace(',', '.')


                product['rating'] = rating_text
                product['reviews'] = reviews_text.strip() # Ensure no trailing spaces


                # url
                item_url = "N/A"
                if item and item.name == 'a' and item.has_attr('href'):
                    value = item['href'].strip()
                    if value:
                        try:
                            if value.startswith("//"): value = base_url.split('://')[0] + ":" + value
                            if value.startswith("://"): value = base_url.split('://')[0] + value
                            if not base_url.endswith('/'): base_url += '/'
                            item_url = urljoin(base_url, value)
                        except ValueError: item_url = value
                if item_url == "N/A":
                     item_url = _extract_attribute(item, [
                         'h3[class*="title"] a', 'h1[class*="title"] a',
                         'a[data-pl*="product_detail"]', 'a[class*="product-item"]', 'a'
                    ], 'href', base_url)
                product['url'] = item_url

                # --- Seller --- (Keep as before)
                product['seller'] = _extract_text(item, [
                    'span.in_io', 'a[href*="/store/"] span',
                    'a[class*="store"]', 'span[class*="store"]'
                ])

                products.append(product)

            except Exception as e:
                print(f"Error parsing AliExpress item: {e}")
                # print(traceback.format_exc())

        return products

    async def _parse_site_html(self, crawler, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetches HTML using the crawler and parses it using site-specific BS logic."""
        products = []
        engine_name = config["name"]
        base_url = config.get("base_url", url)
        item_selector = config.get("item_selector", "body")
        wait_for_selector = config["config"].get("wait_for", item_selector) # Use specific wait_for

        try:
            print(f"\n--- Fetching HTML for {engine_name} ---")
            print(f"URL: {url}")

            result = await crawler.arun(
                url=url,
                js_code=config["config"].get("js", ""),
                wait_for=wait_for_selector, # Use the potentially more specific wait_for
                wait_timeout=60000,
                bypass_cache=self.crawl_config.cache_mode == CacheMode.BYPASS,
                magic=self.crawl_config.magic,
                simulate_user=self.crawl_config.simulate_user
            )

            if result and result.html:
                print(f"Successfully fetched HTML for {engine_name} (Length: {len(result.html)}).")
                # --- Site-Specific Parsing ---
                if engine_name == "Amazon":
                     # with open("amazon_results.html", "w", encoding="utf-8") as f:
                     #     f.write(result.html)
                    print(f"Parsing HTML using BeautifulSoup for {engine_name}...")
                    products = self._parse_amazon_bs(result.html, base_url)
                elif engine_name == "AliExpress":
                     # with open("aliexpress_results.html", "w", encoding="utf-8") as f:
                     #     f.write(result.html)
                    print(f"Parsing HTML using BeautifulSoup for {engine_name}...")
                    products = self._parse_aliexpress_bs(result.html, base_url)
                else:
                    print(f"Warning: No robust BeautifulSoup parser defined for engine: {engine_name}")

                print(f"Parsed {len(products)} products for {engine_name}.")

            elif result and not result.html:
                 print(f"Crawler ran for {engine_name} but returned no HTML content.")
            else:
                 print(f"Crawler returned no result object for {engine_name}.")

        except asyncio.TimeoutError:
            print(f"Error: Timeout occurred during crawl for {engine_name} at {url}")
        except Exception as e:
            print(f"Error during HTML fetching or parsing for {engine_name}: {str(e)}")
            print(traceback.format_exc())

        print(f"--- Finished processing for {engine_name}, returning {len(products)} products ---")
        return products

    async def crawl_site(self, url: str, engine_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawls a single site and extracts products using BeautifulSoup."""
        engine_name = engine_config["name"]
        try:
            async with AsyncWebCrawler(
                verbose=True, # Keep verbose for debugging
                proxy=self.browser_config.proxy,
                config=self.browser_config
            ) as crawler:
                products = await self._parse_site_html(crawler, url, engine_config)
                if products:
                    return self._add_source(products, engine_name)
                else:
                    print(f"No products extracted via parsing for {engine_name}")
                    return []
        except Exception as e:
            print(f"Failed to initialize or run crawler for {engine_name}: {str(e)}")
            print(traceback.format_exc())
            return []

    # --- crawl_for_products and _add_source remain the same ---
    async def crawl_for_products(self, query: str) -> List[Dict[str, Any]]:
        print(f"Crawling for products: {query}")
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
                # print(traceback.format_exc()) # Uncomment for full traceback
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

# --- main function remains the same ---
async def main():
    recommender = EcommerceRecommender()
    user_query = input("What are you looking to buy? ")

    print(f"\nSearching for '{user_query}' on {[e['name'] for e in recommender.search_engines]}...")
    products = await recommender.crawl_for_products(user_query)
    print(products)
if __name__ == "__main__":
    asyncio.run(main())