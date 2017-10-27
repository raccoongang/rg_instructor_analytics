(function () {
    'use strict';
    var CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2';

    var tabList = [];


    function Tab(button, content) {
        this.button = button;
        this.content = content;
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

        this.loadTabData = function () {
            throw new Error("missing implementation")
        }
    }

    function EnrollmentTab(button, content) {
        var dateFormat = "mm/dd/yy";
        var fromDate, toDate;
        var periodDiv;
        var selectDateBtn;
        var enrollTab = new Tab(button, content);


        function getDate(element) {
            try {
                return $.datepicker.parseDate(dateFormat, element.value);
            } catch (error) {
                return null;
            }
        }

        function updateStatPeriod() {
            selectDateBtn.html(fromDate.val() + ' - ' + toDate.val())
        }

        function updateEnrolls() {
            var date = {
                from: fromDate.datepicker("getDate").getTime() / 1000,
                to: toDate.datepicker("getDate").getTime() / 1000
            };

            function onSuccess(response) {
                var trace1 = {
                    x: response.dates.map(function (x) {
                        return new Date(x * 1000)
                    }),
                    y: response.counts,
                    type: 'scatter'
                };
                var layout = {
                    xaxis: {},
                    yaxis: {dtick: 1}
                };
                var data = [trace1];

                Plotly.newPlot('enrollment-stats-plot', data, layout);
            }

            function onError() {
                alert("Can not load statistic fo select period");
            }

            $.ajax({
                traditional: true,
                type: "POST",
                url: "api/enroll_statics",
                data: date,
                success: onSuccess,
                error: onError,
                dataType: "json"
            });
        }

        periodDiv = enrollTab.content.find("#date_dropdown");
        fromDate = enrollTab.content.find("#from")
            .datepicker()
            .on("change", function () {
                toDate.datepicker("option", "minDate", getDate(this));
            });
        toDate = enrollTab.content.find("#to").datepicker()
            .on("change", function () {
                fromDate.datepicker("option", "maxDate", getDate(this));
            });
        var dateStart = periodDiv.attr('data-start');
        var dateEnd = periodDiv.attr('data-end');

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

        selectDateBtn = enrollTab.content.find("#date-btn");
        selectDateBtn.click(function () {
            periodDiv.addClass('show');
            updateEnrolls();
        });

        enrollTab.content.find("#date-apply-btn").click(function () {
            periodDiv.removeClass('show');
            updateStatPeriod()
        });

        enrollTab.loadTabData = updateEnrolls;

        updateStatPeriod();
        updateEnrolls();
        return enrollTab;
    }

    function ProblemTab(button, content) {
        var problemTab = new Tab(button, content);
        problemTab.loadTabData = function () {
        };
        return problemTab;
    }

    function GradebookTab(button, content) {
        var greadebookTab = new Tab(button, content);
        greadebookTab.loadTabData = function () {
        };
        return greadebookTab;
    }

    function toggleToTab(tab) {
        tabList.forEach(function (t) {
            t.setActive(t === tab)
        })
    }

    $(function () {
        var $content;
        $content = $('.' + CSS_INSTRUCTOR_CONTENT);
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
