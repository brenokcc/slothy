
from slothy.api.ui.views import Markdown
from slothy.admin.ui import dashboard


@dashboard.public()
class Texto(Markdown):
    pass
