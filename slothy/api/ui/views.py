
class View(object):

    def __init__(self, request):
        self.request = request

    def serialize(self):
        output = self.view()
        return output.serialize()
