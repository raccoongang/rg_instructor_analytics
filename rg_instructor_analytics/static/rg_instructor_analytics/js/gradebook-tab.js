/**
 * Implementation of Tab for the gradebook tab
 * @returns {Tab}
 * @class old realisation
 */
function GradebookTab(button, content) {
    var greadebookTab = new Tab(button, content);
    var $tbody = $('#gradebook_table_body');
    var $loader = $('#gb-loader');
    var $statsPlot = $('#gradebook-stats-plot');
    var $tabBanner = content.find('.tab-banner');
    var $tabContent = content.find('.tab-content');
    
    greadebookTab.studentsTable = content.find('#student_table_body');
    greadebookTab.gradebookTableHeader = content.find('#gradebook_table_header');
    greadebookTab.gradebookTableBody = content.find('#gradebook_table_body');
    
    greadebookTab.filterString = '';

    $('.export-gradebook-to-csv').click(function(e) {
        exportToCSV('api/gradebook/', greadebookTab.tabHolder.course, {filter: greadebookTab.filterString});
    });

    function loadTabData() {
        var courseDatesInfo = $('.course-dates-data').data('course-dates')[greadebookTab.tabHolder.course];
        if (courseDatesInfo.course_is_started) {
            $tabBanner.prop('hidden', true);
            $tabContent.prop('hidden', false);

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
    
    function updateData(filter) {
        greadebookTab.filterString = filter || '';
        greadebookTab.gradebookTableHeader.empty();
        greadebookTab.gradebookTableBody.empty();
        $statsPlot.addClass('hidden');
        
        function onSuccess(response) {
            greadebookTab.studentInfo = response.student_info;
            greadebookTab.examNames = response.exam_names;
            greadebookTab.studentsNames = response.students_names;
            updateTables(greadebookTab.filterString);
        }
        
        function onError() {
            alert("Can't load data for selected course!");
        }
        
        $.ajax({
            type: "POST",
            url: "api/gradebook/",
            data: {filter: greadebookTab.filterString},
            dataType: "json",
            traditional: true,
            success: onSuccess,
            error: onError,
            beforeSend: toggleLoader,
            complete: toggleLoader,
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
        
        for (var j = 0; j < greadebookTab.studentInfo.length; j++) {
            var htmlStringResults = '';
            var studentName = greadebookTab.studentsNames[j][0];
            var isEnrolled =  greadebookTab.studentsNames[j][1];
            
            for (var nameIndex = 0; nameIndex < greadebookTab.examNames.length; nameIndex++) {
                var exName = greadebookTab.studentInfo[j][greadebookTab.examNames[nameIndex]];
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

        $(greadebookTab.gradebookTableBody).click(function (evt) {
            var colorArray = greadebookTab.examNames.map(function (item, idx, arr) {
                if (idx === arr.length - 1) {
                    return '#c14f84';
                }
                return '#568ecc';
            });

            var studentsGrades = [];
            var studentPosition = evt.target.dataset['position'];
            var stat;
            $statsPlot.removeClass('hidden');
            for (var nameIndex = 0; nameIndex < greadebookTab.examNames.length; nameIndex++) {
                studentsGrades.push(
                  greadebookTab.studentInfo[studentPosition][greadebookTab.examNames[nameIndex]]
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
                title: greadebookTab.studentInfo[evt.target.dataset['position']].username,
                showlegend: false,
                xaxis: {domain: [0, 0.97]},
            };

            $('.gradebook-table-row').removeClass('active');
            $(evt.target).closest('.gradebook-table-row').toggleClass('active');
            $('.enrollment-title-1.hidden').removeClass('hidden');
            $('.enrollment-title-text-1.hidden').removeClass('hidden');

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
