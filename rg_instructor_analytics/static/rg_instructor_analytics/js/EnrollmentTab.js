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

    var dateStart = 0;
    var dateEnd = 0;
    $("#get-report").on('click', loadTabData);
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
        
        $("#enrollment-stats-plot").html(`
            <div class="spinner-size">
                Loading, please wait a while
                <img src="/static/rg_instructor_analytics/images/ajax-loader.gif" alt="loader">
            </div>
        `);
        
        $("#select_cohort").addClass('select-disabled').get(0).disabled = true;
        $("#select_course").addClass('select-disabled').get(0).disabled = true;

        function onSuccess(response) {
            console.log('Enrollments tab', response);
            if (!response.dates_enroll.length) {
                $('#enrollment-stats-plot').html(
                    `<div style="padding:20px;text-align:center;">There are no any enrollments in the given period!</div>`
                );
                $("#select_cohort").removeClass('select-disabled').removeAttr('disabled');
                $("#select_course").removeClass('select-disabled').removeAttr('disabled');
                return;
            }
            
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
                    width: 4,
                    shape: 'hv',
                },
                hovermode: 'closest',
                hoverdistance: 1000,
                spikedistance: 1000,
                type: 'scatter'
            };
            let enrollTrace = {
                x: response.dates_enroll.map(dataFixFunction),
                y: response.counts_enroll,
                mode: 'lines',
                name: django.gettext('Enrollments'),
                line: {
                    color: '#8BB22A',
                },
                yaxis: 'y2',
                type: 'bar',
                marker: {
                    color: '#8BB22A',
                },
            };
            let unenrollTrace = {
                x: response.dates_unenroll.map(dataFixFunction),
                y: response.counts_unenroll,
                mode: 'lines',
                name: django.gettext('Unenrollments'),
                yaxis: 'y2',
                line: {
                    color: '#CC4630',
                },
                type: 'bar',
                marker: {
                    color: '#CC4630',
                },
            };
            let layout = {
                hovermode: 'closest',
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
            $("#enrollment-stats-plot").html('');
            $("#select_cohort").removeClass('select-disabled').removeAttr('disabled');
            $("#select_course").removeClass('select-disabled').removeAttr('disabled');
            Plotly.newPlot('enrollment-stats-plot', data, layout, {
                displayModeBar: false,
                scrollZoom: false,
            });
        }

        function onError() {
            alert("Can not load statistic fo selected period");
        }
        
        $.ajax({
            url: "api/enroll_statics/",
            method: "POST",
            data: date,
            success: function (data){
                var checkStatus = function () {
                    $.ajax({
                        url: "api/enroll_statics/",
                        method: "POST",
                        data: {task_id: data.task_id, ...date},
                        success: function (response) {
                            if(response.state == "SUCCESS"){
                                onSuccess(response.data)
                            } else if (["FAILURE", "REVOKED", "REJECTED"].indexOf(response.state) === -1) {
                                setTimeout(checkStatus, 2000);
                            } else {
                                onError()
                            }
                        },
                        error: onError,
                    })
                };
                checkStatus();
    
            }
        })
    }

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

    enrollTab.content.find("#select-all-week").click(function () {
        setPeriod('all')
    });

    function setPeriod(days) {
        let newFrom;
        if (days === 'all') {
            newFrom = dateStart;
        } else {
            newFrom = new Date(dateEnd - 1000 * 60 * 60 * 24 * days);
            if (newFrom < dateStart) {
                newFrom = dateStart;
            }
        }

        fromDate.datepicker("setDate", newFrom);
        toDate.datepicker("setDate", dateEnd);
        updateStatPeriod();
        updateEnrolls();
    }

    function loadTabData() {
        let now = new Date();
        let defaultStart = new Date();
        defaultStart.setMonth(defaultStart.getMonth() - 1);

        let enrollInfo = JSON.parse(periodDiv.attr('data-enroll'))[enrollTab.tabHolder.course];
        dateStart = enrollInfo.enroll_start === "null" ? defaultStart : new Date(parseFloat(enrollInfo.enroll_start) * 1000);
        dateEnd = enrollInfo.enroll_end === "null" ? now : new Date(parseFloat(enrollInfo.enroll_end) * 1000);

        if (dateEnd > now) {
            dateEnd = now;
        }

        fromDate.datepicker("option", "minDate", dateStart);
        fromDate.datepicker("setDate", dateStart);
        toDate.datepicker("setDate", dateEnd);
        toDate.datepicker("option", "maxDate", dateEnd);

        updateStatPeriod();
        updateEnrolls()
    }

    enrollTab.loadTabData = loadTabData;

    return enrollTab;
};
