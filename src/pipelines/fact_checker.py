"""
fact_checker.py
----------------
Uses Groq’s llama-3.1-8b-instant model to refine the context extracted from captions,
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
        """Extract a JSON object from the LLM response."""
        match = re.search(r"```json\s*(\{.*\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end+1]
        return text  # Return original text if extraction fails

    async def refine_context(self, context: str) -> str:
        """Refine the given context and extract keywords using Groq's LLM."""
        try:
            chat_completion = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                messages=[{"role": "user", "content": f"""
                    Refine the context: {context}
                    Give me more information about this context.
                    Extract keywords for further research.
                    Respond in JSON format:
                    {{
                        "context": "{context}",
                        "keywords": ["keyword1", "keyword2"]
                    }}
                """}],
                model=self.model_name,
                temperature=0.3,
                max_tokens=2000  # Reduced to avoid truncation
            )

            print("Raw Groq API Response:", chat_completion)  # Debugging step

            if not chat_completion.choices:
                return json.dumps({"error": "Groq API returned no response"})

            response_str = chat_completion.choices[0].message.content
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
        """Fetch the first 10 article links related to the keywords using Google News RSS."""
        keywords = [keyword.lower() for keyword in keywords]
        query_str = "+".join(urllib.parse.quote_plus(keyword) for keyword in keywords)
        rss_url = f"https://news.google.com/rss/search?q={query_str}&hl=en-IN&gl=IN&ceid=IN:en"

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
            schema={"type": "object", "properties": {"content": {"type": "string"}}},
            instruction=f"Extract the main article content as plain text. Look for mentions of {keywords}.",
            chunk_token_threshold=1200,
            apply_chunking=True,
            extra_args={"temperature": 0.1, "max_tokens": 2000}
        )

        config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, extraction_strategy=extraction_strategy)
        articles = []

        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            for link_obj in links:
                url = link_obj.get("link", "")
                if not url:
                    continue
                result = await crawler.arun(url, config=config)
                if result.success:
                    try:
                        data = json.loads(result.extracted_content)
                        article_content = data.get("content", "") if isinstance(data, dict) else ""
                    except Exception as e:
                        print(f"Failed to parse extracted content for {url}: {e}")
                        article_content = ""
                    articles.append({"url": url, "content": article_content})
        return articles

    async def verify_fact(self, refined_context: dict, articles: list) -> str:
        """Compare refined context with articles and determine factual accuracy."""
        combined_articles = "\n".join(article["content"] for article in articles if article["content"])
        prompt = f"""
            Based on the refined context: {refined_context.get('context')}
            and the following article contents: {combined_articles}
            Does the evidence support the claim? Respond in JSON:
            {{
                "factually_correct": (boolean),
                "confidence": (float between 0 and 1),
                "explanation": (short explanation)
            }}
        """
        try:
            verification_response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.2,
                max_tokens=4000
            )

            if not verification_response.choices:
                return json.dumps({"error": "Groq API did not return a valid response"})

            verification_result = verification_response.choices[0].message.content
            return verification_result
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_fact_check_resources(self) -> str:
        """Return fact-checking resources."""
        return "FactCheck.org, Snopes, PolitiFact, Reuters Fact Check, AP Fact Check"

    async def fact_check(self, context: str) -> dict:
        """Orchestrates fact-checking steps."""
        refined_str = await self.refine_context(context)
        try:
            refined_json = json.loads(refined_str)
        except Exception as e:
            print(f"Error parsing refined context: {e}")
            refined_json = {"context": context, "keywords": []}
        keywords = refined_json.get("keywords", [])

        links = await self.fetch_article_links(keywords)
        articles = await self.fetch_article_content(links, keywords)
        verification_result = await self.verify_fact(refined_json, articles)
        resources = self.get_fact_check_resources()

        return {
            "refined_context": refined_json,
            "articles": articles,
            "verification_result": verification_result,
            "resources": resources
        }
    
    async def summarize_text(self, transcript: str) -> str:
        """Generate a summary of the given transcript using Groq's LLM."""
        try:
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                messages=[{"role": "user", "content": f"""Summarize this transcript: {transcript}
                    Provide a concise summary of the transcript.
                    Respond in bullet points.
                    Word limit: 1000
                """}],
                model=self.model_name,
                temperature=0.3,
                max_tokens=4000
            )
            
            if not response.choices:
                return "Error: No summary generated."

            return response.choices[0].message.content

        except Exception as e:
            return f"Summarization failed: {str(e)}"


"""
if __name__ == "__main__":
    dotenv.load_dotenv()
    sample = input("Enter context to fact-check: ")

    groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
    fact_checker = FactChecker(groq_client)

    result = asyncio.run(fact_checker.fact_check(sample))
    print(json.dumps(result, indent=2))
"""
