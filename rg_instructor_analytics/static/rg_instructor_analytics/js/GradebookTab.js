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

    function updateData(filterString = '') {
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
};
