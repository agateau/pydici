from django.conf.urls import patterns


incwo_urls = patterns('batch.incwo.views',
                      (r'^/?$', 'imports'),
                      )
