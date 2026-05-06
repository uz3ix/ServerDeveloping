class CustomExceptionA(Exception):
    def __init__(self, message: str = "Business rule is not satisfied"):
        self.message = message


class CustomExceptionB(Exception):
    def __init__(self, message: str = "Requested resource was not found"):
        self.message = message
