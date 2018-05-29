function CohortTab(button, content) {
    let cohortTab = new Tab(button, content);

    cohortTab.cohortList = content.find('#cohort-check-list');
    cohortTab.emailBody = cohortTab.content.find('#email-body');

    //WYSIWYG init
    $('#email-body').richText();

    content.find('#cohort-send-email-btn').click(function () {
        // FIXME used for prevent sending email to students, during presentation
        return;
        let ids = '';
        $("input:checkbox[name=cohort-checkbox]:checked").each(function () {
            if (ids.length > 0) {
                ids += ',';
            }
            ids += $(this).val();
        });

        let request = {
            users_ids: ids,
            subject: $('#email-subject').val(),
            body: $('.richText-editor').html(),
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
            let plot = {
                y: response.values,
                x: response.labels,
                type: 'bar',
            };
            let data = [plot];
            Plotly.newPlot('cohort-plot', data, {}, {displayModeBar: false});

            cohortTab.cohortList.empty();
            for (let i = 0; i < response.cohorts.length; i++) {
                let item = 'cohort-checkbox' + i;
                cohortTab.cohortList.append(
                    `<li>
                        <div>
                            <input 
                                id="${item}" 
                                name="cohort-checkbox" 
                                type="checkbox" 
                                value="${response.cohorts[i].students_id}"
                            >
                            <label for="${item}" style="display: inline-block;">${response.labels[i]}</label>
                        </div>
                    </li>`
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
