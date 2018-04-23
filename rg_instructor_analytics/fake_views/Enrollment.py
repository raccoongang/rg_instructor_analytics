"""
Module for enrollment subtab.
"""
import json

from django.http.response import JsonResponse
from django.views.generic import View

from rg_instructor_analytics.utils.AccessMixin import AccessMixin


class EnrollmentStatisticView(AccessMixin, View):
    """
    Api for getting enrollment statistic.
    """

    def process(self, request, **kwargs):
        """
        Process post request for this view.
        """
        raw_data = (
            '{"dates":[1521756000,1521759600,1521846000,1521932400,1522015200,1522101600,1522188000,1522274400,'
            '1522360800,1522447200,1522533600,1522620000,1522706400,1522792800,1522879200,1522965600,1523138400,'
            '1523224800,1523311200,1523397600,1523484000,1523656800,1523916000,1524175200,1524261600,1524430800],'
            '"total":[200,204,206,218,226,234,237,242,244,247,247,248,248,249,249,251,254,255,257,260,263,265,268,'
            '300,305,306],"enroll":[0,4,2,12,8,8,2,6,3,2,1,2,1,2,1,3,4,2,3,4,4,3,4,31,5,1],"unenroll":[0,0,0,0,0,0,-1,'
            '-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]}'
        )
        return JsonResponse(data=json.loads(raw_data))
