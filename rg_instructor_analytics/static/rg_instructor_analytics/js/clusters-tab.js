function CohortTab(button, content) {
    let cohortTab = new Tab(button, content);
    var $loader = $('#cl-loader');

    cohortTab.cohortList = content.find('#cohort-check-list');
    cohortTab.emailBody = cohortTab.content.find('#email-body');

    //WYSIWYG init
    $('#email-body').richText();

    content.find('#cohort-send-email-btn').click(function () {

        function isValid(data) {
            return !!data.users_ids && !!data.subject && !!data.body
        }

        content.find('.send-email-message').addClass('hidden');
        let $subject = content.find('#email-subject'),
            $richTextEditor = content.find('.richText-editor'),
            $cohortCheckbox = content.find("input:checkbox[name=cohort-checkbox]:checked"),
            ids = '';

        $cohortCheckbox.each(function () {
            if (ids.length > 0) {
                ids += ',';
            }
            ids += $(this).val();
        });

        let request = {
            users_ids: ids,
            subject: $subject.val(),
            body: $richTextEditor.html(),
        };

        if (!isValid(request)) {
            content.find('.send-email-message.validation-error-message').removeClass('hidden');
            return;
        }

        $.ajax({
            type: "POST",
            url: "api/cohort/send_email/",
            data: request,
            success: () => {
                content.find('.send-email-message.success-message').removeClass('hidden');
                // clear fields
                $subject.val('');
                $richTextEditor.html('');
                $cohortCheckbox.prop('checked', false)
            },
            error: () => {
                content.find('.send-email-message.error-message').removeClass('hidden');
            },
            dataType: "json"
        });
    });
    
    function toggleLoader() {
        $loader.toggleClass('hidden');
    }

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
            type: "POST",
            url: "api/cohort/",
            dataType: "json",
            traditional: true,
            success: onSuccess,
            error: onError,
            beforeSend: toggleLoader,
            complete: toggleLoader,
        });

    }

    cohortTab.loadTabData = updateCohort;

    return cohortTab;
}
