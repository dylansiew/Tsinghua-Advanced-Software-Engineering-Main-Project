from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
import pandas as pd
from urllib.parse import quote_plus
import re
import json
import asyncio
import nest_asyncio
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

class EcommerceRecommender:
    def __init__(self, search_engines=None, captcha_key: Optional[str] = None):
        load_dotenv()
        self.search_engines = search_engines or [
            {
                "name": "Amazon", 
                "url": "https://www.amazon.com/s?k=",
                "config": {
                    "wait_for": "div.s-result-item",
                    "selectors": {
                        "products": "div.s-result-item[data-component-type='s-search-result']", 
                        "title": "h2 a.a-link-normal span.a-text-normal",
                        "price": "span.a-price span.a-offscreen", 
                        "url": "h2 a.a-link-normal@href",
                        "rating": "span.a-icon-alt", 
                        "reviews": "span.a-size-base.s-underline-text"
                    },
                    "js": "window.scrollBy(0, 500); await new Promise(r => setTimeout(r, 2000));"
                }
            }
        ]
        
        self.crawler_config = {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "timeout": 300000,
            "proxy": None  # or set your proxy if needed
        }
        
        # LLM configuration (updated for Ollama)
        self.llm_model = os.getenv("LLM_MODEL", "llama2")  # Default to free local model
        self.llm_api_base = os.getenv("LLM_API_BASE", "http://localhost:11434")  # Ollama default
        
        # Browser config
        self.browser_config = BrowserConfig(
            headless=True,
            user_agent=self.crawler_config["user_agent"],
            viewport={"width": 1280, "height": 720},
            proxy=self.crawler_config.get("proxy")
        )
        
        # Global crawler configuration
        self.run_conf = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            magic = True,
            simulate_user = True
        )
        
    def generate_search_urls(self, query: str) -> List[str]:
        """Generate search URLs for each search engine."""
        return [engine["url"] + quote_plus(query) for engine in self.search_engines]
    
    async def crawl_site(self, url: str, engine_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            async with AsyncWebCrawler(
                verbose=True,
                proxy=self.crawler_config.get("proxy"),
                config=self.browser_config  # Keep it here
            ) as crawler:
                raw_html_result = await crawler.arun(
                    run_config=self.run_conf,
                    url=url,
                    js_code=engine_config["config"].get("js", []),
                    strategy="playwright",
                    wait_for=engine_config["config"].get("wait_for", 5),
                    wait_timeout=self.crawler_config["timeout"]
                )
                
                if raw_html_result and hasattr(raw_html_result, 'html'):
                    # Save first 1000 chars to a debug file
                    with open(f"debug_{engine_config['name']}.html", "w") as f:
                        f.write(raw_html_result.html[:20000])  # First 20000 chars
                
                products = []
                
                # 1. First try LLM extraction
                try:
                    products = await self._try_llm_extraction(crawler, url, engine_config)
                    if products and len(products) > 0:
                        print(f"LLM extraction successful for {engine_config['name']}, found {len(products)} products")
                        return self._add_source(products, engine_config["name"])
                except Exception as e:
                    print(f"LLM extraction failed for {engine_config['name']}: {str(e)}")
                
                # 2. Then try CSS extraction if LLM failed
                try:
                    products = await self._try_css_extraction(crawler, url, engine_config)
                    if products and len(products) > 0:
                        print(f"CSS extraction successful for {engine_config['name']}, found {len(products)} products")
                        return self._add_source(products, engine_config["name"])
                except Exception as e:
                    print(f"CSS extraction failed for {engine_config['name']}: {str(e)}")
                
                # 3. Finally try basic extraction as last resort
                try:
                    products = await self._try_basic_extraction(crawler, url, engine_config)
                    if products and len(products) > 0:
                        print(f"Basic extraction successful for {engine_config['name']}, found {len(products)} products")
                        return self._add_source(products, engine_config["name"])
                except Exception as e:
                    print(f"Basic extraction failed for {engine_config['name']}: {str(e)}")
                
                print(f"All extraction methods failed for {engine_config['name']}")
                return []
            
        except Exception as e:
            print(f"Failed to initialize crawler for {engine_config['name']}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    async def _try_llm_extraction(self, crawler, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            instructions = f"""Extract product listings from {config['name']} search results. For each product, extract:
            - product_name (text)
            - price (with currency)
            - rating (out of 5 if available)
            - reviews (count if available)
            - url (product page)
            - seller (if available)
            Return as a JSON array."""
            
            # Create the LLMExtractionStrategy instance
            llm_strategy = LLMExtractionStrategy(
                instruction=instructions,
                extraction_type="json",
                llm_provider="ollama",  # Explicitly set provider
                llm_model=self.llm_model,
                llm_api_base=self.llm_api_base,
            )
                        
            result = await crawler.arun(
                run_config=self.run_conf,
                url=url,
                js_code=config["config"].get("js", ""),
                strategy="playwright",
                extraction_strategy=llm_strategy,
                wait_for=config["config"].get("wait_for", 5),
                wait_timeout=self.crawler_config["timeout"],
                bypass_cache=True
            )

            if result and hasattr(result, 'extracted_content'):
                if result.extracted_content:  # Check if the content is not None/empty
                    try:
                        products = json.loads(result.extracted_content)
                        return self._add_source(products, config["name"])
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse JSON from {config['name']} extraction result: {e}")
                        print(f"Raw content: {result.extracted_content[:200]}...")  # Print first 200 chars
                else:
                    print(f"Extracted content is None or empty for {config['name']} (LLM)")
                        
            return []
        except Exception as e:
            print(f"LLM extraction failed for {config['name']}: {str(e)}")
            import traceback
            print(traceback.format_exc())
        return []
    
    async def _try_css_extraction(self, crawler, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            schema = {
                "name": f"{config['name']} Product Extractor",
                "baseSelector": config["config"]["selectors"]["products"],
                "fields": [
                    {"name": "product_name", "selector": config["config"]["selectors"]["title"], "type": "text"},
                    {"name": "price", "selector": config["config"]["selectors"]["price"], "type": "text"},
                    {"name": "url", "selector": config["config"]["selectors"]["url"], "type": "attribute", "attribute": "href"},
                ]
            }
            
            if "rating" in config["config"]["selectors"]:
                schema["fields"].append({"name": "rating", "selector": config["config"]["selectors"]["rating"], "type": "text"})
            
            extraction_strategy = JsonCssExtractionStrategy(schema)
            
            result = await crawler.arun(
                run_config=self.run_conf,
                url=url,
                js_code=config["config"].get("js", ""),
                extraction_strategy=extraction_strategy,
                wait_for=config["config"].get("wait_for", 5),
                bypass_cache=True
            )
            
            if not result or not result.extracted_content:
                print(f"No content extracted from {config['name']} (CSS)")
                return []
                
            return json.loads(result.extracted_content)
            
        except Exception as e:
            print(f"CSS extraction failed for {config['name']}: {str(e)}")
            return []
    
    async def _try_basic_extraction(self, crawler, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        result = await crawler.arun(
            run_config=self.run_conf,
            url=url,
            js_code=config["config"].get("js", ""),
            strategy="playwright",
            wait_for=config["config"].get("wait_for", 5),
            wait_timeout=self.crawler_config["timeout"]
        )
        
        if not result or not hasattr(result, 'html') or not result.html:
            return []
        with open("amazon_debug.html", "w", encoding="utf-8") as f:
            f.write(result.html)
        # Very basic regex-based extraction as a fallback
        products = []
        
        if config["name"] == "Amazon":
            # Extract product details using regex patterns
            product_blocks = re.findall(r'<div\s+[^>]*data-component-type="s-search-result"[^>]*>(.*?)</div>\s*</div>\s*</div>', result.html, re.DOTALL)
            
            for block in product_blocks[:10]:  # Limit to first 10 matches for performance
                product = {}
                
                # Extract title
                title_match = re.search(r'<h2[^>]*class="[^"]*a-size-base-plus[^"]*"[^>]*>.*?<span>([^<]+)</span>', block, re.DOTALL)
                if title_match:
                    product["product_name"] = title_match.group(1).strip()
                
                # Extract price
                price_match = re.search(r'<span class="a-offscreen">([^<]+)</span>', block)
                if price_match:
                    product["price"] = price_match.group(1).strip()
                
                # Extract URL
                url_match = re.search(r'<a\s+[^>]*href="([^"]+)"[^>]*class="[^"]*a-link-normal[^"]*"', block)
                if url_match:
                    url = url_match.group(1)
                    if not url.startswith('http'):
                        url = f'https://www.{amazon}.com' + url
                    product["url"] = url
                
                if product:
                    products.append(product)
                    
        return products

    async def crawl_for_products(self, query: str) -> List[Dict[str, Any]]:
        """Crawl all configured e-commerce sites for products matching the query."""
        search_urls = self.generate_search_urls(query)
        
        # Create a list to store all crawled products
        all_products = []
        
        # Crawl each search engine in parallel
        tasks = []
        for i, url in enumerate(search_urls):
            engine_config = self.search_engines[i]
            task = self.crawl_site(url, engine_config)
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all products into a single list
        for result in results:
            # Skip exceptions
            if isinstance(result, Exception):
                print(f"Error in crawl task: {result}")
                continue
            all_products.extend(result)
        
        print(f"Found {len(all_products)} products across all sites")
        return all_products

    def _add_source(self, products: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
        """Add source information to products."""
        if isinstance(products, list):
            for product in products:
                if isinstance(product, dict):
                    product['source'] = source
            return products
        return []
    
    def normalize_prices(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize prices to a common currency (USD by default)."""
        for product in products:
            if 'price' in product and isinstance(product['price'], str):
                # Extract numeric value from price string
                price_str = re.sub(r'[^\d.]', '', product['price'])
                try:
                    product['price_float'] = float(price_str)
                except ValueError:
                    product['price_float'] = None
            elif 'price' in product and isinstance(product['price'], (int, float)):
                product['price_float'] = float(product['price'])
            else:
                product['price_float'] = None
        return products
    
    def filter_and_rank(self, 
                       products: List[Dict[str, Any]], 
                       min_price=None, 
                       max_price=None, 
                       min_rating=None,
                       sort_by="relevance") -> List[Dict[str, Any]]:
        """Filter and rank products based on criteria."""
        filtered_products = products.copy()
        
        if min_price is not None:
            filtered_products = [p for p in filtered_products 
                               if p.get('price_float') is not None and p['price_float'] >= min_price]
        
        if max_price is not None:
            filtered_products = [p for p in filtered_products 
                               if p.get('price_float') is not None and p['price_float'] <= max_price]
        
        if min_rating is not None:
            filtered_products = [p for p in filtered_products 
                               if p.get('rating') is not None and float(p['rating']) >= min_rating]
        
        # Sort products
        if sort_by == "price_low":
            filtered_products = [p for p in filtered_products if p.get('price_float') is not None]
            filtered_products.sort(key=lambda x: x.get('price_float', float('inf')))
        elif sort_by == "price_high":
            filtered_products = [p for p in filtered_products if p.get('price_float') is not None]
            filtered_products.sort(key=lambda x: x.get('price_float', float('-inf')), reverse=True)
        elif sort_by == "rating":
            filtered_products.sort(key=lambda x: float(x.get('rating', 0)), reverse=True)
        elif sort_by == "reviews":
            filtered_products.sort(key=lambda x: int(re.sub(r'[^\d]', '', str(x.get('reviews', 0)))), reverse=True)
        
        return filtered_products
    
    async def generate_recommendations(self, 
                                     query: str, 
                                     min_price=None, 
                                     max_price=None, 
                                     min_rating=None, 
                                     sort_by="relevance") -> pd.DataFrame:
        """Generate product recommendations based on the user's query and criteria."""
        print(f"Searching for products matching: {query}")
        
        # Step 1: Crawl for products
        products = await self.crawl_for_products(query)
        
        if not products:
            return pd.DataFrame({"message": ["No products found matching your search query"]})
        
        # Step 2: Normalize prices
        products = self.normalize_prices(products)
        
        # Step 3: Filter and rank
        recommendations = self.filter_and_rank(
            products, 
            min_price=min_price, 
            max_price=max_price, 
            min_rating=min_rating,
            sort_by=sort_by
        )
        
        # Convert to DataFrame for easier viewing
        if recommendations:
            df = pd.DataFrame(recommendations)
            # Reorder columns for better presentation
            columns = ['product_name', 'price', 'price_float', 'rating', 'reviews', 'seller', 'source', 'url']
            columns = [col for col in columns if col in df.columns] + [col for col in df.columns if col not in columns]
            return df[columns]
        else:
            return pd.DataFrame({"message": ["No products found matching your criteria"]})

async def main():
    nest_asyncio.apply()
    recommender = EcommerceRecommender()
    
    # Get user input
    user_query = input("What are you looking to buy? ")
    
    # Optional filtering parameters
    min_price = input("Minimum price (leave blank for none): ")
    min_price = float(min_price) if min_price else None
    
    max_price = input("Maximum price (leave blank for none): ")
    max_price = float(max_price) if max_price else None
    
    min_rating = input("Minimum rating out of 5 (leave blank for none): ")
    min_rating = float(min_rating) if min_rating else None
    
    sort_options = {
        "1": "relevance",
        "2": "price_low",
        "3": "price_high",
        "4": "rating",
        "5": "reviews"
    }
    
    print("\nSort by:")
    for key, value in sort_options.items():
        print(f"{key}. {value.replace('_', ' to ')}")
    
    sort_choice = input("\nEnter your choice (1-5): ")
    sort_by = sort_options.get(sort_choice, "relevance")
    
    # Generate and display results
    recommendations = await recommender.generate_recommendations(
        user_query,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by
    )
    
    if not recommendations.empty and 'message' not in recommendations.columns:
        print(f"\nFound {len(recommendations)} products:")
        print(recommendations.to_markdown(index=False))
    else:
        print("\nNo products found. Try adjusting your search criteria.")

if __name__ == "__main__":
    asyncio.run(main())