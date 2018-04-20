/**
 * Implementation of Tab for the enrollment tab
 * @returns {Tab}
 * @class old realisation
 */
function EnrollmentTab(button, content) {
    var enrollTab = new Tab(button, content);

    var dateFormat = "mm/dd/yy";

    var selectDateBtn = enrollTab.content.find("#date-btn");

    var periodDiv = enrollTab.content.find("#date_dropdown");

    var fromDate = enrollTab.content.find("#from")
        .datepicker()
        .on("change", function () {
            toDate.datepicker("option", "minDate", getDate(this));
        });
    var toDate = enrollTab.content.find("#to").datepicker()
        .on("change", function () {
            fromDate.datepicker("option", "maxDate", getDate(this));
        });

    var dateStart = periodDiv.attr('data-start');
    var dateEnd = periodDiv.attr('data-end');

    /**
     * Provide date from given datepicker
     * @param element - datepicker
     */
    function getDate(element) {
        try {
            return $.datepicker.parseDate(dateFormat, element.value);
        } catch (error) {
            return null;
        }
    }

    /**
     * Update select date button according to selection of date range
     */
    function updateStatPeriod() {
        selectDateBtn.html(fromDate.val() + ' - ' + toDate.val())
    }

    /**
     * Send ajax to server side according selected date range and redraw plot
     */
    function updateEnrolls() {
        var date = {
            from: fromDate.datepicker("getDate").getTime() / 1000,
            to: toDate.datepicker("getDate").getTime() / 1000
        };

        function onSuccess(response) {
            var x = response.dates.map(function (x) {
                var result = new Date(x * 1000);
                result.setHours(0);
                result.setMinutes(0);
                return result;
            });
            var totalTrace = {
                x: x,
                y: response.total,
                mode: 'lines',
                name: django.gettext('total'),
                line: {
                    color: '#70A3FF',
                    width: 2.3,
                    smoothing: 1.25
                },
                hovermode:'closest',
                hoverdistance:1000,
                spikedistance:1000,
                type: 'scatter'
            };
            var enrollTrace = {
                x: x,
                y: response.enroll,
                mode: 'lines',
                name: django.gettext('enroll'),
                fill: 'tozeroy',
                fillcolor: "rgba(139,178,42,0.25)",
                line: {
                    shape: 'hv',
                    color: '#8BB22A',
                },
                yaxis: 'y2', 
                type: 'scatter'
            };
            var unenrollTrace = {
                x: x,
                y: response.unenroll,
                mode: 'lines',
                name: django.gettext('unenroll'),
                fill: 'tozeroy',
                fillcolor: "rgba(204,70,48,0.25)",
                yaxis: 'y2', 
                line: {
                    shape: 'hv',
                    color: '#CC4630',
                },
                hoveron:'points+fills',
                type: 'scatter'
            };
            var layout = {
                hovermode:'closest',
                xaxis: {
                    type: "date",
                    margin: {t: 10}
                },
                yaxis: {nticks: 4},
                yaxis2: {
                    overlaying: 'y',
                    side: 'right'
                },
                showlegend: false
            };
            var data = [unenrollTrace, enrollTrace, totalTrace];
            
            Plotly.newPlot('enrollment-stats-plot', data, layout, {displayModeBar: false});
        }

        function onError() {
            alert("Can not load statistic fo select period");
        }

        $.ajax({
            traditional: true,
            type: "POST",
            url: "api/enroll_statics/",
            data: date,
            success: onSuccess,
            error: onError,
            dataType: "json"
        });
    }

    var now = new Date();
    if (dateEnd !== "null" && (dateEnd = new Date(parseFloat(dateEnd) * 1000)) < now) {
        toDate.datepicker("setDate", dateEnd);
        toDate.datepicker("option", "maxDate", dateEnd);
    } else {
        toDate.datepicker("setDate", now);
        toDate.datepicker("option", "maxDate", now);
    }

    if (dateStart !== "null") {
        dateStart = new Date(parseFloat(dateStart) * 1000);
        fromDate.datepicker("option", "minDate", dateStart);
    }

    var defaultStart = new Date();
    defaultStart.setMonth(defaultStart.getMonth() - 1);
    fromDate.datepicker("setDate", dateStart && dateStart > defaultStart ? dateStart : defaultStart);

    selectDateBtn.click(function () {
        $(this).toggleClass('active');
        periodDiv.toggleClass('show');
    });

    enrollTab.content.find("#date-apply-btn").click(function () {
        periodDiv.removeClass('show');
        updateStatPeriod();
        updateEnrolls();
    });

    enrollTab.content.find("#select-1-week").click(function () {
        setPeriod(7)
    });

    enrollTab.content.find("#select-2-week").click(function () {
        setPeriod(14)
    });

    enrollTab.content.find("#select-4-week").click(function () {
        setPeriod(30)
    });

    function setPeriod(days) {

        let newFrom = new Date(toDate.datepicker('getDate') - 1000 * 60 * 60 * 24 * days);
        if (dateStart !== "null" && newFrom < dateStart) {
            newFrom = dateStart
        }
        fromDate.datepicker("setDate", newFrom);
        updateStatPeriod();
        updateEnrolls();
    }


    enrollTab.loadTabData = updateEnrolls;

    updateStatPeriod();
    updateEnrolls();
    return enrollTab;
};
