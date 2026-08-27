"""
Live Real-Time Web Search & Grounding Engine for Yakob Assistant.
Enables Yakob to act like a real AI chatbot with live internet searching capabilities:
1. DuckDuckGo Instant Answer & Web Search API (Zero API keys needed)
2. Wikipedia Fact Extraction API
3. HTML Text Snippet Scraper & Synthesizer
"""
import re
import json
import urllib.request
import urllib.parse
from typing import Optional, List, Dict


class WebSearchEngine:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    def search_live_web(self, query: str, max_results: int = 4) -> str:
        """
        Performs real-time web search and returns compiled factual snippets.
        """
        if not query or not query.strip():
            return ""

        clean_query = self._clean_query(query)

        # 1. Try DuckDuckGo Instant Answer API
        instant_answer = self._search_duckduckgo_instant(clean_query)
        if instant_answer:
            return instant_answer

        # 2. Try Wikipedia Summary API (Great for people, events, geography, science)
        wiki_summary = self._search_wikipedia(clean_query)
        if wiki_summary:
            return wiki_summary

        # 3. Try DuckDuckGo HTML Web Search (Live search results)
        html_snippets = self._search_duckduckgo_html(clean_query, max_results=max_results)
        if html_snippets:
            return html_snippets

        return ""

    def _clean_query(self, query: str) -> str:
        q = re.sub(r'^(who is|what is|tell me about|search for|look up|where is|when was|how to|find)\s+', '', query, flags=re.IGNORECASE)
        q = re.sub(r'\?$', '', q).strip()
        return q or query

    def _search_duckduckgo_instant(self, query: str) -> Optional[str]:
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("AbstractText"):
                    return f"According to DuckDuckGo: {data['AbstractText']}"
                if data.get("Answer"):
                    return f"Result: {data['Answer']}"
        except Exception:
            pass
        return None

    def _search_wikipedia(self, query: str) -> Optional[str]:
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("extract") and len(data["extract"]) > 30:
                    extract = data["extract"]
                    # Limit to first 2 sentences for concise voice chatbot response
                    sentences = re.split(r'(?<=[.!?])\s+', extract)
                    return " ".join(sentences[:2])
        except Exception:
            pass
        return None

    def _search_duckduckgo_html(self, query: str, max_results: int = 3) -> Optional[str]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                
                # Extract snippets from DuckDuckGo HTML results
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, flags=re.DOTALL)
                clean_snippets = []
                for s in snippets[:max_results]:
                    text = re.sub(r'<.*?>', '', s)  # strip tags
                    text = re.sub(r'\s+', ' ', text).strip()
                    if text and len(text) > 20:
                        clean_snippets.append(text)

                if clean_snippets:
                    return " ".join(clean_snippets[:2])
        except Exception:
            pass
        return None


# Global Singleton Instance
web_search = WebSearchEngine()
