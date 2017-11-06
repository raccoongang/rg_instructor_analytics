/**
 * module for instructor analytics tab
 */
(function () {
    'use strict';
    var CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2';

    var tabList = [];

    /**
     * Abstract class for tabs in instructor analytics tab
     * @param button is used for switching to the given tab
     * @param content content of the given tab
     * @class old realisation
     * @abstract
     */
    function Tab(button, content) {
        this.button = button;
        this.content = content;
        /**
         * Called for mark this tab active and show content.
         * @param isActive
         */
        this.setActive = function (isActive) {
            if (isActive) {
                content.addClass('active-section');
                button.addClass('active-section');
                this.loadTabData()
            } else {
                content.removeClass('active-section');
                button.removeClass('active-section');
            }
        };

        /**
         * Called for loading date for some tab implementation.
         * @abstract
         */
        this.loadTabData = function () {
            throw new Error("missing implementation")
        }
    }

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
                        shape: 'spline',
                        width: 2.3,
                        smoothing: 1.25
                    },
                    type: 'scatter',
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
                    type: 'scatter'
                };
                var unenrollTrace = {
                    x: x,
                    y: response.unenroll,
                    mode: 'lines',
                    name: django.gettext('unenroll'),
                    fill: 'tozeroy',
                    fillcolor: "rgba(204,70,48,0.25)",
                    line: {
                        shape: 'hv',
                        color: '#CC4630',
                    },
                    type: 'scatter'
                };
                var layout = {
                    xaxis: {},
                    yaxis: {dtick: 1}
                };
                var data = [unenrollTrace, enrollTrace, totalTrace];

                Plotly.newPlot('enrollment-stats-plot', data, layout);
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
            periodDiv.addClass('show');
        });

        enrollTab.content.find("#date-apply-btn").click(function () {
            periodDiv.removeClass('show');
            updateStatPeriod();
            updateEnrolls();
        });

        enrollTab.loadTabData = updateEnrolls;

        updateStatPeriod();
        updateEnrolls();
        return enrollTab;
    }

    /**
     * Implementation of Tab for the problem tab
     * @returns {Tab}
     * @class old realisation
     */
    function ProblemTab(button, content) {
        var problemTab = new Tab(button, content);
        problemTab.loadTabData = function () {
            console.log("Called loadTabData method for ProblemTab. " +
                "ProblemTab functionality will be implemented in feature")
        };
        return problemTab;
    }

    /**
     * Implementation of Tab for gradebook tab
     * @returns {Tab}
     * @class old realisation
     */
    function GradebookTab(button, content) {
        var greadebookTab = new Tab(button, content);
        greadebookTab.loadTabData = function () {
            console.log("Called loadTabData method for GradebookTab. " +
                "GradebookTab functionality will be implemented in feature")
        };
        return greadebookTab;
    }

    function toggleToTab(tab) {
        tabList.forEach(function (t) {
            t.setActive(t === tab)
        })
    }

    $(function () {
        var $content = $('.' + CSS_INSTRUCTOR_CONTENT);
        tabList = [
            EnrollmentTab(
                $content.find('#enrollment-stats-btn'),
                $content.find('#section-enrollment-stats')),
            ProblemTab(
                $content.find('#problems-btn'),
                $content.find('#section-problem')),
            GradebookTab(
                $content.find('#gradebook-btn'),
                $content.find('#section-gradebook'))
        ];
        tabList.forEach(function (tab) {
            tab.button.click(function () {
                toggleToTab(tab)
            })
        });

        toggleToTab(tabList[0]);
    });

}).call(this);
