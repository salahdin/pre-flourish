from edc_visit_schedule import FormsCollection, Crf

caregiver_crfs_1000 = FormsCollection(
    Crf(show_order=1, model='pre_flourish.cyhuupreenrollment'),
    Crf(show_order=2, model='pre_flourish.updatecaregiverlocator'),
    name='enrollment')
