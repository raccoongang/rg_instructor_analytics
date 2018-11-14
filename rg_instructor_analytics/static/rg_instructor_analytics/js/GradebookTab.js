/**
 * Implementation of Tab for the gradebook tab
 * @returns {Tab}
 * @class old realisation
 */
function GradebookTab(button, content) {
    var greadebookTab = new Tab(button, content);

    greadebookTab.studentsTable = content.find('#student_table_body');
    greadebookTab.gradebookTableHeader = content.find('#gradebook_table_header');
    greadebookTab.gradebookTableBody = content.find('#gradebook_table_body');

    greadebookTab.filterString = '';
    greadebookTab.loadTabData = function (resetCohort) {
        updateData('', resetCohort)
    };

    function updateData(filterString = '', resetCohort) {
        
        function onSuccess(response) {
            if (!response.students_names.length){
                greadebookTab.gradebookTableHeader.html(
                    `<div style="width: 100%;
                                 text-align: center;
                                 margin: 0 auto;
                                 padding: 150px 0;">No data to display</div>`
                );
                return
            }
            
            greadebookTab.studentInfo = response.student_info;
            greadebookTab.examNames = response.exam_names;
            greadebookTab.studentsNames = response.students_names;
            updateTables();
            greadebookTab.populateCohortSelect(response, resetCohort);
        }

        function onError() {
            alert("Can not load statistic for select course");
        }
        
        $.ajax({
            traditional: true,
            type: "POST",
            url: "api/gradebook/",
            data: { filter: filterString, reset_cohort: resetCohort },
            success: onSuccess,
            error: onError,
            dataType: "json"
        });
    }
    let inputValue = '';

    function updateTables() {
        var htmlStringStudents = '';
        var htmlStringResults = '';
        greadebookTab.gradebookTableHeader.empty();
        
        var htmlTemp = `<table class="table table-striped rg-table"><thead><tr><th><form class="student-search"><input value="${django.gettext(inputValue)}" type="search" class="student-search-field" placeholder="Search students"/></form></th>`;
        
        for (var i = 0; i < greadebookTab.examNames.length; i++) {
            htmlTemp += `<th class="">${greadebookTab.examNames[i]}</th>`;
        }
        htmlTemp += `</tr></thead><tbody>`;

        for (var i = 0; i < greadebookTab.studentInfo.length; i++) {
            var htmlStringResults = ``;
            for (var nameIndex = 0; nameIndex < greadebookTab.examNames.length; nameIndex++) {
                let studentInfo = greadebookTab.studentInfo[i][greadebookTab.examNames[nameIndex]];
                studentInfo = studentInfo !== undefined ? studentInfo : 0;
                htmlStringResults += `<td>${studentInfo}</td>`;
            }
            htmlTemp += `<tr><td><a data-position="${i}">${greadebookTab.studentsNames[i]}</a></td>${htmlStringResults}</tr>`;
        }
        htmlTemp += `</tbody></table>`;

        greadebookTab.gradebookTableHeader.append(htmlTemp);
        let $input = $('.student-search-field');
        $input[0].addEventListener('keyup', function(e){
            if (e.keyCode == 13) {
                e.preventDefault();
                this.blur();
            }
        });

        $(".student-search").submit(function(e) {
            e.preventDefault();
        });

        $input.on('change', (e) => {
            inputValue = e.target.value;
            updateData(inputValue);
            e.target.value = inputValue;
        });

        $('tr td a').click(function (element) {
            $('.rg-table tr:not(element.currentTarget)').removeClass('active');
            $(element.currentTarget).parent('td').parent('tr').toggleClass('active');
            let colorArray = greadebookTab.examNames.map((item, idx, arr) => {
                if (idx === arr.length - 1) {
                    return '#c14f84';
                }
                return '#568ecc';
            });

            let studentsGrades = [];
            const studentPosition = element.target.dataset['position'];
            for (var nameIndex = 0; nameIndex < greadebookTab.examNames.length; nameIndex++)
                studentsGrades.push(greadebookTab.studentInfo[studentPosition][greadebookTab.examNames[nameIndex]])

            var stat = {
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
                title: greadebookTab.studentInfo[element.target.dataset['position']].username,
                showlegend: false,
                xaxis: {domain: [0, 0.97]},
            };
            Plotly.newPlot('gradebook-stats-plot', data, layout, {displayModeBar: false});
        })
    }
    return greadebookTab;
}
