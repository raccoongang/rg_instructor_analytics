$(function() {
    'use strict';
    var CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2';
    var $content = $('.' + CSS_INSTRUCTOR_CONTENT);
    var courseSelect = $content.find('#select_course');
    var cohortSelect = $content.find('#select_cohort');
    var enrollmentTypeSelect = $content.find('#select_enrollment_type');


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
        var cohortID, enrollmentType = null
        var courseId = courseSelect.val();
        if (cohortSelect) {
            cohortID = cohortSelect.val();
            courseId = $content.find('#select_cohort option:selected').data('course-id');
            if (enrollmentTypeSelect) {
              enrollmentType = enrollmentTypeSelect.val();
            }
        }
        var tabId = firstTab.children()[0].id;

        var tabHolder = new TabHolder(tabs, courseId, cohortID, enrollmentType);
        tabHolder.toggleToTab(tabNames[tabId]);

        courseSelect.change(function(item) {
            tabHolder.selectCourse(item.target.value);
        });
        if (cohortSelect) {
        cohortSelect.change(function(item) {
            tabHolder.selectCohort(item.target.value, $content.find('#select_cohort option:selected').data('course-id'));
        });
        if (enrollmentTypeSelect) {
          enrollmentTypeSelect.change(function(item) {
              tabHolder.selectEnrollmentType(item.target.value);
          });
        }
      }
    }

    window.setup_debug = function (element_id, edit_link, staff_context) {
        // stub function.
    };

});
