# -*- coding: UTF-8 -*-
"""URL dispatcher for lead module
@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license: AGPL v3 or newer (http://www.gnu.org/licenses/agpl-3.0.html)
"""

from django.conf.urls import patterns, url


leads_urls = patterns('leads.views',
                      (r'^review', 'review'),
                      (r'^csv/(?P<target>.*)', 'csv_export'),
                      (r'^tag/(?P<tag_id>\d+)/$', 'tag'),
                      (r'^tags/(?P<lead_id>\d+)$', 'tags'),
                      (r'^tag/add$', 'add_tag'),
                      (r'^tag/remove/(?P<tag_id>\d+)/(?P<lead_id>\d+)$', 'remove_tag'),
                      (r'^(?P<lead_id>\d+)/$', 'detail'),
                      (r'^lead$', 'lead'),
                      (r'^lead/(?P<lead_id>\d+)/change$', 'lead'),
                      (r'^documents/(?P<lead_id>\d+)/$', 'lead_documents'),
                      (r'^sendmail/(?P<lead_id>\d+)/$', 'mail_lead'),
                      url(r'^mail/text', 'summary_mail', {"html": False}, name="lead-mail-text"),
                      url(r'^mail/html', 'summary_mail', {"html": True}, name="lead-mail-html"),
                      (r'^graph/bar-jqp$', 'graph_bar_jqp'),
                      )
