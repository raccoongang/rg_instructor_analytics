function CohortTab(button, content) {
    var cohortTab = new Tab(button, content);
    var $loader = $('#cl-loader');
    var $tabBanner = content.find('.tab-banner');
    var $tabContent = content.find('.tab-content');
    var timerId;

    cohortTab.cohortList = content.find('#cohort-check-list');
    cohortTab.emailBody = cohortTab.content.find('#email-body');

    //WYSIWYG init
    $('#email-body').richText();

    content.find('#cohort-send-email-btn').click(function () {
        var $subject = content.find('#email-subject');
        var $richTextEditor = content.find('.richText-editor');
        var $cohortCheckbox = content.find("input:checkbox[name=cohort-checkbox]:checked");
        var emails = '';
        var request;

        function isValid(data) {
            return !!data.users_emails && !!data.subject && !!data.body
        }

        function showInfoMsg(msg){
            msg.removeClass('hidden');
            clearTimeout(timerId);
            timerId = setTimeout(function () {
                msg.addClass('hidden');
            }, 3000);
        }

        $cohortCheckbox.each(function () {
            if (emails.length > 0) {
                emails += ',';
            }
            emails += $(this).val();
        });

        request = {
            users_emails: emails,
            subject: $subject.val(),
            body: $richTextEditor.html(),
        };

        if (!isValid(request)) {
            showInfoMsg(content.find('.send-email-message.validation-error-message'));
            return;
        }

        $.ajax({
            type: "POST",
            url: "api/cohort/send_email/",
            data: request,
            dataType: "json",
            success: function () {
                showInfoMsg(content.find('.send-email-message.success-message'));
                // clear fields
                $subject.val('');
                $richTextEditor.html('');
                $cohortCheckbox.prop('checked', false)
            },
            error: function () {
                showInfoMsg(content.find('.send-email-message.error-message'));
            },
        });
    });
    
    function toggleLoader() {
        $loader.toggleClass('hidden');
    }

    function showEmailList() {
      $('.emails-list-button').on('click', function (ev) {
        ev.preventDefault();
        $(ev.currentTarget).parents('.block-emails-list').find('.cohort-emails-list').toggleClass('hidden');
      });
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
                var studentsEmails = response.cohorts[i].students_emails;
                var label  = response.labels[i];

                cohortTab.cohortList.append(
                    _.template(
                        '<li>' +
                            '<div>' +
                                '<input ' +
                                    'id="<%= item %>" ' +
                                    'name="cohort-checkbox" ' +
                                    'type="checkbox" ' +
                                    '<%if (studentsEmails.length == 0) {%> disabled <%}%>' +
                                    'value="<%= studentsEmails %>"' +
                                '>' +
                                '<label for="<%= item %>" class="emails-label">' +
                                    '<%= label %>' +
                                '</label>' +
                                '<%if (studentsEmails.length != 0) {%>' +
                                '<div class="block-emails-list">' +
                                    '<span class="cohort-emails-list">' +
                                      '<button class="emails-list-button">Show emails</button>' +
                                    '</span>' +
                                    '<span class="cohort-emails-list hidden">' +
                                      '<button class="emails-list-button">Hide emails</button>' +
                                      '<div class="emails-list-holder"><%= studentsEmails.join(", ") %></div>' +
                                    '</span>' +
                                '</div>' +
                                '<%}%>' +
                            '</div>' +
                        '</li>'
                    )({
                        item: item,
                        studentsEmails: studentsEmails,
                        label: label,
                    })
                )
            }
            showEmailList();
        }

        function onError() {
            alert("Statistics for the select course cannot be loaded.");
        }

        $.ajax({
            type: "POST",
            url: "api/cohort/",
            data: {
                course_id: cohortTab.tabHolder.course,
                cohort_id: cohortTab.tabHolder.cohort
            },
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
            $tabBanner.prop('hidden', true);
            $tabContent.prop('hidden', false);
            updateCohort();
        } else {
            $tabBanner.prop('hidden', false);
            $tabContent.prop('hidden', true);
        }
    }

    cohortTab.loadTabData = loadTabData;

    return cohortTab;
}
