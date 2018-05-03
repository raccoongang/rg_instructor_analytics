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
    greadebookTab.loadTabData = function () {
        updateData()
    };

    function updateData(filterString = '') {
        function onSuccess(response) {
            greadebookTab.studentInfo = response.student_info;
            greadebookTab.examNames = response.exam_names;
            greadebookTab.studentsNames = response.students_names;
            updateTables()
        }

        function onError() {
            alert("Can not load statistic for select course");
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
    let inputValue = '';

    function updateTables() {
        var htmlStringStudents = '';
        var htmlStringResults = '';

        var htmlTemp = `<div class="gradebook-table-cell"><form class="student-search">
            <input 
                value="${django.gettext(inputValue)}" 
                type="search" 
                class="student-search-field" 
                placeholder="Search students"
            />
            </form></div>`;

        greadebookTab.gradebookTableHeader.empty();
        greadebookTab.gradebookTableBody.empty();

        for (var i = 0; i < greadebookTab.examNames.length; i++) {
            htmlTemp += `
                <div class="gradebook-table-cell">
                    <div class="assignment-label">${greadebookTab.examNames[i]}</div>
                </div>
            `;
        }
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

        greadebookTab.studentsTable.empty();

        for (var i = 0; i < greadebookTab.studentInfo.length; i++) {
            var htmlStringResults = '';
            for (var nameIndex = 0; nameIndex < greadebookTab.examNames.length; nameIndex++) {
                htmlStringResults += `
                    <div class="gradebook-table-cell">
                        ${greadebookTab.studentInfo[i][greadebookTab.examNames[nameIndex]]}
                    </div>
                `
            }

            htmlStringStudents +=
                `<div class="gradebook-table-row">
                    <div class="gradebook-table-cell">
                        <a data-position="${i}">${greadebookTab.studentsNames[i]}</a>
                    </div>
                    ${htmlStringResults}
                </div>`;
        }

        greadebookTab.gradebookTableBody.append(htmlStringStudents);

        //Make cells width equal to biggest cell
        let maxLength = 0;
        let $tableCells = $('.gradebook-table-cell:not(:first-child)');

        $tableCells.each((item) => {
            let width = $tableCells[item].clientWidth;
            if (maxLength < width) {
                maxLength = width;
            }
        });

        $tableCells.each((item) => {
            $tableCells[item].style.flex = `0 0 ${maxLength}px`;
        });

        $(greadebookTab.gradebookTableBody).click(function (element) {
            let colorArray = greadebookTab.examNames.map((item, idx, arr) => {
                if (idx === arr.length - 1) {
                    return '#c14f84';
                }
                return '#568ecc';
            })

            var stat = {
                y: greadebookTab.studentInfo[element.target.dataset['position']].grades,
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
            $('.gradebook-table-row').removeClass('active');
            $(element.target).closest('.gradebook-table-row').toggleClass('active');
            $('.enrollment-title-1.hidden').removeClass('hidden');
            $('.enrollment-title-text-1.hidden').removeClass('hidden');
            Plotly.newPlot('gradebook-stats-plot', data, layout, {displayModeBar: false});
        })
    }
    let $tbody = $('#gradebook_table_body');
    $tbody.on('scroll',() => {

        let scrollLeft = $tbody.scrollLeft();
    
        $('#gradebook_table_header').css("left", -scrollLeft);
        $('.gradebook-table-cell:first-child').css("left", scrollLeft)
    });
    return greadebookTab;
}
