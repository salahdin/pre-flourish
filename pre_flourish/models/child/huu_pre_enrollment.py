from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from edc_base.model_validators import date_not_future, dob_not_today
from edc_constants.choices import YES_NO, GENDER

from ..model_mixins import CrfModelMixin
from ...choices import POS_NEG_IND, YES_NO_UNKNOWN


class HuuPreEnrollment(CrfModelMixin):

    child_hiv_docs = models.CharField(
        verbose_name='Is there documentation of the child’s HIV status?',
        choices=YES_NO,
        max_length=3, )

    child_hiv_result = models.CharField(
        verbose_name='HIV test result',
        choices=POS_NEG_IND,
        max_length=14,
        blank=True,
        null=True)

    child_test_date = models.DateField(
        verbose_name='Date of test',
        validators=[date_not_future, ],
        blank=True,
        null=True)

    weight = models.IntegerField(
        verbose_name='Weight (kg)',
        validators=[MinValueValidator(15), MaxValueValidator(140), ],
    )

    height = models.IntegerField(
        verbose_name='Height (cm)',
        validators=[MinValueValidator(40), MaxValueValidator(210), ],
    )

    bmi = models.IntegerField(blank=True, null=True)

    knows_gest_age = models.CharField(
        verbose_name='Does the caregiver know the gestational age of the '
                     'child?',
        max_length=3,
        choices=YES_NO)

    gestational_age = models.IntegerField(
        verbose_name='What is the Gestational Age of the child/adolescent?',
        null=True,
        blank=True,
        validators=[MaxValueValidator(42), MinValueValidator(24)])

    premature_at_birth = models.CharField(
        verbose_name='Was the child/adolescent premature when born?',
        choices=YES_NO_UNKNOWN,
        max_length=20,
        help_text='Preterm birth is a birth that occurs before 37 weeks '
                  'gestation. You may have to ask the mother if this child was'
                  ' born earlier than she was told to expect the child, right '
                  'at the same time, or after.')

    breastfed = models.CharField(
        verbose_name='Was your child breastfed?',
        choices=YES_NO_UNKNOWN,
        max_length=8)

    months_breastfeed = models.IntegerField(
        verbose_name='Approximately how many months did this child breastfeed,'
                     ' including periods where the child was breast feeding '
                     'and taking formula and solid foods together?',
        validators=[MaxValueValidator(30), MinValueValidator(1)],
        blank=True,
        null=True)

    class Meta:
        app_label = 'pre_flourish'
        verbose_name = 'HUU Pre-Enrollment'
        verbose_name_plural = 'HUU Pre-Enrollment'
