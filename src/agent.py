import os
import re
import sys
import time
import logging
import unicodedata
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
import requests
from tavily import TavilyClient
from google import genai


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("atlas.agent")

# Load environment variables
load_dotenv()


def slugify(text: str) -> str:
    """Converts a text string into a clean, filename-friendly slug.

    Args:
        text: The string to slugify.

    Returns:
        A slugified string containing only alphanumeric characters and hyphens.
    """
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text[:50]


def run_tavily_search(query: str, api_key: str) -> List[Dict[str, str]]:
    """Executes a search using the Tavily API and retrieves the top 5 results.

    Args:
        query: The search query to run.
        api_key: The Tavily API key.

    Returns:
        A list of dictionaries, where each dict has 'title', 'url', and 'content'.

    Raises:
        RuntimeError: If the Tavily search fails or if a status code error occurs.
    """
    logger.info("Sending query to Tavily: '%s'", query)
    try:
        client = TavilyClient(api_key=api_key)
        # Call Tavily search API
        response = client.search(query=query, max_results=5)
        
        results = response.get("results", [])
        sources = []
        for r in results:
            sources.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")
            })
        
        logger.info("Tavily search retrieved %d sources successfully.", len(sources))
        return sources
    except Exception as e:
        status_code = None
        # Extract status code if available
        if hasattr(e, 'response') and e.response is not None:
            status_code = getattr(e.response, 'status_code', None)
        elif hasattr(e, 'status_code'):
            status_code = getattr(e, 'status_code', None)
        
        if status_code is not None:
            raise RuntimeError(f"Tavily API call failed with status code {status_code}: {str(e)}") from e
        else:
            # Fallback to checking string representations of common request issues or HTTPError
            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                raise RuntimeError(f"Tavily API call failed with status code {e.response.status_code}: {str(e)}") from e
            raise RuntimeError(f"Tavily API call failed: {str(e)}") from e


def generate_report_content(question: str, sources: List[Dict[str, str]], api_key: str) -> Dict[str, Any]:
    """Generates a structured research report using Gemini based on retrieved sources.

    Args:
        question: The user's research question.
        sources: A list of retrieved sources containing title, url, and content.
        api_key: The Google API Key.

    Returns:
        A dictionary containing the 'text' response and token usage information.

    Raises:
        Exception: If the Gemini call fails twice.
    """
    # Initialize google-genai Client
    client = genai.Client(api_key=api_key)

    # Format source text for the prompt
    sources_text = ""
    for i, source in enumerate(sources, 1):
        sources_text += f"[{i}] Title: {source['title']}\nURL: {source['url']}\nContent: {source['content']}\n\n"

    # Build the prompt instructing Gemini on constraints
    prompt = f"""You are a precise and objective research analyst for ATLAS (Agentic Trust and Literature Analysis System).

Your task is to synthesize a research report on the following question:
"{question}"

Based ONLY on the retrieved search results below, generate a structured markdown report. Do not extrapolate, assume, or use any outside knowledge that is not explicitly present in the provided sources.

Retrieved Sources:
{sources_text}

Instructions:
1. Ground every statement strictly in the provided sources.
2. Cite your sources inline using brackets containing the source index, e.g., [1], [2], etc. (corresponding to the sources list above). Every key claim or finding must be supported by an inline citation.
3. If the sources do not contain enough information to answer the question, state this clearly.
4. Output your response in structured markdown with exactly the following three sections:
   - ## Summary
   - ## Key Findings
   - ## Sources (Listing the cited sources with their titles and URLs)
"""

    logger.info("Sending generation request to Gemini model 'gemini-2.0-flash'.")
    
    # Try calling the API with a retry once on failure
    last_error = None
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            
            prompt_tokens = 0
            candidate_tokens = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata is not None:
                prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                candidate_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
            
            logger.info("Gemini call succeeded. Tokens used: prompt=%d, candidate=%d", prompt_tokens, candidate_tokens)
            
            return {
                "text": response.text,
                "prompt_tokens": prompt_tokens,
                "candidate_tokens": candidate_tokens
            }
        except Exception as e:
            last_error = e
            if attempt == 0:
                logger.warning("Gemini generation failed, retrying once... Error: %s", str(e))
                time.sleep(1)
            else:
                logger.error("Gemini generation failed twice. Raising error.")
                
    if last_error:
        raise last_error
    raise RuntimeError("Gemini generation failed without a returned error.")


def run_research(question: str) -> str:
    """Orchestrates the research flow: Tavily search, Gemini report generation, and file saving.

    Args:
        question: The research question.

    Returns:
        The file path of the saved research report.

    Raises:
        ValueError: If required API keys are missing in the environment.
    """
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY is not set in the environment.")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY is not set in the environment.")

    # 1. Run Search
    sources = run_tavily_search(question, tavily_api_key)

    # 2. Run Generation
    gen_result = generate_report_content(question, sources, google_api_key)
    report_text = gen_result["text"]

    # 3. Format and save output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(question)
    filename = f"{timestamp}_{slug}.md"
    
    # Save path is relative to the root project directory in data/outputs/
    output_dir = os.path.join("data", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    logger.info("Successfully generated report saved at: %s", output_path)
    return output_path
