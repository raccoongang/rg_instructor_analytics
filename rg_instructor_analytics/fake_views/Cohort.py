"""
Module for fake cohort subtab.
"""
import json

from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.views.generic import View

from rg_instructor_analytics import tasks
from rg_instructor_analytics.utils.AccessMixin import AccessMixin

try:
    from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
except Exception:
    from lms.djangoapps.grades.new.course_grade import CourseGradeFactory


class CohortView(AccessMixin, View):
    """
    Api for cohort statistic.
    """

    def process(self, request, **kwargs):
        raw_data = ('{"cohorts":[{"max_progress":14,"students_username":["47922729mylifeunisaacza",'
                    '"aawadullahgmailcom","abdel-hakshotmailfr","abdullahshakir82gmailcom","adelsaber_ishotmailcom",'
                    '"adeyinkadamigmailcom","ahmadkabir8akgmailcom","ahmeddesoky646gmailcom","aimanasakgmailcom",'
                    '"alarekehindepaulgmailcom","aliraza125ar10gmailcom","amriradhiainsatgmailcom",'
                    '"anuridhi1yahoocom","arehman9860gmailcom","asangaryaccesscomeg","asmaa1054365t3moeedueg",'
                    '"ayeshadounya32gmailcom","berkberk198917gmailcom","bilalmughal540gmailcom","binosh1hotmailcom",'
                    '"chamathcgmailcom","changezlashari1outlookcom","chaudhryasim5gmailcom",'
                    '"chibuikekenneth003gmailcom","davidgambo1gmailcom","didaahmed58gmailcom","dkapenggmailcom",'
                    '"duoglas4hotmailcom","emreuyguchotmailcom","enasnabiloutlookcom","fabianenebeligmailcom",'
                    '"faithndlovuoutlookcom","favoururepent2000yahoocom","felixkimanigmailcom",'
                    '"firasaridhi998gmailcom","gavinthysyahoocom","get2jayhotmailcom","ghulamjillani216gmailcom",'
                    '"gilitcherfgmailcom","gmpanhgmailcom","gntsdidamgmailcom","hammadnaveed010gmailcom",'
                    '"hamzaghani71gmailcom","hannan_arshedymailcom","hanzalaiqbal789hotmailcom",'
                    '"heebcampustechnionacil","hidayatrehman64gmailcom","hodaswydangmailcom","hussainsanni2gmailcom",'
                    '"ikbenezergmailcom","imrannasir71gmailcom","interlockingcbogmailcom",'
                    '"issawogoleliquidtelecomcotz","jadelusi11gmailcom","jajioladimejiyahoocom",'
                    '"jasimminhasgmailcom","jazzyjoeweeyahoocom","jobogetooutlookcom","joekubarigmailcom",'
                    '"johnsonmessilo19gmailcom","josephadewole1gmailcom","junaid_alicomsatsedupk",'
                    '"kayaismail3705gmailcom","kemzy2teasegmailcom","kershni25gmailcom","kobibodekgmailcom",'
                    '"lieslkrauseeduplexcoza","loisewayahoocom","lolafiyingmailcom","lovelyboy523gmailcom",'
                    '"mahmoudsheir11hotmailcom","mahmoud_elashryhotmailcom","mahwishfatima89hotmailcom",'
                    '"malikharis58336gmailcom","maram_abbasaucegyptedu","mariahussain18outlookcom",'
                    '"markcharlz5gmailcom","maxblosevodacomcoza","mayabraingmailcom","mcbenny4uhotmailcom",'
                    '"mehmoodijunejogmailcom","meraquettagmailcom","michael4dominion1gmailcom","mickyshamgmailcom",'
                    '"midoomran72gmailcom","minaboshra75gmailcom","mityabvgmailcom","mmesomegmailcom",'
                    '"mohdbadahdoohgmailcom","msinanabylgmailcom","muhibimran38gmailcom","muzamilkaleem1997gmailcom",'
                    '"naimuddingmailcom","nhamodapigmailcom","numans321msncom","nwanadehenryigmailcom",'
                    '"okeadeyinkagmailcom","olucharmackayahoocom","ombongi2015gmailcom","opemoses01",'
                    '"opeyemiaremu34gmailcom","otegaobijekogmailcom","qasimkazmi786outlookcom","ranmasavcoil",'
                    '"realowdedgmailcom","saadbintayyab7gmailcom","sameershk1999gmailcom","samsonajele55gmailcom",'
                    '"shafeeqjadoutlookcom","shahzaibawan227gmailcom","sonerdemirtasoutlookcomtr","spdjshgmailcom",'
                    '"staff","stanzaokoigmailcom","steveochiengj17gmailcom","strahimsharafyargmailcom",'
                    '"summaiya_96hotmailcom","supriseadenlegmailcom","syedhoney0gmailcom","tellegurtinagmailcom",'
                    '"thamerkhangmailcom","troubleshootandfixgmailcom","ubaid7ullah195gmailcom",'
                    '"udoakaghainyanggmailcom","ugochi2okoriegmailcom","umer2209outlookcom","ushasam62gmailcom",'
                    '"vandupaulinusgmailcom","vicabongogmailcom","vicckyblinksgmailcom","vickiemirerigmailcom",'
                    '"victoronyinyemegmailcom","wallacemyemhotmailcom","waseem0888gmailcom",'
                    '"wwwrukayyafaroukgmailcom","yofetahegmailcom","zw71004gmailcom"],"students_id":[5245,7583,2140,'
                    '8731,2707,10767,10531,9973,10342,11168,7918,9341,11310,8524,1020,9120,8444,11010,8151,10600,'
                    '10124,7563,8039,9979,9527,9130,9624,6023,10849,9157,10260,10042,9195,9033,9117,11330,5023,1004,'
                    '8702,8732,8393,6788,3856,8761,8112,9981,4065,8799,9695,9500,10497,10461,5486,9807,8529,10189,'
                    '7818,1082,8277,10335,10482,9637,10384,10648,3648,9256,10317,11111,7909,5259,5849,7119,9525,452,'
                    '9532,1580,11313,10896,8847,1298,1714,8453,10058,11155,9036,9311,9013,9552,11294,8925,9116,8296,'
                    '9265,8803,7991,8456,9429,8474,11272,64,10761,9994,8610,9250,10500,8413,6822,10730,5349,10653,'
                    '10509,9812,5,8124,9375,8375,9457,835,8291,3144,9906,8489,2440,8378,10972,5522,9715,8289,8727,'
                    '10655,10889,8149,10568,10913,11095,6294,2800],"percent":90},{"max_progress":56,'
                    '"students_username":["abiodunakinbotehealthpluscomng","abucheriwitnessgmailcom",'
                    '"edwardoche25yahoocom","josephugonnagmailcom","kelvinmwenda9outlookcom","lecenochgmailcom",'
                    '"ngangadanchegmailcom","ritaokonkwo6gmailcom","saedalhag2020hotmailcom"],"students_id":[5033,'
                    '10799,9371,9723,8890,9226,8573,9670,8684],"percent":5},{"max_progress":100,"students_username":['
                    '"Cyrus","martinsosadebe360gmailcom","muhammadbilalbangashhotmailcom","onlinemartez1gmailcom",'
                    '"valamasiatugmailcom","zohaibkool00gmailcom"],"students_id":[47,2213,8629,8970,8754,7107],'
                    '"percent":3}],"labels":["to 14 %","to 56 %","to 100 %"],"values":[90,5,3]}')
        return JsonResponse(data=json.loads(raw_data))


class CohortSendMessage(AccessMixin, View):
    """
    Endpoint for sending email message.
    """

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        tasks.send_email_to_cohort(
            subject=request.POST['subject'],
            message=request.POST['body'],
            students=User.objects.filter(id__in=request.POST['users_ids'].split(',')).values_list('email', flat=True)
        )
        return JsonResponse({'status': 'ok'})
