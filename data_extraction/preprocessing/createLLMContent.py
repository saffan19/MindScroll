import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROMPT = """
You are given some reference data. Your task is to transform it into a short, engaging, and entertaining post.

### Requirements:
- The post will be converted into a *voice format*, so it must be:
  - Conversational and engaging (do not add hello or greetings, and byes)
  - Concise while keeping the essence of the reference data
  - Friendly and approachable in tone
  - Free of technical jargon or overly complex language
  - do not add expressions like "Whoa, Wow in everything you write"
- You may add relevant supporting information if it improves clarity or engagement, but stay on-topic.

### Output Format:
Return your answer *strictly* as a JSON object with the following keys:
- "title": A catchy, relevant title for the post
- "content": The engaging and concise post content
- "tags": A list of 3 - 7 relevant tags
- "rating": One of:
    - "U" (Universal - suitable for all audiences)
    - "UA" (Parental Guidance - suitable for all, but children under 12 may need supervision)
    - "A" (Adults - restricted to 18+)
    - "S" (Special category - restricted to specialized audiences such as experts or professionals)
- "difficulty": One of:
    - "Beginner" (for users with no prior knowledge)
    - "Intermediate" (for users with some prior knowledge)
    - "Advanced" (for users with strong prior knowledge)

Reference Data:
"""

# ---------------- API Key Manager ----------------
def get_api_keys():
    """Fetch all API keys stored as API_KEY1, API_KEY2, ... from .env/env."""
    keys = []
    i = 1
    while True:
        key = os.getenv(f"API_KEY{i}")
        if not key:
            break
        keys.append(key)
        i += 1
    return keys

class APIKeyManager:
    def __init__(self):
        self.keys = get_api_keys()
        if not self.keys:
            raise RuntimeError("No API keys found in environment (API_KEY1, API_KEY2, ...)")
        self.index = 0

    @property
    def current_key(self):
        return self.keys[self.index]

    def rotate_key(self):
        """Switch to next API key if available."""
        if self.index + 1 < len(self.keys):
            self.index += 1
            print(f"Switching to next API key (index={self.index})")
        else:
            raise RuntimeError("All API keys are exhausted!")

api_manager = APIKeyManager()

# ---------------- Gemini Function ----------------
def send_to_gemini(article, prompt_template=None):
    if prompt_template is None:
        prompt_template = (
            PROMPT +
            "\n\n"
            "{data}\n"
        )
    article_str = json.dumps(article, indent=2)
    prompt = prompt_template.format(data=article_str)

    while True:
        try:
            genai.configure(api_key=api_manager.current_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            # Example: Check if it's a quota/usage error
            print(f"Error with key {api_manager.current_key}: {e}")
            try:
                api_manager.rotate_key()
            except RuntimeError:
                raise  # All keys exhausted, re-raise error


# Example usage:
if __name__ == "__main__":
    # Hardcoded article dict
    article = {
        "guid": "https://techcrunch.com/?p=3037155",
        "title": "US government is reportedly in discussions to take stake in Intel",
        "link": "https://techcrunch.com/2025/08/14/u-s-government-is-reportedly-in-discussions-to-take-stake-in-intel/",
        "published": "Thu, 14 Aug 2025 20:38:20 +0000",
        "summary": "This deal would be meant to help Intel bulk up its U.S. chip manufacturing, including its much-delayed Ohio factory.",
        "description": "This deal would be meant to help Intel bulk up its U.S. chip manufacturing, including its much-delayed Ohio factory.",
        "image_url": None,
        "author": "Rebecca Szkutak",
        "source": "https://techcrunch.com/feed/",
        "content": (
            "In Brief\n\nThe Trump administration continues to meddle with semiconductor giant Intel.\n\n"
            "The U.S. government is reportedly in discussions to take a stake in Intel, according to reporting from Bloomberg. "
            "This deal would be structured to help the company expand its U.S. manufacturing efforts, including its much-delayed Ohio chip factory.\n\n"
            "This news comes less than a week after President Donald Trump insisted that Intel CEO Lip-Bu Tan resign because of perceived conflicts of interest. "
            "While Trump didn’t provide a reason, this came after Republican U.S. Sen. Tom Cotton wrote to Intel’s board asking about Tan’s alleged ties to China.\n\n"
            "Tan met with the Trump administration on August 11 to quell the administration’s fears and figure out ways for the company to work with the government. "
            "This meeting is what sparked discussions of the U.S. government taking a direct stake in the company, according to Bloomberg.\n\n"
            "Intel declined to comment.\n\n"
            "“Intel is deeply committed to supporting President Trump’s efforts to strengthen U.S. technology and manufacturing leadership,” an Intel spokesperson said in a statement. "
            "“We look forward to continuing our work with the Trump Administration to advance these shared priorities, but we are not going to comment on rumors or speculation.”\n\n"
            "We’re always looking to evolve, and by providing some insight into your perspective and feedback into TechCrunch and our coverage and events, you can help us! "
            "Fill out this survey to let us know how we’re doing and get the chance to win a prize in return!"
        ),
        "rss_categories": [
            "AI",
            "Enterprise",
            "Government & Policy",
            "AI chips",
            "In Brief",
            "Intel",
            "Lip-bu Tan",
            "semiconductors",
            "Trump Administration"
        ],
        "categories": [
            {"category": "Technology", "score": 0.9701311588287354},
            {"category": "AI & Machine Learning", "score": 0.8011420369148254},
            {"category": "Politics & Current Affairs", "score": 0.01350952684879303},
            {"category": "Startups & Entrepreneurship", "score": 0.009887760505080223},
            {"category": "Cloud Computing", "score": 0.003793698735535145}
        ]
    }


    print(send_to_gemini(article))

