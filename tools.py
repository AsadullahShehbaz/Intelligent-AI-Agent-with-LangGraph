"""
All AI tools in one file
"""
import re
import requests
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import wikipedia
import config


# ============ Tool 1: Web Search ============
search_tool = DuckDuckGoSearchRun(region="us-en")


# ============ Tool 2: Calculator ============
@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Do basic math: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Cannot divide by zero"}
            result = first_num / second_num
        else:
            return {"error": "Use: add, sub, mul, or div"}
        
        return {
            "first_num": first_num,
            "second_num": second_num,
            "operation": operation,
            "result": result
        }
    except Exception as e:
        return {"error": str(e)}


# ============ Tool 3: YouTube Transcript ============
@tool
def get_transcript(video_url: str) -> dict:
    """
    Get YouTube video transcript
    """
    try:
        # Get video ID from URL
        match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", video_url)
        video_id = match.group(1) if match else video_url
        
        # Get transcript
        ytt_api = YouTubeTranscriptApi()
        transcript_obj = ytt_api.fetch(video_id, languages=['en','hi'])
        transcript = " ".join(snippet.text for snippet in transcript_obj.snippets)
        
        return {"video_id": video_id, "transcript": transcript}
        
    except TranscriptsDisabled:
        return {"error": "No captions available"}
    except Exception as e:
        return {"error": str(e)}


# ============ Tool 4: Stock Price ============
@tool
def get_stock_price(symbol: str) -> dict:
    """
    Get stock price from AlphaVantage
    """
    try:
        url = (
            f"https://www.alphavantage.co/query?"
            f"function=TIME_SERIES_INTRADAY"
            f"&symbol={symbol}"
            f"&interval=5min"
            f"&apikey={config.STOCK_API_KEY}"
        )
        return requests.get(url).json()
    except Exception as e:
        return {"error": str(e)}


# ============ Tool 5: Wikipedia Search ============
@tool
def search_wikipedia(query: str, sentences: int = 3) -> dict:
    """
    Search Wikipedia and get a summary.
    
    Args:
        query: The topic to search for (e.g., "Python programming", "Albert Einstein")
        sentences: Number of sentences in summary (default: 3)
    
    Returns:
        Dictionary with title, summary, and url
    """
    try:
        # Search for the page
        search_results = wikipedia.search(query, results=1)
        
        if not search_results:
            return {"error": f"No Wikipedia article found for '{query}'"}
        
        # Get the page
        page = wikipedia.page(search_results[0], auto_suggest=False)
        
        # Get summary with specified sentences
        summary = wikipedia.summary(search_results[0], sentences=sentences, auto_suggest=False)
        
        return {
            "title": page.title,
            "summary": summary,
            "url": page.url,
            "categories": page.categories[:5] if hasattr(page, 'categories') else []
        }
        
    except wikipedia.exceptions.DisambiguationError as e:
        # Multiple results found
        options = e.options[:5]  # Show first 5 options
        return {
            "error": "Multiple results found. Please be more specific.",
            "options": options
        }
    except wikipedia.exceptions.PageError:
        return {"error": f"No Wikipedia page found for '{query}'"}
    except Exception as e:
        return {"error": f"Wikipedia error: {str(e)}"}


# ============ Tool 6: Weather (wttr.in) ============
@tool
def get_weather(city: str) -> str:
    """
    Get current weather for any city using wttr.in service.
    
    Args:
        city: City name (e.g., "London", "New York", "Islamabad", "Tokyo")
    
    Returns:
        Weather condition and temperature as a string
    
    Examples:
        - "What's the weather in London?"
        - "Get weather for Tokyo"
        - "How's the weather in Karachi?"
    """
    try:
        # wttr.in API - simple and free, no API key needed
        # %C = weather condition, %t = temperature
        url = f"https://wttr.in/{city.lower()}?format=%C+%t"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            weather_text = response.text.strip()
            return f"The weather in {city} is {weather_text}"
        else:
            return f"⚠️ Could not fetch weather for {city}. Please check the city name."
            
    except requests.exceptions.Timeout:
        return f"⚠️ Weather service timeout for {city}. Please try again."
    except Exception as e:
        return f"⚠️ Error getting weather for {city}: {str(e)}"


# ============ Tool 7: Language Translation ============
@tool
def translate_text(text: str, target_language: str = "en", source_language: str = "auto") -> dict:
    """
    Translate text between languages using Google Translate.
    
    Args:
        text: Text to translate
        target_language: Target language code. Common codes:
            - en (English)
            - ur (Urdu)
            - ar (Arabic)
            - es (Spanish)
            - fr (French)
            - de (German)
            - zh-cn (Chinese)
            - ja (Japanese)
            - hi (Hindi)
        source_language: Source language (default: auto-detect)
    
    Examples:
        - "Translate 'Hello, how are you?' to Urdu"
        - "Translate 'یہ کیسا ہے' to English"
        - "Convert 'Bonjour' to English"
    """
    try:
        from googletrans import Translator
        
        translator = Translator()
        result = translator.translate(text, dest=target_language, src=source_language)
        
        # Language name mapping for better UX
        lang_names = {
            'en': 'English', 'ur': 'Urdu', 'ar': 'Arabic',
            'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'zh-cn': 'Chinese', 'ja': 'Japanese', 'hi': 'Hindi',
            'tr': 'Turkish', 'ru': 'Russian', 'it': 'Italian'
        }
        
        source_name = lang_names.get(result.src, result.src)
        target_name = lang_names.get(target_language, target_language)
        
        return {
            "original_text": text,
            "translated_text": result.text,
            "source_language": f"{source_name} ({result.src})",
            "target_language": f"{target_name} ({target_language})",
            "pronunciation": result.pronunciation if result.pronunciation else None
        }
        
    except ImportError:
        return {
            "error": "Translation library not installed. Run: pip install googletrans==4.0.0-rc1"
        }
    except Exception as e:
        return {"error": f"Translation failed: {str(e)}"}


# ============ Import Document Tool ============
from document_analyzer import ask_document


# ============ Export All Tools ============
all_tools = [
    search_tool, 
    calculator, 
    get_transcript, 
    get_stock_price,
    search_wikipedia,
    get_weather,
    translate_text,
    ask_document  # PDF/Document Q&A
]