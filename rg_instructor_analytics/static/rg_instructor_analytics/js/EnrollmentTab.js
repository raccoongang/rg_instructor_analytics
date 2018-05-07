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

        if (new Date(fromDate.val()) == 'Invalid Date')
            fromDate.datepicker("setDate", dateStart);
        if (new Date(toDate.val()) == 'Invalid Date')
            toDate.datepicker("setDate", dateEnd);

        if (new Date(fromDate.val()) < dateStart)
            fromDate.datepicker("setDate", dateStart);
        if (new Date(toDate.val()) > dateEnd)
            toDate.datepicker("setDate", dateEnd);

        if (new Date(fromDate.val()) > dateEnd)
            fromDate.datepicker("setDate", dateEnd);
        if (new Date(toDate.val()) < dateStart)
            toDate.datepicker("setDate", dateStart);

        if (new Date(fromDate.val()) > new Date(toDate.val()))
            fromDate.datepicker("setDate", new Date(toDate.val()));

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
            function dataFixFunction(x) {
                var result = new Date(x);
                result.setHours(0);
                result.setMinutes(0);
                return result;
            }
            let totalTrace = {
                x: response.dates_total.map(dataFixFunction),
                y: response.counts_total,
                mode: 'lines',
                name: django.gettext('Total'),
                line: {
                    color: '#70A3FF',
                    width: 2.3,
                    shape: 'spline',
                    smoothing: 0.7
                },
                hovermode:'closest',
                hoverdistance:1000,
                spikedistance:1000,
                type: 'scatter'
            };
            let enrollTrace = {
                x: response.dates_enroll.map(dataFixFunction),
                y: response.counts_enroll,
                mode: 'lines',
                name: django.gettext('Enrollments'),
                line: {
                    // shape: 'hv',
                    color: '#8BB22A',
                    smoothing: 0.25,
                    shape: 'spline',
                },
                yaxis: 'y2', 
                type: 'scatter'
            };
            let unenrollTrace = {
                x: response.dates_unenroll.map(dataFixFunction),
                y: response.counts_unenroll,
                mode: 'lines',
                name: django.gettext('Unenrollments'),
                yaxis: 'y2',
                line: {
                    // shape: 'hv',
                    color: '#CC4630',
                    smoothing: 0.25,
                    shape: 'spline',
                },
                type: 'scatter'
            };
            let layout = {
                hovermode:'closest',
                xaxis: {
                    type: "date",
                    margin: {t: 10}
                },
                yaxis: {
                    nticks: 4,
                    overlaying: 'y2',
                },
                yaxis2: {
                    side: 'right'
                },
                showlegend: false,
            };
            let data = [unenrollTrace, enrollTrace, totalTrace];
            
            Plotly.newPlot('enrollment-stats-plot', data, layout, {
                displayModeBar: false,
                scrollZoom: false,
            });
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
