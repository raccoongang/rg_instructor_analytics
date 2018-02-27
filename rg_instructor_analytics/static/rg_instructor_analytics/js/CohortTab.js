function CohortTab(button, content) {
    var cohortTab = new Tab(button, content);

    cohortTab.cohortList = content.find('#cohort-check-list');
    cohortTab.emailBody = cohortTab.content.find('#email-body');
    cohortTab.emailBody.froalaEditor({
        toolbarButtons: ['undo', 'redo' , 'bold', '|', 'alert', 'clear', 'insert']
    });

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
