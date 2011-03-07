import re, yaml, logging
from datetime import datetime, timedelta

from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime, validate
from piston.utils import Mimer, FormValidationError

from vumi.webapp.api.models import SentSMS, ReceivedSMS, URLCallback
from vumi.webapp.api import forms
from vumi.webapp.api import signals
from vumi.webapp.api.utils import specify_fields

from alexandria.loader.base import YAMLLoader
from alexandria.dsl.utils import dump_menu

import pystache


class SendSMPPHandler(BaseHandler):
    allowed_methods = ('GET', 'POST',)
    exclude, fields = specify_fields(SentSMS,
        include=['transport_status_display'],
        exclude=['user','send_group'])

    def _send_one(self, **kwargs):
        kwargs.update({
            'transport_name': 'smpp'
        })
        form = forms.SentSMSForm(kwargs)
        if not form.is_valid():
            raise FormValidationError(form)
        send_sms = form.save()
        logging.debug('Scheduling an SMPP to: %s' % kwargs['to_msisdn'])
        return send_sms

    @throttle(6000, 60) # allow for 100 a second
    def create(self, request):
        form = forms.SendGroupForm({'title':'test group', 'user':request.user.pk})
        if not form.is_valid():
            raise FormValidationError(form)
        send_group = form.save()
        returnable = [self._send_one(
                                send_group=send_group.id,
                                user=request.user.pk,
                                to_msisdn=msisdn,
                                from_msisdn=request.POST.get('from_msisdn'),
                                message=request.POST.get('message'))
                    for msisdn in request.POST.getlist('to_msisdn')]
        signals.sms_scheduled.send(sender=SentSMS, instance=send_group,
                pk=send_group.pk)
        return {"send_group":send_group.id,
                "group_list":send_group.sentsms_set.all()}

