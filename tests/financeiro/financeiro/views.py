from slothy.api.ui.views import Markdown
from slothy.decorators import dashboard


@dashboard.public()
class Texto(Markdown):
    pass
