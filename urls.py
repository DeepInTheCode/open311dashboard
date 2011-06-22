from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'open311dashboard.dashboard.views.index'),
    url(r'^tickets/$', 'open311dashboard.dashboard.views.ticket_days'),
    url(r'^tickets/(?P<ticket_status>\w+)/$', 'open311dashboard.dashboard.views.ticket_days'),
    url(r'^tickets/(?P<ticket_status>\w+)/(?P<start>.+)/(?P<end>.+)/$', 'open311dashboard.dashboard.views.ticket_days'),
    # Examples:
    # url(r'^$', 'open311dashboard.views.home', name='home'),
    # url(r'^open311dashboard/', include('open311dashboard.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)