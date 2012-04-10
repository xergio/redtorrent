from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'tracker.views.announce', name='announce'),
    url(r'^announce', 'tracker.views.announce', name='announce'),
    url(r'^scrape$', 'tracker.views.scrape', name='scrape'),
)
