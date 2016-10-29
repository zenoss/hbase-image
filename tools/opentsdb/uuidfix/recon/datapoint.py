class ParseError(Exception):
    pass


class Datapoint(object):
    """
    Represents a datapoint from openTSDB
    """
    def __init__(self, s=""):
        fields = s.split()
        if len(fields) < 3:
            raise ParseError("Not enough fields in input")
        self.name = fields[0]
        try:
            self.date = int(fields[1])
        except ValueError:
            raise ParseError("Bad Date in input ({})".format(fields[1]))
        try:
            self.value = float(fields[2])
        except ValueError:
            raise ParseError("Bad Value in input")
        self.tags = {}
        for field in fields[3:]:
            key, value = field.split('=')
            self.tags[key]=value

    def __str__(self):
        return str(self.__dict__)

    def MetricName(self):
        return self.name

    def Timestamp(self):
        return self.date

    def Value(self):
        return self.value

    def Tags(self):
        return self.tags

    def Tag(self, key):
        try:
            return self.tags[key]
        except KeyError:
            return None

