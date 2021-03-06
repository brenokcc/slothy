
class View(object):

    def __init__(self, request):
        self.request = request

    def serialize(self):
        output = self.view()
        return output.serialize()


class Markdown(object):

    def __init__(self, request):
        self.request = request

    def markdown(self):
        pass

    def serialize(self):
        content = '''
# Hello World!
_I'm a Markdown file._
This is some code:
```
:)
```

## Teste 2

ok

## Test 2

Column 1 | Column 2 | Column 3
--- | --- | ---
**Things** | _Don't_ | [Need](http://makeuseof.com?id=2)
To | *__Look__* | `Pretty`

![Imagem](https://guides.github.com/images/logo@2x.png)

        '''
        return dict(type='markdown', content=content)
