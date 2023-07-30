import re


def generate_acronym(full_phrase: str) -> str:
    """Helper function to generate acronyms of book titles up to 10 characters in length for the creation of new campaigns"""
    # Take only the title which is delimited by colon in the full title of the book
    title_length = full_phrase.find(":")
    if title_length > 0:
        full_phrase = full_phrase[:title_length]
        full_phrase = full_phrase.strip()
    # Getting rid of 'of' word using replace() method & Spiliting the user input into individual words using split() method
    phrase = (re.sub(r"[^\w\s]", "", full_phrase)).split()
    # Initializing an empty string to append the acronym
    a = ""
    # for loop to append acronym
    for word in phrase:
        a = a + word[0].upper()
    return a[:10]