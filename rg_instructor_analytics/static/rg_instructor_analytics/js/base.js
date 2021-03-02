$(function() {
    'use strict';
    var CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2';
    var $content = $('.' + CSS_INSTRUCTOR_CONTENT);
    var courseSelect = $content.find('#select_course');
    var cohortSelect = $content.find('#select_cohort');

    var tabNames = {
        'enrollment-stats-btn': 'enrollment',
        'activity-btn': 'activity',
        'problems-btn': 'problems',
        'gradebook-btn': 'gradebook',
        'cohort-btn': 'cohort',
        'funnel-btn': 'funnel',
        'suggestion-btn': 'suggestion'
    }

    var tabs = {
        enrollment: EnrollmentTab(
            $content.find('#enrollment-stats-btn'),
            $content.find('#section-enrollment-stats')
        ),
        activity: ActivityTab(
            $content.find('#activity-btn'),
            $content.find('#section-activity')
        ),
        problems: ProblemTab(
            $content.find('#problems-btn'),
            $content.find('#section-problems')),
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

    var firstTab = $content.find('.instructor-nav').children().first();
    if (firstTab.length) {
        var courseId = courseSelect.val();
        if (cohortSelect) {
            var cohortID = cohortSelect.val();
            var courseId = $content.find('#select_cohort option:selected').data('course-id');
        }
        var tabId = firstTab.children()[0].id;

        var tabHolder = new TabHolder(tabs, courseId, cohortID);
        tabHolder.toggleToTab(tabNames[tabId]);

        courseSelect.change(function(item) {
            tabHolder.selectCourse(item.target.value);
        });
        cohortSelect.change(function(item) {
            tabHolder.selectCohort(item.target.value, $content.find('#select_cohort option:selected').data('course-id'));
        });
    }

    window.setup_debug = function (element_id, edit_link, staff_context) {
        // stub function.
    };

}).call(this);
