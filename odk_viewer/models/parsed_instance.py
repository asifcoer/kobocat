from django.db import models
from django.db.models.signals import post_save

from utils.reinhardt import queryset_iterator
from odk_logger.models import XForm, Instance
from common_tags import IMEI, DEVICE_ID, START_TIME, START, \
    END_TIME, END, LGA_ID, ID, SURVEYOR_NAME, ATTACHMENTS, DATE, SURVEY_TYPE
import datetime


class ParseError(Exception):
    pass


def datetime_from_str(text):
    # Assumes text looks like 2011-01-01T09:50:06.966
    if text is None:
        return None
    date_time_str = text.split(".")[0]
    return datetime.datetime.strptime(
        date_time_str, '%Y-%m-%dT%H:%M:%S'
        )


class ParsedInstance(models.Model):
    instance = models.OneToOneField(Instance, related_name="parsed_instance")
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    class Meta:
        app_label = "odk_viewer"

    def to_dict(self):
        if not hasattr(self, "_dict_cache"):
            self._dict_cache = self.instance.get_dict()
        self._dict_cache.update(
            {
                ID: self.instance.id,
                ATTACHMENTS: [a.media_file.name for a in self.instance.attachments.all()],                    
                u"_status": self.instance.status,
                }
            )
        for mod in self.instance.modifications.all():
            self._dict_cache = mod.process_doc(self._dict_cache)
        return self._dict_cache

    @classmethod
    def dicts(cls, xform):
        qs = cls.objects.filter(instance__xform=xform)
        for parsed_instance in queryset_iterator(qs):
            yield parsed_instance.to_dict()

    def _set_start_time(self):
        doc = self.to_dict()
        if START_TIME in doc:
            date_time_str = doc[START_TIME]
            self.start_time = datetime_from_str(date_time_str)
        elif START in doc:
            date_time_str = doc[START]
            self.start_time = datetime_from_str(date_time_str)
        else:
            self.start_time = None

    def _set_end_time(self):
        doc = self.to_dict()
        if END_TIME in doc:
            date_time_str = doc[END_TIME]
            self.end_time = datetime_from_str(date_time_str)
        elif END in doc:
            date_time_str = doc[END]
            self.end_time = datetime_from_str(date_time_str)
        else:
            self.end_time = None

    def parse(self):
        self._set_start_time()
        self._set_end_time()


def _parse_instance(sender, **kwargs):
    # When an instance is saved, first delete the parsed_instance
    # associated with it.
    instance = kwargs["instance"]
    pi, created = ParsedInstance.objects.get_or_create(instance=instance)

post_save.connect(_parse_instance, sender=Instance)