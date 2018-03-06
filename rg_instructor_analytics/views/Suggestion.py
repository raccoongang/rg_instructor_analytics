"""
Module for the suggestion's tab logic.
"""
from abc import ABCMeta, abstractmethod
from collections import namedtuple
import json

from django.utils.translation import ugettext as _
from django.views.generic import View
from django_comment_client.utils import JsonResponse

from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from rg_instructor_analytics.views.Funnel import GradeFunnelView

# Structure for saving information about filter item.
# name - variable name, title - display title, value - default value.
FilterItem = namedtuple("FilterItem", "name title value")


class FilterBuilder:
    """
    Class for build filters.
    """

    def __init__(self):
        """
        Construct filter builder.
        """
        self.filter_map = []

    def add(self, **kwargs):
        """
        Add new field inside the filter.
        """
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
        """
        Return filter object.

        Filter object contains next field: `filter_title` and `filter_items`.
        Filter object contains method `serialize` return next dict:
            {
                title: "title of the filter"
                items: [
                    {name,title,value}
                    ...
                ]
            }
        """
        filter = {
            'filter_title': filter_title,
            'filter_items': self.filter_map,
            'serialize': lambda self: {
                'title': filter_title,
                'items': [{
                    'name': f.name,
                    'title': f.title,
                    'value': getattr(self, f.name)
                } for f in self.filter_items]
            }
        }
        filter.update({i.name: i.value for i in self.filter_map})
        return type('', (object,), filter)()


class BaseNorm:
    """
    Base class for suggestion nroms.
    """

    __metaclass__ = ABCMeta
    title = _("blank suggestion")
    description = ''
    filter = FilterBuilder().build(_('blank'))

    @abstractmethod
    def intent(self):
        """
        Return unique intent for current norm.
        """
        pass

    @abstractmethod
    def provide_data(self, course_key):
        """
        Return list in format  [{display_label,element_id}] with information according to the course.
        """
        pass

    def get_display_info(self):
        """
        Return list in format {information: [{display_label,element_id}], provider:{intent,filter_info}.
        """
        return {
            'intent': self.intent(),
            'filter': self.filter.serialize(),
            'title': self.title,
            'description': self.description
        }

    def applay_filter_from_request(self, request, **kwargs):
        """
        Return information according to the settuped filter.

        Return next map: {
            information: items according to applayed filters, each items has next format.
            provider: {
                intent: name of the intent.
            }
        }
        """
        for d in json.loads(request.POST['data']):
            setattr(self.filter, d['name'], d['value'])
        result = {
            'information': self.provide_data(kwargs['course_key']),
            'provider': {
                'intent': self.intent(),
            }
        }
        return result


class FunnelNorm(BaseNorm):
    """
    Norm, based on the information from the funnel tab with predefined threshold.
    """

    title = _('Suggestion by stuck users')
    filter = (FilterBuilder().build(_('Default stuck filter')))

    def intent(self):
        """
        Implement abstract method. Return `funnel_norm` as intent.
        """
        return 'funnel_norm'

    def get_items_with(self, funnel, criteria):
        """
        Return list of the funnel's item according to the filter function `criteria`.
        """
        result = []
        for i in funnel:
            if criteria(i):
                result.append(i)
            if i['children']:
                result = result + self.get_items_with(i['children'], criteria)
        return result

    def get_stuck_threshold(self):
        """
        Return predefined threshold for the stuck students.
        """
        return 25.0

    def provide_data(self, course_key):
        """
        Return list of the filter result, according to a threshold.
        """
        filtered_items = self.get_items_with(
            GradeFunnelView().get_funnel_info(course_key),
            (lambda i:
             float(i['student_count_in']) > 0 and
             float(i['student_count']) / float(i['student_count_in']) * 100.0 > float(self.get_stuck_threshold()))
        )
        label = _('On the partition named `{}` stuck to many students. We recommend reassessing content or pay '
                  'attention to the assignment.')
        return [{'displayLabel': label.format(i['name']), 'elementId':i['id']} for i in filtered_items]


class UserDefineFunnelNorm(FunnelNorm):
    """
    Modification of the FunnelNorm with a user-setted threshold.
    """

    title = _('Suggestion by stuck users')
    filter = (FilterBuilder()
              .add(stuck_percent=25, title=_("Setup percent of the stuck student"))
              .build(_('Default stuck filter'))
              )

    def intent(self):
        """
        Return intent name, that represents norm for the stuck use filter with a custom threshold.
        """
        return 'user_funnel_norm'

    def get_stuck_threshold(self):
        """
        Overload method, that returns custom stuck threshold instead predefined value.
        """
        return self.filter.stuck_percent


class SuggestionView(AccessMixin, View):
    """
    Api for get courses suggestion.
    """

    norma_list = [
        FunnelNorm(),
        UserDefineFunnelNorm()
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
