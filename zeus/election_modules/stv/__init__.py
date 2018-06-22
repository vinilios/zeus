import json
import os
import zipfile
import logging
import StringIO

from django.utils.translation import ugettext_lazy as _
from django.forms.formsets import formset_factory
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.conf import settings

from zeus.election_modules import ElectionModuleBase, election_module
from zeus.views.utils import set_menu

from helios.view_utils import render_template
from stv.stv import count_stv, Ballot
from zeus.core import gamma_decode, to_absolute_answers

from zeus.election_modules.unicouncilsgr import UniCouncilsGr

@election_module
class StvElection(UniCouncilsGr):
    module_id = 'stv'
    description = _('Single transferable vote election')
    department_limit_label = _("Maximum elected from the same constituency")

    booth_module_id = 'stv'

    pdf_result = True
    csv_result = True
    json_result = True

    @property
    def questions_form_cls(self):
        from zeus.forms import StvForm
        return StvForm

    def questions_form_initial(self, poll):
        if not poll.questions_data:
            poll.questions_data = [{'droop_quota': True}]

        poll.questions_data[0]['departments_data'] = poll.election.departments
        initial = poll.questions_data
        return initial

