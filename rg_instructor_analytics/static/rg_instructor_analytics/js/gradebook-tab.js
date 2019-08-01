/**
 * Implementation of Tab for the gradebook tab
 * @returns {Tab}
 * @class old realisation
 */
function GradebookTab(button, content) {
    var greadebookTab = new Tab(button, content);
    var $tabBanner = content.find('.tab-banner');
    var $tabContent = content.find('.tab-content');
    var $tabSubtitle = content.find('.js-analytics-subtitle');
    var $tabSubtitleText = content.find('.js-analytics-subtitle-text');

    var $tbody = $('#gradebook_table_body');
    var $loader = $('#gb-loader');
    var $statsPlot = $('#gradebook-stats-plot');
    var $loaderDiscussion = $('.gradebook-discussion-plot .loader');
    var $discussionPlot = $('#gradebook-discussion-stats-plot');
    var $loaderVideo = $('.gradebook-video-plot .loader');
    var $videoPlot = $('#gradebook-video-stats-plot');
    var $loaderStudentStep = $('.gradebook-student-step-plot .loader');
    var $studentStepPlot = $('#gradebook-student-step-stats-plot');
    var $lastVisitInfo = $('.js-last-student-visit');

    greadebookTab.studentsTable = content.find('#student_table_body');
    greadebookTab.gradebookTableHeader = content.find('#gradebook_table_header');
    greadebookTab.gradebookTableBody = content.find('#gradebook_table_body');
    
    greadebookTab.filterString = '';

    function loadTabData() {
        var courseDatesInfo = $('.course-dates-data').data('course-dates')[greadebookTab.tabHolder.course];
        if (courseDatesInfo.course_is_started) {
            $tabBanner.prop('hidden', true);
            $tabContent.prop('hidden', false);
            $tabSubtitle.addClass('hidden');
            $tabSubtitleText.addClass('hidden');
            updateData();
        } else {
            $tabBanner.prop('hidden', false);
            $tabContent.prop('hidden', true);
        }
    }

    greadebookTab.loadTabData = loadTabData;

    function toggleLoader() {
        $loader.toggleClass('hidden');
    }

    function onError() {
        alert("Can't load data for selected course!");
    }
    
    function updateData(filter) {
        var filterString = filter || '';
        greadebookTab.gradebookTableHeader.empty();
        greadebookTab.gradebookTableBody.empty();
        $statsPlot.addClass('hidden');
        $discussionPlot.empty();
        $videoPlot.empty();
        $studentStepPlot.empty();
        $lastVisitInfo.prop('hidden', true).empty();

        function onSuccess(response) {
            greadebookTab.studentExamValues = response.student_exam_values;
            greadebookTab.examNames = response.exam_names;
            greadebookTab.studentInfo = response.students_info;
            updateTables(filterString);
        }
        
        $.ajax({
            type: "POST",
            url: "api/gradebook/",
            data: {
                cohort_id: greadebookTab.tabHolder.cohort,
                filter: filterString
            },
            dataType: "json",
            traditional: true,
            success: onSuccess,
            error: onError,
            beforeSend: toggleLoader,
            complete: toggleLoader,
        });
    }

    function renderDiscussionActivity(data, userName) {
        var stat = {
            y: data.activity_count,
            x: data.thread_names,
            type: 'bar',
            marker:{
                color: '#568ecc'
            },
        };

        var y_template = {
        };

        if (Math.max(...data.activity_count) <= 5) {
            y_template["nticks"] = Math.max(...data.activity_count)+1
        }

        var layout = {
            title: userName,
            showlegend: false,
            xaxis: {
                tickangle: 90,
            },
            yaxis: y_template,
        };

        Plotly.newPlot('gradebook-discussion-stats-plot', [stat], layout, {displayModeBar: false});
        $loaderDiscussion.addClass('hidden');

    }

    function renderVideoActivity(data, userName) {
        var colorVideoArray = data.videos_completed.map(function (isCompleted) {
            return isCompleted ? '#50c156' : '#568ecc';
        });

        var stat = {
            y: data.videos_time,
            x: data.videos_names,
            type: 'bar',
            marker:{
                color: colorVideoArray
            },
        };

        var y_template = {
        };

        if (Math.max(...data.videos_time) <= 5) {
            y_template["nticks"] = Math.max(...data.videos_time)+1
        }

        var layout = {
            title: userName,
            showlegend: false,
            xaxis: {
                tickangle: 90,
            },
            yaxis: y_template,
        };

        Plotly.newPlot('gradebook-video-stats-plot', [stat], layout, {displayModeBar: false});
        $loaderVideo.addClass('hidden');
    }

    function getDiscussionActivity(studentPosition) {
        var userName = greadebookTab.studentInfo[studentPosition]['username'];

        $discussionPlot.empty();
        $loaderDiscussion.removeClass('hidden');

        $.ajax({
            type: "POST",
            url: "api/gradebook/discussion/",
            data: {
                cohort_id: greadebookTab.tabHolder.cohort,
                username: userName
            },
            dataType: "json",
            traditional: true,
            success: function (response) {
              renderDiscussionActivity(response, userName);
            },
            error: onError,
        });
    }

    function getVideoActivity(studentPosition) {
        var userName = greadebookTab.studentInfo[studentPosition]['username'];

        $videoPlot.empty();
        $loaderVideo.removeClass('hidden');

        $.ajax({
            type: "POST",
            url: "api/gradebook/video_views/",
            data: {
                cohort_id: greadebookTab.tabHolder.cohort,
                username: userName
            },
            dataType: "json",
            traditional: true,
            success: function (response) {
              renderVideoActivity(response, userName);
            },
            error: onError,
        });
    }

    function renderStudentStep(data, userName) {
        var heightLayout = data.tickvals.length * 20;
        var defaultStat = {
            x: data.x_default,
            y: data.tickvals
        };

        var stat = {
            x: data.steps,
            y: data.units,
            mode: 'lines+markers',
            name: '',
            marker: {
                size: 8
            },
            line: {
                dash: 'solid',
                width: 1
            }
        };

        var x_template = {
        };

        if (Math.max(...data.steps) <= 5) {
            x_template["nticks"] = Math.max(...data.steps)+1
        }

        var layout = {
            title: userName,
            showlegend: false,
            height: heightLayout > 450 && heightLayout || 450,
            xaxis: x_template,
            yaxis: {
                ticktext: data.ticktext,
                tickvals: data.tickvals,
                tickmode: 'array',
                automargin: true,
                autorange: true,
            },
        };

        Plotly.newPlot('gradebook-student-step-stats-plot', [defaultStat, stat], layout, {displayModeBar: false});
        $loaderStudentStep.addClass('hidden');
    }

    function getStudentStep(studentPosition) {
        var userName = greadebookTab.studentInfo[studentPosition]['username'];
        $studentStepPlot.empty();
        $loaderStudentStep.removeClass('hidden');

        $.ajax({
            type: "POST",
            url: "api/gradebook/student_step/",
            data: {
                cohort_id: greadebookTab.tabHolder.cohort,
                username: userName
            },
            dataType: "json",
            traditional: true,
            success: function (response) {
              renderStudentStep(response, userName);
            },
            error: onError,
        });
    }

    function updateTables(filterString) {
        var htmlStringStudents = '';
        var htmlStringStudentsUnenroll = '';
        var value = filterString;
        var $searchInput;
        var htmlTemp;
        
        var htmlTemplate = (
            '<div class="gradebook-table-cell">' +
            '<form class="student-search">' +
            '<input ' +
            'value="<%= value %>" ' +
            'type="search" ' +
            'class="student-search-field" ' +
            'placeholder="<%= placeholder %>" ' +
            '/>' +
            '</form>' +
            '</div>'
        );

        for (var i = 0; i < greadebookTab.examNames.length; i++) {
            htmlTemplate += (
                '<div class="gradebook-table-cell">' +
                '<div class="assignment-label">' +
                greadebookTab.examNames[i] +
                '</div>' +
                '</div>'
            );
        }
        
        htmlTemp = _.template(htmlTemplate)({
            value: value,
            placeholder: django.gettext("Search students"),
        });
        
        greadebookTab.gradebookTableHeader.append(htmlTemp);
        
        $searchInput = $('.student-search-field');
        $searchInput[0].addEventListener('keyup', function(e) {
            if (e.keyCode == 13) {
                e.preventDefault();
                this.blur();
            }
        });
        
        $(".student-search").submit(function(e) {
            e.preventDefault();
        });
        
        $searchInput.on('change', function(evt) {
            var filterValue = evt.target.value;
            updateData(filterValue);
        });
        greadebookTab.studentsTable.empty();
        
        for (var j = 0; j < greadebookTab.studentExamValues.length; j++) {
            var htmlStringResults = '';
            var studentName = greadebookTab.studentInfo[j]['username'];
            var isEnrolled =  greadebookTab.studentInfo[j]['is_enrolled'];
            
            for (var nameIndex = 0; nameIndex < greadebookTab.examNames.length; nameIndex++) {
                var exName = greadebookTab.studentExamValues[j][greadebookTab.examNames[nameIndex]];
                htmlStringResults += '<div class="gradebook-table-cell">' + exName + '</div>';
            }

            if (isEnrolled) {
                htmlStringStudents += _.template(
                    '<div class="gradebook-table-row">' +
                        '<div class="gradebook-table-cell">' +
                            '<a data-position="<%= dataPosition %>"><%= studentName %></a>' +
                        '</div>' +
                        htmlStringResults +
                    '</div>'
                )({
                    studentName: studentName,
                    dataPosition: j,
                });
            } else {
                htmlStringStudentsUnenroll += _.template(
                    '<div class="gradebook-table-row">' +
                        '<div class="gradebook-table-cell">' +
                            '<a data-position="<%= dataPosition %>"><%= studentName %> (unenroll)</a>' +
                        '</div>' +
                        htmlStringResults +
                    '</div>'
                )({
                    studentName: studentName,
                    dataPosition: j,
                });
            }
        }
        
        greadebookTab.gradebookTableBody.append(htmlStringStudents);
        greadebookTab.gradebookTableBody.append(htmlStringStudentsUnenroll);
        
        //Make cells width equal to biggest cell
        var maxLength = 0;
        var $tableCells = $('.gradebook-table-cell:not(:first-child)');
        $tableCells.each(function (item) {
            var width = $tableCells[item].clientWidth;
            if (maxLength < width) {
                maxLength = width;
            }
        });
        
        $tableCells.each(function (item) {
            $tableCells[item].style.flex = '0 0 ' + maxLength + 'px';
        });

        $(greadebookTab.gradebookTableBody).off('click');
        $(greadebookTab.gradebookTableBody).on('click', function (evt) {
            var colorArray = greadebookTab.examNames.map(function (item, idx, arr) {
                if (idx === arr.length - 1) {
                    return '#c14f84';
                }
                return '#568ecc';
            });

            var studentsGrades = [];
            var studentPosition = evt.target.dataset['position'];
            var stat;
            var lastVisit = greadebookTab.studentInfo[studentPosition]['last_visit'];
            $lastVisitInfo.prop('hidden', false).html('Date of the last Course visit: ' + lastVisit);

            getDiscussionActivity(studentPosition);
            getVideoActivity(studentPosition);
            getStudentStep(studentPosition);

            $statsPlot.removeClass('hidden');
            for (var nameIndex = 0; nameIndex < greadebookTab.examNames.length; nameIndex++) {
                studentsGrades.push(
                  greadebookTab.studentExamValues[studentPosition][greadebookTab.examNames[nameIndex]]
                );
            }

            stat = {
                y: studentsGrades,
                x: greadebookTab.examNames,
                type: 'bar',
                marker:{
                    color: colorArray
                },
                width: 0.6,
            };
            var data = [stat];

            var layout = {
                title: greadebookTab.studentExamValues[evt.target.dataset['position']].username,
                showlegend: false,
                xaxis: {domain: [0, 0.97]},
            };

            $('.gradebook-table-row').removeClass('active');
            $(evt.target).closest('.gradebook-table-row').toggleClass('active');
            $tabSubtitle.removeClass('hidden');
            $tabSubtitleText.removeClass('hidden');

            Plotly.newPlot('gradebook-stats-plot', data, layout, {displayModeBar: false});
        })
    }

    $tbody.on('scroll', function() {
        var scrollLeft = $tbody.scrollLeft();
        
        $('#gradebook_table_header').css("left", -scrollLeft);
        $('.gradebook-table-cell:first-child').css("left", scrollLeft)
    });

    return greadebookTab;
}
