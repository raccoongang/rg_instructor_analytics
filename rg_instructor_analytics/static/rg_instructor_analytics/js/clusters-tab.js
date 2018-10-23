function CohortTab(button, content) {
    var cohortTab = new Tab(button, content);
    var $loader = $('#cl-loader');

    cohortTab.cohortList = content.find('#cohort-check-list');
    cohortTab.emailBody = cohortTab.content.find('#email-body');

    //WYSIWYG init
    $('#email-body').richText();

    content.find('#cohort-send-email-btn').click(function () {
        var $subject = content.find('#email-subject');
        var $richTextEditor = content.find('.richText-editor');
        var $cohortCheckbox = content.find("input:checkbox[name=cohort-checkbox]:checked");
        var ids = '';
        var request;

        function isValid(data) {
            return !!data.users_ids && !!data.subject && !!data.body
        }

        content.find('.send-email-message').addClass('hidden');

        $cohortCheckbox.each(function () {
            if (ids.length > 0) {
                ids += ',';
            }
            ids += $(this).val();
        });

        request = {
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
            dataType: "json",
            success: function () {
                content.find('.send-email-message.success-message').removeClass('hidden');
                // clear fields
                $subject.val('');
                $richTextEditor.html('');
                $cohortCheckbox.prop('checked', false)
            },
            error: function () {
                content.find('.send-email-message.error-message').removeClass('hidden');
            },
        });
    });
    
    function toggleLoader() {
        $loader.toggleClass('hidden');
    }

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
                var item = 'cohort-checkbox' + i;
                var studentsId = response.cohorts[i].students_id;
                var label  = response.labels[i];
                
                cohortTab.cohortList.append(
                    _.template(
                        '<li>' +
                            '<div>' +
                                '<input ' +
                                    'id="<%= item %>" ' +
                                    'name="cohort-checkbox" ' +
                                    'type="checkbox" ' +
                                    'value="<%= studentsId %>" ' +
                                '>' +
                                '<label for="<%= item %>" class="emails-label">' +
                                    '<%= label %>' +
                                '</label>' +
                            '</div>' +
                        '</li>'
                    )({
                        item: item,
                        studentsId: studentsId,
                        label: label,
                    })
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

    function loadTabData() {
        var courseDatesInfo = $('.course-dates-data').data('course-dates')[cohortTab.tabHolder.course];
        if (courseDatesInfo.course_is_started) {
            $('.tab-banner').prop('hidden', true);
            $('.tab-content').prop('hidden', false);
        } else {
            $('.tab-banner').prop('hidden', false);
            $('.tab-content').prop('hidden', true);
        }

        updateCohort();
    }

    cohortTab.loadTabData = loadTabData;

    return cohortTab;
}
