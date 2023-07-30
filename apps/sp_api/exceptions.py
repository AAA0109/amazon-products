class BookHasHightBSRException(Exception):
    def __init__(self, bsr: int, asin: str):
        self.bsr = bsr
        self.asin = asin

    def __str__(self):
        return f"Book[{self.asin}] has height bsr = {self.bsr}"
