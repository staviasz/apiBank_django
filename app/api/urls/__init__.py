from .acounts import urlpatterns as accounts_urls
from .transations import urlpatterns as transations_urls

urlpatterns = accounts_urls + transations_urls
