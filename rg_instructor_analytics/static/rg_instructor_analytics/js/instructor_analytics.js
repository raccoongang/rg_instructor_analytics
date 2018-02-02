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

            let newFrom = new Date(toDate.datepicker('getDate') - 1000*60*60*24*days);
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
    }

    /**
     * Implementation of Tab for the problem tab
     * @returns {Tab}
     * @class old realisation
     */
    function ProblemTab(button, content) {
        var problemTab = new Tab(button, content);
        var problemDetail = problemTab.content.find("#problem-body");

        /**
         * function for display general plot with homework`s stat
         */
        function updateHomeWork() {
            function onSuccess(response) {

                const correct_answer = {
                    x: response.names,
                    y: response.correct_answer,
                    data: response.problems,
                    name: django.gettext('Percent of the correct answers'),
                    type: 'bar'
                };

                const attempts = {
                    x: response.names,
                    y: response.attempts,
                    data: response.problems,
                    name: django.gettext('Average count of attempts'),
                    type: 'bar'
                };
                const data = [correct_answer, attempts];

                Plotly.newPlot('problem-homeworks-stats-plot', data);
                document.getElementById("problem-homeworks-stats-plot").on('plotly_click', function (data) {
                    loadHomeWorkProblems(response.problems[data.points[0].pointNumber]);
                });
            }

            function onError() {
                alert("Can not load statistic fo select course");
            }

            $.ajax({
                traditional: true,
                type: "POST",
                url: "api/problem_statics/homework/",
                data: {},
                success: onSuccess,
                error: onError,
                dataType: "json"
            });
        }

        /**
         * function for display plot with homework problem stat
         * @param homeworsProblem string id of problem
         */
        function loadHomeWorkProblems(homeworsProblem) {
            function onSuccess(response) {

                const incorrect = {
                    y: response.incorrect,
                    name: django.gettext('Incorrect answers'),
                    type: 'bar'
                };

                const correct = {
                    y: response.correct,
                    name: django.gettext('Correct answers'),
                    type: 'bar'
                };
                const data = [correct, incorrect];

                const layout = {
                    barmode: 'relative',
                    xaxis: {dtick: 1},
                    yaxis: {dtick: 1}
                };

                Plotly.newPlot('problems-stats-plot', data, layout);

                document.getElementById("problems-stats-plot").on('plotly_click', function (data) {
                    displayProblemView(homeworsProblem[data.points[0].pointNumber]);
                });
            }

            function onError() {
                alert("Can not load statistic fo select course");
            }

            $.ajax({
                traditional: true,
                type: "POST",
                url: "api/problem_statics/homeworksproblems/",
                data: {problems: homeworsProblem},
                success: onSuccess,
                error: onError,
                dataType: "json"
            });

        }

        /**
         * function for render problem body
         * @param stringProblemID string problem id
         */
        function displayProblemView(stringProblemID) {
            function onSuccess(response) {
                problemDetail.html(response.html);
                let problemsWrapper = problemDetail.find(".problems-wrapper");
                let problemBody = problemsWrapper.attr("data-content");
                problemsWrapper.html(problemBody);

                //hide problem debug info
                problemsWrapper.find('.status-icon').hide();
                problemsWrapper.find('.submit').hide();
                problemDetail.find('.instructor-info-action').hide();
                problemDetail.find('.status').remove();

                bindPlotsPopupForProblem(problemsWrapper, stringProblemID)
            }

            function onError() {
                alert("Can not load statistic fo select course");
            }

            $.ajax({
                traditional: true,
                type: "POST",
                url: "api/problem_statics/problem_detail/",
                data: {problem: stringProblemID},
                success: onSuccess,
                error: onError,
                dataType: "json"
            });
        }

        problemTab.loadTabData = function () {
            updateHomeWork()
        };

        problemTab.content.find('.close').click(item => problemTab.content.find('#model_plot').hide());

        return problemTab;
    }

    /**
     * add buttons for show plot for problem`s question
     * @param problem div with problem`s render
     * @param stringProblemID string problem id
     */
    function bindPlotsPopupForProblem(problem, stringProblemID) {
        var avalivleQuestions = [OpetionQuestion, RadioOpetionQuestion, MultyChoseQuestion];
        var questionsDivs = problem.find(".wrapper-problem-response");
        var isAdded;
        questionsDivs.each(function (index) {
            isAdded = false;
            var html = $(questionsDivs[index]);
            for (var i = 0; i < avalivleQuestions.length; i++) {
                var question = avalivleQuestions[i](html, stringProblemID);
                if (question.isCanParse()) {
                    question.applyToCurrentProblem(html);
                    isAdded = true;
                    break;
                }
            }
            if(!isAdded){
                $('<p>We can`t display plot for this question.</p>').appendTo(html);
            }
        });
    }

    /**
     * Base class for questions
     * @param questionHtml layout with question
     * @param stringProblemID string id of question`s problem
     * @class old realisation
     * @abstract
     */
    function BaseQuestion(questionHtml, stringProblemID) {
        this.questionHtml = questionHtml;
        this.problemID = stringProblemID;

        /**
         * abstract method for indicate, can instance of question correct parse given html
         * @abstract
         */
        this.isCanParse = function () {
            throw new Error("missing implementation")
        };

        /**
         * abstract method, that provide information for request about question statistic
         * @return object with next body:
         * return {
         *       type: string // string marker for given question
         *       questionID: string, // id of question
         *       answerMap: JSON string // json with relation between real data and it representation in database
         *  }
         *
         * @abstract
         */
        this.getRequestMap = function () {
            throw new Error("missing implementation")
        };

        /**
         * function for display server response as bar plot
         * @param data server response. Object with key - name of position and value - value of position
         */
        this.displayBar = function (data) {
            const plot_popupp = $('#model_plot');
            plot_popupp.show();

            var x = [];
            var y = [];
            Object.keys(data).forEach(function (key) {
                y.push(key);
                x.push(data[key]);
            });
            const answers = {
                x: x,
                y: y,
                type: 'bar',
                orientation: 'h'
            };
            const layout = {
                margin: {
                    l: 500
                }
            };
            Plotly.newPlot('proble-question-plot', [answers], layout);
        };

        /**
         * call`s when receive response with stats for question
         * @param response
         */
        this.onGettingStat = function (response) {
            switch (response.type) {
                case 'bar':
                    this.displayBar(response.stats)
                    break;
            }
        };

        this.onGettingStatFail = function () {
            console.log("something bad headings")
        };

        /**
         * apply given instance to some question of problem
         * @param html layout for inserting button for display plot
         */
        this.applyToCurrentProblem = function (html) {
            const $plotBtn = $('<button>Show plot!</button>');
            $plotBtn.appendTo(html);
            $plotBtn.click((item) => {
                var requestMap = this.getRequestMap();
                requestMap.problemID = this.problemID;
                $.ajax({
                    traditional: true,
                    type: "POST",
                    url: "api/problem_statics/problem_question_stat/",
                    data: requestMap,
                    success: (response) => this.onGettingStat(response),
                    error: () => this.onGettingStatFail(),
                    dataType: "json"
                });
            });
        };
    }

    /**
     * Implementation for the drop down question
     * @param questionHtml
     * @param stringProblemID
     * @return {OpetionQuestion}
     * @class old realisation
     * @extends BaseQuestion
     */
    function OpetionQuestion(questionHtml, stringProblemID) {
        const optionQuestion = new BaseQuestion(questionHtml, stringProblemID);
        const question = optionQuestion.questionHtml.find('.option-input');
        optionQuestion.questionHtml = question.length === 1 ? $(question[0]) : null;

        optionQuestion.isCanParse = function () {
            return this.questionHtml !== null
        };

        optionQuestion.getRequestMap = function () {
            const selectRoot = this.questionHtml.find('select');
            const optionsItem = selectRoot.find('option');
            const id2ValueMap = {};
            optionsItem.each(index => id2ValueMap[optionsItem[index].value] = optionsItem[index].text);
            return {
                type: 'select',
                questionID: selectRoot.attr('name').replace('input_', ''),
                answerMap: JSON.stringify(id2ValueMap)
            }

        };

        return optionQuestion;
    }

    /**
     * Implementation for the single choice question
     * @param questionHtml
     * @param stringProblemID
     * @return {RadioOpetionQuestion}
     * @class old realisation
     * @extends BaseQuestion
     */
    function RadioOpetionQuestion(questionHtml, stringProblemID) {
        const optionQuestion = new BaseQuestion(questionHtml, stringProblemID);
        const question = optionQuestion.questionHtml.find('.choicegroup');
        optionQuestion.questionHtml = question.length === 1 ? $(question[0]) : null;
        optionQuestion.options = optionQuestion.questionHtml.find('input[type="radio"]');

        optionQuestion.isCanParse = function () {
            return optionQuestion.options.length > 0
        };

        optionQuestion.getRequestMap = function () {
            const id2ValueMap = {};
            this.options.each(index =>
                id2ValueMap[this.options[index].value] = $(this.options[index].parentNode).text().trim());
            return {
                type: 'select',
                questionID: this.questionHtml.attr('id').replace('inputtype_', ''),
                answerMap: JSON.stringify(id2ValueMap)
            }

        };

        return optionQuestion;
    }


    /**
     * Implementation for the question with checkbox
     * @param questionHtml
     * @param stringProblemID
     * @return {MultyChoseQuestion}
     * @class old realisation
     * @extends RadioOpetionQuestion
     */
    function MultyChoseQuestion(questionHtml, stringProblemID) {
        const multyChooseQuestion = new RadioOpetionQuestion(questionHtml, stringProblemID);
        multyChooseQuestion.options = multyChooseQuestion.questionHtml.find('input[type="checkbox"]');

        var baseRequestMapFunction = multyChooseQuestion.getRequestMap;
        multyChooseQuestion.getRequestMap = function () {
            var result = baseRequestMapFunction.call(this)
            result.type = 'multySelect';
            return result;
        };

        return multyChooseQuestion;
    }


    /**
     * Implementation of Tab for gradebook tab
     * @returns {Tab}
     * @class old realisation
     */
    function GradebookTab(button, content) {
        var greadebookTab = new Tab(button, content);

        greadebookTab.studentsTable = content.find('#student_table_body');
        greadebookTab.gradebookTableHeader = content.find('#gradebook_table_header');
        greadebookTab.gradebookTableBody = content.find('#gradebook_table_body');

        content.find('.student-search-field').on('change', function postinput() {
            updateData($(this).val());
        });

        greadebookTab.filterString = '';
        greadebookTab.loadTabData = function () {
            updateData()
        };

        function updateData(filterString = '')
        {
            function onSuccess(response) {
                greadebookTab.studentInfo = response.student_info;
                greadebookTab.examNames = response.exam_names;
                updateTables()
            }

            function onError() {
                alert("Can not load statistic fo select course");
            }

            $.ajax({
                traditional: true,
                type: "POST",
                url: "api/gradebook/",
                data: {filter: filterString},
                success: onSuccess,
                error: onError,
                dataType: "json"
            });
        }

        function updateTables() {
            greadebookTab.gradebookTableHeader.empty();
            greadebookTab.gradebookTableBody.empty();

            for (var i = 0; i < greadebookTab.examNames.length; i++) {
                greadebookTab.gradebookTableHeader.append('<th><div class="assignment-label">' + greadebookTab.examNames[i] + '</div></th>')
            }

            greadebookTab.studentsTable.empty();
            for (var i = 0; i < greadebookTab.studentInfo.length; i++) {
                greadebookTab.studentsTable.append(
                    '<tr class="gradebook-table-row" >' +
                    '<td>' +
                    '<a data-position="' + i + '">' + greadebookTab.studentInfo[i].username + '</a>' +
                    '</td>' +
                    '</tr>');
                var row = '<tr>';
                for (var g = 0; g < greadebookTab.studentInfo[i].grades.length; g++) {
                    row += '<td>';
                    row += greadebookTab.studentInfo[i].grades[g];
                    row += '</td>';
                }
                row += '</tr>';
                greadebookTab.gradebookTableBody.append(row);
            }
            $(greadebookTab.studentsTable).find('a').click(function (element) {
                var stat = {
                    y: greadebookTab.studentInfo[element.target.dataset['position']].grades,
                    x: greadebookTab.examNames,
                    type: 'bar',
                };
                var data = [stat];

                var layout = {
                    title: greadebookTab.studentInfo[element.target.dataset['position']].username,
                    showlegend: false
                };

                Plotly.newPlot('gradebook-stats-plot', data, layout, {displayModeBar: false});
            })
        }

        return greadebookTab;
    }

    function CohortTab(button, content) {
        var cohortTab = new Tab(button, content);

        cohortTab.cohortList = content.find('#cohort-check-list');
        cohortTab.emailBody = cohortTab.content.find('#email-body');
        cohortTab.emailBody.froalaEditor();

        content.find('#cohort-send-email-btn').click(function () {
            var ids = '';
            $("input:checkbox[name=cohort-checkbox]:checked").each(function () {
                if (ids.length > 0) {
                    ids += ',';
                }
                ids += $(this).val();
            });

            var request = {
                users_ids: ids,
                subject: $('#email-subject').val(),
                body: $('#email-body').froalaEditor('html.get'),
            };

            $.ajax({
                traditional: true,
                type: "POST",
                url: "api/cohort/send_email/",
                data: request,
                success: () => console.log('Emails are sended'),
                error:  () => console.log('Email sending failed'),
                dataType: "json"
            });
        });

        function updateCohort() {
            function onSuccess(response) {
                var plot = {
                    y: response.values,
                    x: response.labels,
                    type: 'bar',
                };
                var data = [plot];
                Plotly.newPlot('cohort-plot', data, {}, {displayModeBar: false});

                cohortTab.cohortList.empty();
                for(var i=0;i< response.cohorts.length;i++){
                    cohortTab.cohortList.append(
                        '<li>' +
                            '<div>'+
                                '<input name="cohort-checkbox" type="checkbox" value="'+
                                    response.cohorts[i].students_id+'">'+
                                '<label style="display: inline-block;">'+
                                    '&ensp;'+response.labels[i]+':&ensp;'+response.cohorts[i].students_username+
                                '</label>'+
                            '</div>'+
                        '</li>'
                    )
                }
            }

            function onError() {
                alert("Statistics for the select course cannot be loaded.");
            }

            $.ajax({
                traditional: true,
                type: "POST",
                url: "api/cohort/",
                success: onSuccess,
                error: onError,
                dataType: "json"
            });

        }
        cohortTab.loadTabData = updateCohort;
        cohortTab.emailBody.on('froalaEditor.image.beforeUpload', function (e, editor, files) {
            if (files.length) {
                // Create a File Reader.
                var reader = new FileReader();

                // Set the reader to insert images when they are loaded.
                reader.onload = function (e) {
                    var result = e.target.result;
                    editor.image.insert(result, null, null, editor.image.get());
                };

                // Read image as base64.
                reader.readAsDataURL(files[0]);
            }

            // Stop default upload chain.
            return false;
        });

        return cohortTab;
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
                $content.find('#section-gradebook')),
            CohortTab(
                $content.find('#cohort-btn'),
                $content.find('#section-cohort'))
        ];
        tabList.forEach(function (tab) {
            tab.button.click(function () {
                toggleToTab(tab)
            })
        });

        toggleToTab(tabList[0]);
    });

    window.setup_debug = function (element_id, edit_link, staff_context) {
        // stub function.
    };

}).call(this);
