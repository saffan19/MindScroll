import os
from dotenv import load_dotenv
import json
import google.generativeai as genai
from dotenv import load_dotenv

# This should be at the very top of your script
load_dotenv()

API_KEY = os.getenv("API_KEY")

PROMPT = """
You are given the following reference data. Your task is to create a short, engaging, and entertaining post from it.

The post will later be converted to a voice format, so it must:
- Be conversational and engaging
- Be concise while retaining the essence of the reference data
- You can add more relevant information if needed, but it must be relevant to the topic
- Use a friendly and approachable tone
- Avoid technical jargon or complex language

Return your answer strictly as a JSON object with these keys:
- title: A catchy, relevant title for the post
- content: The engaging and concise content for the post
- tags: A list of 3-7 relevant tags
- difficulty: One of ["easy", "medium", "hard"]
- rating: One of ["U", "UA", "A", "S"]

Here is your data:
"""




def send_to_gemini(article, prompt_template=None):
    if prompt_template is None:
        prompt_template = (
            PROMPT +
            "\n\n"
            "{data}\n"
        )
    article_str = json.dumps(article, indent=2)
    prompt = prompt_template.format(data=article_str)
    print(API_KEY)
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(prompt)
    return response.text

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

