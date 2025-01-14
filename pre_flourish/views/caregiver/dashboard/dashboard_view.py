from django.apps import apps as django_apps
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from edc_base.view_mixins import EdcBaseViewMixin
from edc_constants.constants import NO
from edc_dashboard.views import DashboardView as BaseDashboardView
from edc_navbar import NavbarViewMixin
from edc_registration.models import RegisteredSubject
from edc_subject_dashboard.view_mixins import SubjectDashboardViewMixin

from pre_flourish.action_items import MATERNAL_DEATH_STUDY_ACTION
from pre_flourish.model_wrappers import AppointmentModelWrapper, \
    MaternalCrfModelWrapper, \
    PreFlourishSubjectConsentModelWrapper
from pre_flourish.model_wrappers import (MaternalVisitModelWrapper,
                                         PreflourishCaregiverLocatorModelWrapper,
                                         PreFlourishDataActionItemModelWrapper)
from ...view_mixins.dashboard_view_mixin import DashboardViewMixin
from ....models import PFDataActionItem


class DashboardView(DashboardViewMixin, EdcBaseViewMixin, SubjectDashboardViewMixin,
                    NavbarViewMixin, BaseDashboardView):
    dashboard_url = 'pre_flourish_subject_dashboard_url'
    dashboard_template = 'pre_flourish_subject_dashboard_template'
    appointment_model = 'pre_flourish.appointment'
    appointment_model_wrapper_cls = AppointmentModelWrapper
    crf_model_wrapper_cls = MaternalCrfModelWrapper
    consent_model = 'pre_flourish.preflourishconsent'
    consent_model_wrapper_cls = PreFlourishSubjectConsentModelWrapper
    screening_model = 'pre_flourish.preflourishsubjectscreening'
    navbar_name = 'pre_flourish_dashboard'
    navbar_selected_item = 'pre_flourish_consent'
    subject_locator_model = 'flourish_caregiver.caregiverlocator'
    subject_locator_model_wrapper_cls = PreflourishCaregiverLocatorModelWrapper
    visit_model_wrapper_cls = MaternalVisitModelWrapper
    mother_infant_study = True
    infant_links = True
    infant_subject_dashboard_url = 'pre_flourish_child_dashboard_url'
    infant_dashboard_include_value = \
        'pre_flourish/caregiver/dashboard/infant_dashboard_links.html'
    special_forms_include_value = 'pre_flourish/caregiver/dashboard/special_forms.html'
    visit_attr = 'preflourishvisit'

    @property
    def appointments(self):
        """Returns a Queryset of all appointments for this subject.
        """
        if not self._appointments:
            self._appointments = self.appointment_model_cls.objects.filter(
                subject_identifier=self.subject_identifier).order_by(
                'visit_code')
        return self._appointments

    @property
    def consent_model_cls(self):
        return django_apps.get_model(self.consent_model)

    @property
    def screening_model_cls(self):
        return django_apps.get_model(self.screening_model)

    @property
    def subject_locator_model_cls(self):
        return django_apps.get_model(self.subject_locator_model)

    @property
    def subject_consent(self):
        try:
            consent = self.consent_model_cls.objects.get(
                subject_identifier=self.subject_identifier[:17]
            )
        except self.consent_model_cls.DoesNotExist:
            pass
        else:
            return consent

    @property
    def subject_locator(self):
        """Returns a model instance either saved or unsaved.

        If a save instance does not exits, returns a new unsaved instance.
        """

        screening_identifier = getattr(self.subject_consent, 'screening_identifier')

        subject_locator_obj = None

        try:
            screening_obj = self.screening_model_cls.objects.get(
                screening_identifier=screening_identifier
            )
        except self.screening_model_cls.ObjectDoesNotExist:
            pass
        else:
            subject_locator_objs = self.subject_locator_model_cls.objects.filter(
                study_maternal_identifier=screening_obj.study_maternal_identifier
            )
            if not subject_locator_objs:
                try:
                    subject_locator_obj = self.subject_locator_model_cls.objects.get(
                        subject_identifier=self.consent.subject_identifier
                    )
                except self.subject_locator_model_cls.DoesNotExist:
                    pass
                else:
                    subject_locator_obj = subject_locator_obj
            else:
                subject_locator_obj = subject_locator_objs.first()
        return subject_locator_obj

    @property
    def data_action_item(self):
        """Returns a wrapped saved or unsaved consent version.
        """
        model_obj = PFDataActionItem(subject_identifier=self.subject_identifier)
        return PreFlourishDataActionItemModelWrapper(model_obj=model_obj)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locator_obj = self.get_locator_info()
        caregiver_offstudy_cls = django_apps.get_model(
            'pre_flourish.preflourishdeathreport')
        caregiver_visit_cls = django_apps.get_model(
            'pre_flourish.preflourishvisit')

        self.get_offstudy_or_message(
            visit_cls=caregiver_visit_cls,
            offstudy_cls=caregiver_offstudy_cls,
            offstudy_action=MATERNAL_DEATH_STUDY_ACTION)

        self.get_offstudy_message(offstudy_cls=caregiver_offstudy_cls)
        self.get_subject_locator_message()
        context.update(
            infant_registered_subjects=self.infant_registered_subjects,
            locator_obj=locator_obj,
            data_action_item_add_url=self.data_action_item.href,
            subject_consent=self.consent_wrapped,
            pre_flourish_subject_dashboard_url=self.dashboard_url,
            schedule_names=[model.schedule_name for model in self.onschedule_models], )
        return context

    def set_current_schedule(self, onschedule_model_obj=None,
                             schedule=None, visit_schedule=None,
                             is_onschedule=True):
        if onschedule_model_obj:
            if is_onschedule:
                self.current_schedule = schedule
                self.current_visit_schedule = visit_schedule
                self.current_onschedule_model = onschedule_model_obj
            self.onschedule_models.append(onschedule_model_obj)
            self.visit_schedules.update(
                {visit_schedule.name: visit_schedule})

    def get_onschedule_model_obj(self, schedule):
        try:
            return schedule.onschedule_model_cls.objects.get(
                subject_identifier=self.subject_identifier,
                schedule_name=schedule.name)
        except ObjectDoesNotExist:
            return None

    def get_locator_info(self):

        subject_identifier = self.kwargs.get('subject_identifier')
        try:
            obj = self.subject_locator_model_cls.objects.get(
                subject_identifier=subject_identifier)
        except ObjectDoesNotExist:
            return None
        return obj

    @property
    def infant_registered_subjects(self):
        """Returns an infant registered subjects.
        """
        subject_identifier = self.kwargs.get('subject_identifier')
        registered_subject = RegisteredSubject.objects.filter(
            relative_identifier=subject_identifier)
        if registered_subject:
            return registered_subject

    def get_subject_locator_message(self):
        """
        Overridden to stop system from generating subject locator
        action items for child.
        """
        update_caregiver_locator_model = django_apps.get_model(
            'pre_flourish.updatecaregiverlocator')

        try:
            obj = update_caregiver_locator_model.objects.get(
                subject_identifier=self.subject_identifier)
        except update_caregiver_locator_model.DoesNotExist:
            self.prompt_locator()
        else:
            if obj.is_locator_updated == NO:
                self.prompt_locator()

    def prompt_locator(self):
        message = 'Please update caregiver locator and complete the Update caregiver ' \
                  'locator forms under special forms'
        messages.error(self.request, message)
