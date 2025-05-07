from django import forms
from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
from api.models import Death, Staff


class FormUtils:
    @classmethod
    def label_widget_attrs(cls, **kwargs):
        attrs = {
            'class': 'form-input',
        }

        attrs.update(kwargs)
        return attrs

    @classmethod
    def char_widget_attrs(cls, readonly=False, **kwargs):
        attrs = {
            'class': 'form-input',
        }
        if readonly:
            attrs['readonly'] = 'readonly'

        attrs.update(kwargs)
        return attrs

    @classmethod
    def date_widget_attrs(cls, readonly=False, **kwargs):
        attrs = {
            'type': 'date',
            'class': 'form-input',
        }
        if readonly:
            attrs['readonly'] = 'readonly'

        attrs.update(kwargs)
        return attrs

    @classmethod
    def select_widget_attrs(cls, readonly=False, **kwargs):
        attrs = {
            'class': 'select select-bordered form-input',
        }
        if readonly:
            attrs['disabled'] = 'disabled'

        attrs.update(kwargs)
        return attrs

    @classmethod
    def label_field(cls, choices=None, **kwargs):
        if 'widget' not in kwargs:
            widget_attrs = cls.label_widget_attrs()
            kwargs['widget'] = cls.LabelWidget(attrs=widget_attrs, choices=choices)
        if 'required' not in kwargs:
            kwargs['required'] = False
        return forms.CharField(**kwargs)

    @classmethod
    def char_field(cls, readonly=False, **kwargs):
        if 'widget' not in kwargs:
            widget_attrs = cls.char_widget_attrs(readonly=readonly)
            kwargs['widget'] = forms.TextInput(attrs=widget_attrs)
        return forms.CharField(**kwargs)

    @classmethod
    def date_field(cls, readonly=False, **kwargs):
        if 'widget' not in kwargs:
            widget_attrs = cls.date_widget_attrs(readonly=readonly)
            kwargs['widget'] = forms.DateInput(attrs=widget_attrs)
        return forms.DateField(**kwargs)

    @classmethod
    def choice_field(cls, readonly=False, **kwargs):
        if 'widget' not in kwargs:
            widget_attrs = cls.select_widget_attrs(readonly=readonly)
            kwargs['widget'] = forms.Select(attrs=widget_attrs)
        return forms.ChoiceField(**kwargs)

    @classmethod
    def typed_choice_field(cls, readonly=False, **kwargs):
        if 'widget' not in kwargs:
            widget_attrs = cls.select_widget_attrs(readonly=readonly)
            kwargs['widget'] = forms.Select(attrs=widget_attrs)
        return forms.TypedChoiceField(**kwargs)

    @classmethod
    def model_choice_field(cls, readonly=False, **kwargs):
        if 'widget' not in kwargs:
            widget_attrs = cls.select_widget_attrs(readonly=readonly)
            kwargs['widget'] = forms.Select(attrs=widget_attrs)
        return forms.ModelChoiceField(**kwargs)

    class LabelWidget(Widget):
        def __init__(self, choices=None, *args, **kwargs):
            self.choices = dict(choices) if choices else None
            super().__init__(*args, **kwargs)

        def render(self, name, value, attrs=None, renderer=None):
            display_value = (value or '') if self.choices is None else self.choices.get(value, '')
            hidden_input = '<input type="hidden" name="{name}" value="{value}">'.format(name=name, value=value or '')
            label = '<label>{display_value}</label>'.format(display_value=display_value)
            return mark_safe(hidden_input + label)


class DeathForm(forms.ModelForm):
    death_code = FormUtils.label_field(label="Death ID")
    death_status = FormUtils.label_field(label='Status', choices=Death.DeathStatus.choices)
    respondent_name = FormUtils.label_field(label="Respondent")
    submission_date = FormUtils.label_field(label="Date of Event")
    va_scheduled_date = FormUtils.date_field(label="VA Scheduled Date", required=True)
    va_proposed_date = FormUtils.label_field(label="Date Requested by Family")
    va_staff = FormUtils.model_choice_field(label="VA Interviewer", queryset=None, empty_label="", required=True)
    comment = FormUtils.char_field(label="Comment", required=False)

    class Meta:
        model = Death
        fields = [
            'death_code',
            'death_status',
            'respondent_name',
            'submission_date',
            'va_scheduled_date',
            'va_proposed_date',
            'va_staff',
            'comment'
        ]

    def __init__(self, *args, is_readonly=False, **kwargs):
        self.is_readonly = is_readonly
        super().__init__(*args, **kwargs)

        if self.is_readonly:
            self.fields['va_scheduled_date'] = FormUtils.label_field(label="VA Scheduled Date")
            self.fields['va_staff'] = FormUtils.label_field(label="VA Interviewer")
            self.fields['comment'] = FormUtils.label_field(label="Comment")

        if self.instance and self.instance.event:
            self.fields['respondent_name'].initial = self.instance.event.respondent_name
            self.fields['submission_date'].initial = self.instance.event.submission_date
            self.fields['va_proposed_date'].initial = self.instance.event.va_proposed_date
            self.fields['va_staff'].label_from_instance = lambda staff: f"{staff.full_name} ({staff.code})"
            self.fields['va_staff'].queryset = Staff.objects.filter(staff_type=Staff.StaffType.VA,
                                                                    province=self.instance.event.cluster.province)

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit and not self.is_readonly:
            if instance.va_proposed_date in ['', 'None']:
                instance.va_proposed_date = None

            if instance.death_status != Death.DeathStatus.VA_SCHEDULED:
                instance.death_status = Death.DeathStatus.VA_SCHEDULED
            instance.save()
        return instance
