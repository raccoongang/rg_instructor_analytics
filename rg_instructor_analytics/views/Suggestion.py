import json
from collections import namedtuple

from abc import ABCMeta, abstractmethod
from django.utils.translation import ugettext as _
from django.views.generic import View

from django_comment_client.utils import JsonResponse
from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from rg_instructor_analytics.views.Funnel import GradeFunnelView

FilterItem = namedtuple("FilterItem", "name title value")


class FilterBuilder:
    def __init__(self):
        self.filter_map = []

    def add(self, **kwargs):

        values_name = list(kwargs.keys())
        if 'title' in values_name:
            values_name.remove('title')
        if len(values_name) > 1:
            raise Exception("To many argument in getting. Allowed only `title` and `{filter name}`")
        elif len(values_name) == 0:
            raise Exception("Name of the filter don`t passed")

        self.filter_map.append(
            FilterItem(
                name=values_name[0],
                title=kwargs.get('title', ''),
                value=kwargs.get(values_name[0], None),
            )
        )
        return self

    def build(self, filter_title):
        filter = {
            'filter_title': filter_title,
            'filter_items': self.filter_map,
            'serialize': lambda self: {'title': filter_title, 'items': [dict(f._asdict()) for f in self.filter_items]},
        }
        filter.update({i.name: i.value for i in self.filter_map})
        return type('', (object,), filter)()


class BaseNorma():
    __metaclass__ = ABCMeta
    title = _("blank suggestion")
    description = ''
    filter = FilterBuilder().build(_('blank'))

    def get_predefine_filters(self):
        return [self.filter]

    @abstractmethod
    def intent(self):
        pass

    @abstractmethod
    def provide_data(self, course_key):
        """
        Return list in format  [{display_label,element_id}] with information according to the course.
        """
        pass

    def get_display_info(self):
        """
        Return list in format {information: [{display_label,element_id}], provider:{intent,filter_info}
        """
        return {
            'intent': self.intent(),
            'filters': [i.serialize() for i in self.get_predefine_filters()],
            'title': self.title,
            'description': self.description
        }

    def applay_filter_from_request(self, request, **kwargs):
        for d in json.loads(request.POST['data']):
            setattr(self.filter, d['name'], d['value'])
        result = {
            'information': self.provide_data(kwargs['course_key']),
            'provider': {
                'intent': self.intent(),
            }
        }
        return result


class FunnelNorma(BaseNorma):
    SECTION_TYPE = {
        0: 'Section',
        1: 'Subsection',
        2: 'Unit',
    }

    title = _('Suggestion by stack users')
    filter = (FilterBuilder()
              .add(stuck_percent=25, title=_("Setup percent of the stuck student"))
              .build(_('Default stack filter'))
              )

    def intent(self):
        return 'funnel_norm'

    def get_items_with(self, funnel, criteria):
        result = []
        for i in funnel:
            if criteria(i):
                result.append(i)
            if i['children']:
                result = result + self.get_items_with(i['children'], criteria)
        return result

    def provide_data(self, course_key):
        filtered_items = self.get_items_with(
            GradeFunnelView().get_funnel_info(course_key),
            (lambda i:
             float(i['student_count_in']) > 0
             and float(i['student_count']) / float(i['student_count_in']) * 100.0 > float(self.filter.stuck_percent))
        )
        return [{'displayLabel': i['name'], 'elementId':i['id']} for i in filtered_items]


class SuggestionView(AccessMixin, View):
    """
    Api for get courses suggestion.
    """
    norma_list = [
        FunnelNorma()
    ]

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        intent = request.POST['intent']

        if intent == 'get_norm_list':
            return JsonResponse(data={'norm': [n.get_display_info() for n in self.norma_list]})
        else:
            for n in self.norma_list:
                if n.intent() == request.POST['intent']:
                    result = n.applay_filter_from_request(request=request, **kwargs)
                    return JsonResponse(data=result)

        return JsonResponse(data={})
