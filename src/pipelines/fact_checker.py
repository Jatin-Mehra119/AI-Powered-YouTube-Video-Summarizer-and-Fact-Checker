"""
fact_checker.py
----------------
Uses Groq’s deepseek-r1-distill-llama-70b-specdec model to refine the context extracted from captions,
and then uses crawl4ai to verify the refined claim online.
"""

import os
import json
import asyncio
import dotenv
import streamlit as st
import feedparser
import urllib.parse  # For URL encoding
import re             

import groq 
import crawl4ai 
from crawl4ai import LLMExtractionStrategy, CrawlerRunConfig, CacheMode, BrowserConfig, AsyncWebCrawler

dotenv.load_dotenv()

class FactChecker:
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.model_name = "llama-3.1-8b-instant"
        self.crawl_model = "llama-3.1-8b-instant"

    def extract_json_from_response(self, text: str) -> str:
        """
        Attempt to extract a JSON object from the given text.
        It first looks for a block enclosed in triple backticks with 'json'.
        If not found, it searches for the first '{' and last '}'.
        """
        # Try to extract from a code block, e.g., ```json { ... } ```
        match = re.search(r"```json\s*(\{.*\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1)
        # Fallback: extract from first '{' to last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end+1]
        # If extraction fails, return the original text
        return text

    async def refine_context(self, context: str) -> str:
        """Refine the given context and extract keywords using Groq's LLM.
        
        Returns a JSON string with the refined context and keywords.
        """
        try:
            # Wrap the synchronous LLM call with asyncio.to_thread
            chat_completion = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                messages=[{
                    "role": "user",
                    "content": f"""
Refine the context: {context}
Give me more information about this context.
Give Keywords so I can search on the internet for more information.
Please respond in JSON format like:
{{
    "context": "{context}",
    "keywords": ["keyword1", "keyword2"]
}}
"""
                }],
                model=self.model_name,
                temperature=0.3,
                max_tokens=4000
            )
            response_str = chat_completion.choices[0].message.content
            # Extract JSON substring from the LLM's response
            json_str = self.extract_json_from_response(response_str)
            try:
                json_data = json.loads(json_str)
            except Exception as e:
                print(f"Error parsing refined context JSON: {e}")
                json_data = {"context": context, "keywords": []}
            return json.dumps(json_data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def fetch_article_links(self, keywords: list) -> list:
        """Fetch the first 10 article links related to the keywords using the Google News RSS feed."""
        # Convert keywords to lowercase and URL-encode each keyword
        keywords = [keyword.lower() for keyword in keywords]
        query_str = "+".join(urllib.parse.quote_plus(keyword) for keyword in keywords)
        rss_url = f"https://news.google.com/rss/search?q={query_str}&hl=en-IN&gl=IN&ceid=IN:en"
        # Run feedparser.parse in a thread because it's synchronous.
        feed = await asyncio.to_thread(feedparser.parse, rss_url)
        links = []
        for entry in feed.entries[:10]:
            link = entry.get("link", "")
            title = entry.get("title", "")
            base_domain = link.split("://")[1].split("/")[0] if "://" in link else ""
            links.append({
                "link": link,
                "text": title,
                "title": title,
                "base_domain": base_domain
            })
        return links

    async def fetch_article_content(self, links: list, keywords: list) -> list:
        """Fetch and process article content from the provided links using crawl4ai."""
        extraction_strategy = LLMExtractionStrategy(
            provider="groq",
            model_name=self.crawl_model,
            api_token=os.getenv("GROQ_API_KEY"),
            extraction_type="schema",
            # Schema expecting a JSON object with a single key 'content'
            schema={"type": "object", "properties": {"content": {"type": "string"}}},
            instruction=(
                f"Extract the main article content as plain text from the HTML. Look for mentions of {keywords}. "
                "Ignore navigation, advertisements, and boilerplate text. "
                "Return a JSON object with a single key 'content'."
            ),
            chunk_token_threshold=1200,
            overlap_rate=0.1,
            apply_chunking=True,
            input_format="html",
            extra_args={"temperature": 0.1, "max_tokens": 4000}
        )

        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy
        )

        articles = []
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            for link_obj in links:
                url = link_obj.get("link", "")
                if not url:
                    print("Skipping empty URL for link object:", link_obj)
                    continue
                result = await crawler.arun(url, config=config)
                if result.success:
                    try:
                        data = json.loads(result.extracted_content)
                        # If the extracted content is a list, try to extract the first element's content.
                        if isinstance(data, dict):
                            article_content = data.get("content", "")
                        elif isinstance(data, list) and data:
                            if isinstance(data[0], dict):
                                article_content = data[0].get("content", "")
                            else:
                                article_content = ""
                        else:
                            article_content = ""
                    except Exception as e:
                        print(f"Failed to parse extracted content for {url}: {e}")
                        article_content = ""
                    articles.append({"url": url, "content": article_content})
                else:
                    print(f"Content crawl failed for {url}: {result.error_message}")
        return articles

    async def verify_fact(self, refined_context: dict, articles: list) -> str:
        """
        Compare the refined context with the fetched article contents to determine if the claim is supported.
        Uses the LLM to output a JSON with keys:
            - factually_correct: boolean
            - confidence: float (0 to 1)
            - explanation: short explanation
        """
        combined_articles = "\n".join(article["content"] for article in articles if article["content"])
        prompt = (
            f"Based on the refined context: {refined_context.get('context')} \n\n"
            f"and the following article contents: \n{combined_articles}\n\n"
            "Does the evidence support the claim? Please respond in JSON format with the following keys:\n"
            '"factually_correct": (boolean), "confidence": (float between 0 and 1), "explanation": (short explanation)'
        )
        try:
            verification_response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.2,
                max_tokens=4000
            )
            verification_result = verification_response.choices[0].message.content
            return verification_result
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_fact_check_resources(self) -> str:
        """
        Suggest resources that can be used to verify the veracity of a claim.
        Returns:
            str: A comma-separated list of recommended fact-checking resources.
        """
        resources = "FactCheck.org, Snopes, PolitiFact, Reuters Fact Check, AP Fact Check"
        return resources

    async def fact_check(self, context: str) -> dict:
        """
        Orchestrates the fact-checking process:
          1. Refines the context using Groq.
          2. Extracts keywords.
          3. Fetches article links from Google News RSS.
          4. Fetches article contents.
          5. Verifies the claim by comparing the refined context with article content.
          6. Provides recommended resources for further verification.
        
        Args:
            context (str): The original claim or context.
            
        Returns:
            dict: Contains refined context, articles, verification result, and suggested resources.
        """
        # Step 1: Refine the context and extract keywords.
        refined_str = await self.refine_context(context)
        try:
            refined_json = json.loads(refined_str)
        except Exception as e:
            print(f"Error parsing refined context after extraction: {e}")
            refined_json = {"context": context, "keywords": []}
        keywords = refined_json.get("keywords", [])
        
        # Step 2: Fetch article links based on the extracted keywords.
        links = await self.fetch_article_links(keywords)
        
        # Step 3: Fetch article content from those links.
        articles = await self.fetch_article_content(links, keywords)
        
        # Step 4: Verify the claim by comparing with the articles.
        verification_result = await self.verify_fact(refined_json, articles)
        
        # Step 5: Get additional fact-checking resources.
        resources = self.get_fact_check_resources()
        
        return {
            "refined_context": refined_json,
            "articles": articles,
            "verification_result": verification_result,
            "resources": resources
        }

if __name__ == "__main__":
    dotenv.load_dotenv()  # Ensure environment variables are loaded.
    sample = input("Enter context to fact-check: ")
    
    # Initialize the GROQ client (ensure GROQ_API_KEY is set in your environment)
    groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
    fact_checker = FactChecker(groq_client)
    
    # Run the asynchronous fact-checking pipeline.
    result = asyncio.run(fact_checker.fact_check(sample))
    print(json.dumps(result, indent=2))
