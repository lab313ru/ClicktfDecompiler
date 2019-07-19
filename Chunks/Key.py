from keyconvert import getKeyText


class Key:

    def __init__(self, value=None):
        self.value = value

    def get_name(self):
        return getKeyText(self.value)

    def get_value(self):
        return self.value

    def set_value(self, input):
        self.value = input

    def __repr__(self):
        return self.get_name()
