import warnings

import openai
import requests
from dotenv import dotenv_values
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter("ignore", InsecureRequestWarning)

env_vars = dotenv_values(".env")
key = env_vars["OPENAI_API_KEY"]
openai.api_key = key

# MODEL = "gpt-3.5-turbo"
MODEL = "gpt-4"


def chat_gpt(system_role: str, prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": prompt},
            # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            # {"role": "user", "content": "Where was it played?"}
        ],
    )
    text = response["choices"][0]["message"]["content"]
    # formatted_text = text.strip().replace('\n', '\r\n')
    return text


############################################################################################
############################################################################################


def get_suggestions(list_of_keywords: list[str]):
    url = "https://completion.amazon.com/api/2017/suggestions"

    params = {
        "limit": 11,
        "suggestion-type": ["WIDGET", "KEYWORD"],
        "page-type": "Search",
        "alias": "stripbooks",  # this sets the dropdown  "digital-text" for kindle    "audible" for audiobooks
        "site-variant": "desktop",
        "version": 3,
        "event": "onfocuswithsearchterm",
        "wc": "",
        "lop": "en_US",
        "last-prefix": "\x00",
        "avg-ks-time": 0,
        "fb": 1,
        # "session-id": "132-2576429-7940920",
        # "request-id": "D036R6XJJ9K1HS7VV2BK",
        "mid": "ATVPDKIKX0DER",
        "plain-mid": 1,
        "client-info": "amazon-search-ui",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-GB,en;q=0.5",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "referrer": "https://www.amazon.com/",
    }

    cookies = {
        # "session-id": "132-2576429-7940920",
        # "session-id-time": "2082787201l",
        "i18n-prefs": "USD",
        # "sp-cdn": "L5Z9:AE",
        # "ubid-main": "131-4049986-6820324",
        # "session-token": "hRfk+qpGXsTkDAeW7Ezv/wmCHZ4CxmZ3qIRBCpBoWPYdtSK1bPaC+dFTiYPp6iLR57eG9sMR5Q0HxKcSjazjBA7eMnTVY7+3pGMXEvIFKTn7QpUzhtDdooi0P1GBk5xByBtObrvGqvFgLuzG7L/BfxwbNSEDaw3NU/kvYXvxjNxJyVHdG+0owhdI5xgGchGohx3uKVk2ahM8Mc18ZXwMv0sI00Yzj7YEm/IpsJaPJtI=",
    }

    all_suggestions = []

    for keyword in list_of_keywords:
        params.update({"prefix": keyword})

        response = requests.get(url, params=params, headers=headers, cookies=cookies, verify=False)

        # Extract keyword values from response
        if response.status_code == 200:
            data = response.json()
            if "suggestions" in data:
                keyword_values = []
                for suggestion in data["suggestions"]:
                    if suggestion["type"] == "KEYWORD":
                        keyword_values.append(suggestion["value"])
        else:
            print("Request failed with status code: ", response.status_code)
            break

        for new_kw in keyword_values:
            if new_kw not in all_suggestions:
                all_suggestions.append(new_kw)

    return all_suggestions


def extract_list_string(input_string: str) -> list[str]:
    start_index = input_string.find("[")
    end_index = input_string.find("]")
    my_list = input_string[start_index : end_index + 1]
    my_list = my_list.strip("[]").replace("'", "")
    my_list = my_list.split(", ")
    return my_list


list_of_keywords = [
    "Personal Development",
    "Self-Help",
    "Motivation",
    "Mindset Shift",
    "Athletic Training",
    "Leadership Development",
    "High Performers",
    "Goal Setting",
    "Success Habits",
    "Performance Improvement",
    "Discipline",
    "Health & Fitness",
    "Focus",
    "Productivity",
    "Professional Growth",
    "Personal Growth",
    "Mental Strength",
    "Elite Athletes",
    "Powerful Habits",
    "Achievement",
    "Life Changes",
    "Inspirational",
    "Mind-body Connection",
    "Purpose Finding",
    "Time Management",
    "Awareness and Self-Control",
    "Human Capacity",
    "Peak Performance",
    "Fitness and Wellness",
    "Stress Management",
    "Lifestyle Changes",
    "Performance Psychology",
    "Emotional Intelligence",
    "Self-Improvement",
    "Decision Making",
    "Transformative",
    "Executive Leadership",
    "Mental Health",
    "Success Principles",
    "Physical Health",
    "Self Mastery",
    "Overcoming Distractions",
    "Organizational Skills",
    "Sports Psychology",
    "Resilience Training",
    "Personal Power",
    "Fitness Motivation",
    "Self-Discipline",
    "Emotional Discipline",
    "Mindfulness",
]

all_suggestions = [
    "personal development books",
    "self-help and personal development books",
    "personal development",
    "personal growth and development",
    "self-help",
    "books best sellers new releases 2023 self help",
    "self-help books",
    "self help books for women",
    "self help books for men",
    "self help journal for women",
    "best self help books",
    "self help books for mental health",
    "motivational books",
    "motivational interviewing",
    "motivation",
    "motivational books for women",
    "motivational interviewing book",
    "motivation book",
    "motivation notebook",
    "motivational water bottle",
    "motivational notebooks for girls",
    "motivational books for men",
    "mindset shift",
    "mindset dweck",
    "mindset matters",
    "mind shift",
    "athletic training boc prep book",
    "principles of athletic training",
    "leadership development toolkit",
    "high performers journal",
    "goal setting",
    "goal setting journal",
    "goal setting book",
    "goal-setting and action planning to address anger-issues",
    "atomic affirmations for success habits",
    "performance improvement plan",
    "discipline equals freedom",
    "discipline is destiny",
    "discipline",
    "discipline is destiny ryan holiday",
    "discipline book",
    "celebration of discipline by richard foster",
    "disciplines of a godly man by r. kent hughes",
    "disciplines of a godly woman",
    "positive discipline",
    "no drama discipline book",
    "health and fitness",
    "health and fitness books",
    "focus",
    "stolen focus why you can't pay attention",
    "focus book",
    "focus on grammar 5",
    "focusing eugene gendlin",
    "focus on the family radio theatre",
    "focus select areds2",
    "focus on the family",
    "stolen focus johann hari paperback",
    "focus by chris jansmann",
    "productivity",
    "productivity book",
    "productivity journal",
    "productivity books best sellers",
    "the productivity project",
    "books about productivity",
    "debt payoff planner productivity partners",
    "professional growth book",
    "irestore professional laser hair growth system",
    "personal growth",
    "personal growth books",
    "personal growth journal",
    "rise above unleashing inner resilience for personal growth",
    "mental strength bracelet",
    "elite athlete",
    "powerful habits",
    "power of habits",
    "dangerous habits",
    "habits of highly effective people",
    "from ashes to achievement a jewish journey in america",
    "life changes book",
    "inspirational books",
    "inspirational quotes coloring book for adults",
    "inspirational quotes coloring book",
    "inspirational books for women",
    "inspirational books for kids",
    "inspirational coloring book for adults",
    "inspirational quotes",
    "inspirational quotes book",
    "inspirational sports stories for young readers",
    "inspirational coloring book",
    "mind body connection",
    "finding purpose",
    "finding your purpose",
    "finding purpose in life",
    "time management",
    "time management for teens",
    "time management book",
    "time management quotes",
    "time management books best sellers",
    "time management planner",
    "time management with action plan",
    "time management for mortals oliver",
    "mind management not time management",
    "human capacity in the attention economy",
    "human motivation",
    "human performance",
    "human intelligence",
    "peak performance",
    "peak performance culture book",
    "fitness and wellness book",
    "stress management",
    "a stress management guide for moms",
    "stress management book",
    "stress management workbook",
    "lifestyle changes",
    "lifestyle games",
    "lifestyle by focus",
    "lifestyle solutions",
    "performance psychology",
    "emotional intelligence",
    "emotional intelligence 2.0",
    "emotional intelligence book daniel goleman",
    "emotional intelligence 2.0 book",
    "emotional intelligence for kids",
    "emotional intelligence 2.0 book with access code",
    "emotional intelligence for leadership",
    "the color of emotional intelligence",
    "self-improvement books",
    "self improvement books best sellers",
    "self improvement books for women",
    "self improvement",
    "self improvement books for men",
    "self improvement journal",
    "best self improvement books",
    "best seller books 2023 self improvement",
    "self improvement journal for women",
    "decision making",
    "decision making books",
    "medical decision making",
    "ethical leadership and decision making in education",
    "my ultimate decision-making trainer",
    "transformative learning mezirow",
    "executive leadership books",
    "mental health journal for men",
    "mental health books",
    "mental health",
    "mental health workbook",
    "mental health journal",
    "mental health for teens",
    "mental health awareness",
    "mental health books for women",
    "mental health journal for women",
    "mental health workbooks for women",
    "the success principles by jack canfield",
    "home health physical therapy",
    "physical examination and health assessment",
    "self mastery",
    "overcoming distractions thriving with adult add/adhd",
    "overcoming anxiety",
    "overcoming obsessive thoughts",
    "overcoming intrusive thoughts",
    "organizational skills teenagers",
    "sports psychology",
    "sports psychology books for athletes",
    "resilience training",
    "resilience factor",
    "resitance training",
    "nurturing resilience",
    "personal power anthony robbins",
    "fitness motivation art",
    "self discipline for teens",
    "the power of self discipline",
    "mastering self discipline",
    "emotional discipline",
    "mindfulness",
    "mindfulness cards",
    "mindfulness journal",
    "mindfulness for kids",
    "mindfulness book",
    "mindfulness in plain english",
    "mindfulness coloring book",
    "mindfulness coloring book for adults",
    "mindfulness books for adults",
    "mindfulness workbook",
]

book_title = "THE UNDENIABLE POWER OF MOVEMENT THE IRREFUTABLE POWER HABITS OF ELITE ATHLETES, LEADERS, & HIGH PERFORMERS TO ACHIEVE ANY GOAL"

system_role = "You are a terminal interface helping a publisher advertise books on Amazon"

avatar_description = "The target reader is likely a male or female, aged between 18 to 60 years. They embody the driven spirit of the ambitious modern individual, drawn by the allure of success and the pursuit of peak performance. This individual takes pleasure in exploring the edges of their potential and is always looking for ways to push beyond their existing boundaries. They may already be an athlete seeking to reach the top echelons of their sport, a corporate leader endeavoring to maximize their leadership prowess, or an aspiring high performer in any field, thirsty for actionable strategies to elevate their game. But equally, they could be a beginner, someone looking to jumpstart their journey towards self-improvement, attracted by the promise of unlocking the undeniable power mentioned in the book's title. This reader is fascinated by the habits of the successful, often reading biographies and self-help books in their spare time. They are drawn to scientific, evidence-based methods, and hence, are likely to appreciate the irrefutable power habits discussed in this book. They understand the value of consistency and discipline, and are eager to transform their daily routines to become more productive and efficient. They're not afraid of hard work, and they know that greatness is often found in the small, everyday actions that others overlook. With a growth mindset, they believe that they can learn and grow from every experience. They're resilient, able to bounce back from failures and see them as opportunities to learn rather than setbacks. They understand the power of mental and physical movement, and they're intrigued by the prospect of learning how elite athletes, leaders, and high performers leverage this power to achieve their goals. In a nutshell, the target reader is a motivated individual, regardless of their current status or field, who has a keen interest in personal development and a strong desire to achieve their peak potential. They are driven, persistent, and open-minded, ready to embrace the power of movement and habits to transform their life and reach their ultimate goals."

# Get keywords
if len(list_of_keywords) == 0:
    prompt = f"suggest main keywords to advertise book titled {book_title} and output the result as a Python list only (pretend you are a console interface)"
    keyword_str = chat_gpt(system_role=system_role, prompt=prompt)
    list_of_keywords = extract_list_string(input_string=keyword_str)
    print(f"List of keywords: {str(list_of_keywords)}")

# Get suggestions
if len(all_suggestions) == 0:
    all_suggestions = get_suggestions(list_of_keywords=list_of_keywords)
    print(f"Suggestions: {str(all_suggestions)}")

# Filter out irrelevant suggestions
prompt = f"remove irrelevant entries from list of keywords to advertise book titled {book_title} and output the result as a Python list only (pretend you are a console interface). Consider the following target reader description when deciding which keywords to remove: {avatar_description}. Keywords: {str(all_suggestions)}"
system_role = "you are an advertising bot that understands the target market well"
only_relevants = chat_gpt(system_role=system_role, prompt=prompt)
only_relevants_list = extract_list_string(input_string=only_relevants)
print(f"Relevant keywords: {str(only_relevants_list)}")


############################################################################################
############################################################################################

# Testing

# Input keywords
# ["natural remedies", "healing", "plant medicine"]

# Suggestions
# [
#     "natural remedies book",
#     "natural remedies encyclopedia",
#     "natural remedies",
#     "natural remedies for essential tremors",
#     "herbal medicine book natural remedies",
#     "natural health remedies book",
#     "natural essential oil remedies",
#     "barbara o'neill natural remedies",
#     "the best natural remedies for headaches",
#     "medicinal herbs natural holistic healing books remedies",
#     "healing after loss martha hickman",
#     "healing the soul of a woman joyce meyer",
#     "healing the shame that binds you",
#     "healing books",
#     "healing back pain john sarno",
#     "healing from infidelity",
#     "healing herbs",
#     "healing inner child workbook",
#     "healing from a narcissistic relationship",
#     "healing hands",
#     "plant medicine encyclopedia",
# ]

# Filtered list
# [
#     "natural remedies book",
#     "natural remedies encyclopedia",
#     "natural remedies",
#     "herbal medicine book natural remedies",
#     "natural health remedies book",
#     "natural essential oil remedies",
#     "barbara o'neill natural remedies",
#     "the best natural remedies for headaches",
#     "medicinal herbs natural holistic healing books remedies",
#     "plant medicine encyclopedia",
# ]

# Another prompt for input keywords

# Suggest main keywords to advertise book titled: {book_title}


##############################################################
##############################################################

# List of keywords: ['herb garden', 'herbal medicine', 'sustainable living', 'self-sufficiency', 'natural remedies', 'organic gardening', 'health benefits', 'herbal remedies', 'common ailments', 'seed starting', 'medicinal herbs', 'plant care', 'herbal tea', 'composting', 'essential oils', 'culinary herbs']
# Suggestions: ['herb gardening', 'herb garden', 'herb garden kit indoor', 'herb gardening books for beginners', 'container herb gardening book', "danu's irish herb garden", 'medicinal herb garden book', 'herbal medicine for beginners', 'herbal medicine', 'herbal medicine book natural remedies', 'encyclopedia of herbal medicine', 'herbal medicine recipe book', 'grow your own herbal medicine', 'encyclopedia of herbal medicine book', 'herbal remedies and natural medicine bible', 'japanese herbal medicine', 'sustainable living', 'self sufficiency', 'natural remedies book', 'natural remedies encyclopedia', 'natural remedies', 'natural remedies for essential tremors', 'natural health remedies book', 'natural essential oil remedies', "barbara o'neill natural remedies", 'the best natural remedies for headaches', 'medicinal herbs natural holistic healing books remedies', 'organic gardening', 'organic gardening book', 'organic gardening for beginners', 'organic vegetable gardening', 'home gardening universal slow-release tablet organic fertilizer', 'infared sauna blanket/health benefits/weight loss higher dose', 'what is the health benefits of saltwater', 'herbal remedies handbook', 'herbal remedies book', 'herbal remedies', 'herbal remedies for beginners', 'lost book of herbal remedies dr. nicole apelian', 'the lost book of herbal remedies', 'natural herbal remedies book', 'the lost book of herbal remedies by nicole apelian', 'seed starting heat pad', 'seed starting', 'espoma seed starting mix', "medicinal herbs a beginner's guide", 'medicinal herbs', 'book on herbs and plants medicinal use', 'medicinal herbs for beginners', 'peterson field guide to medicinal plants and herbs', 'medicinal plants and herbs', 'planting herbs for medicinal purposes', 'plant care book', 'plant care journal', 'house plant book identification and care', 'house plant care', 'house plant care book', 'outdoor plant care', 'herbal teas', 'healing herbal teas', 'herbal tea book', 'composting for dummies', 'composting', 'composting book', 'composting spinner', 'composting books for beginners', 'kindle books composting', 'worm composting', 'organic composting book', 'essential oils book', 'essential oils books for beginners', 'essential oils for healing', 'essential oils books reference', 'diffusers for essential oils large room', 'stephanie ariel essential oils', 'dr teals sleep lotion with melatonin and essential oils']
# Relevant keywords: ['herb gardening', 'herb garden', 'herb gardening books for beginners', 'container herb gardening book', 'medicinal herb garden book', 'herbal medicine for beginners', 'herbal medicine', 'herbal medicine book natural remedies', 'encyclopedia of herbal medicine', 'herbal medicine recipe book', 'grow your own herbal medicine', 'encyclopedia of herbal medicine book', 'herbal remedies and natural medicine bible', 'japanese herbal medicine', 'sustainable living', 'self sufficiency', 'natural remedies book', 'natural remedies encyclopedia', 'natural remedies', 'natural remedies for essential tremors', 'natural health remedies book', 'natural essential oil remedies', 'herbal remedies handbook', 'herbal remedies book', 'herbal remedies', 'herbal remedies for beginners', 'lost book of herbal remedies dr. nicole apelian', 'the lost book of herbal remedies', 'natural herbal remedies book', 'the lost book of herbal remedies by nicole apelian', 'medicinal herbs a beginners guide', 'medicinal herbs', 'book on herbs and plants medicinal use', 'medicinal herbs for beginners', 'peterson field guide to medicinal plants and herbs', 'medicinal plants and herbs', 'planting herbs for medicinal purposes', 'herbal teas', 'healing herbal teas', 'herbal tea book']
