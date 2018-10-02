$(function() {
    'use strict';
    var CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2';
    var $content = $('.' + CSS_INSTRUCTOR_CONTENT);
    var courseSelect = $content.find('#select_course');

    var tabs = {
        enrollment: EnrollmentTab(
            $content.find('#enrollment-stats-btn'),
            $content.find('#section-enrollment-stats')
        ),
        problems: ProblemTab(
            $content.find('#problems-btn'),
            $content.find('#section-problem')),
        gradebook: GradebookTab(
            $content.find('#gradebook-btn'),
            $content.find('#section-gradebook')),
        cohort: CohortTab(
            $content.find('#cohort-btn'),
            $content.find('#section-cohort')),
        funnel: FunnelTab(
            $content.find('#funnel-btn'),
            $content.find('#section-funnel')),
        suggestion: SuggestionTab(
            $content.find('#suggestion-btn'),
            $content.find('#section-suggestion'))
    };

    const tabHolder = new TabHolder(tabs, courseSelect.val());
    tabHolder.toggleToTab('enrollment');

    courseSelect.change(function(item) {
        tabHolder.selectCourse(item.target.value);
    });

    window.setup_debug = function (element_id, edit_link, staff_context) {
        // stub function.
    };

}).call(this);
