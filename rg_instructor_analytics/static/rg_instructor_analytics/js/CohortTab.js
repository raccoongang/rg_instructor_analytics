function CohortTab(button, content) {
    var cohortTab = new Tab(button, content);

    cohortTab.cohortList = content.find('#cohort-check-list');
    cohortTab.emailBody = cohortTab.content.find('#email-body');

    //WYSIWYG init
    $('#email-body').richText();

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
            type: "POST",
            url: "api/cohort/send_email/",
            data: request,
            success: () => console.log('Emails are sended'),
            error: () => console.log('Email sending failed'),
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
            for (var i = 0; i < response.cohorts.length; i++) {
                cohortTab.cohortList.append(
                    '<li>' +
                    '<div>' +
                    '<input name="cohort-checkbox" type="checkbox" value="' +
                    response.cohorts[i].students_id + '">' +
                    '<label style="display: inline-block;">' +
                    '&ensp;' + response.labels[i] + ':&ensp;' + response.cohorts[i].students_username +
                    '</label>' +
                    '</div>' +
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

    return cohortTab;
}
