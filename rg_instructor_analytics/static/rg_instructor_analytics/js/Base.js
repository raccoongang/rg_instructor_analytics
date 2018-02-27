$(function () {
    'use strict';
    var CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2';

    var tabList = [];

    function toggleToTab(tab) {
        tabList.forEach(function (t) {
            t.setActive(t === tab);
        });
    }

    $(function () {
        var $content = $('.' + CSS_INSTRUCTOR_CONTENT);
        tabList = [
            EnrollmentTab(
                $content.find('#enrollment-stats-btn'),
                $content.find('#section-enrollment-stats')),
            ProblemTab(
                $content.find('#problems-btn'),
                $content.find('#section-problem')),
            GradebookTab(
                $content.find('#gradebook-btn'),
                $content.find('#section-gradebook')),
            CohortTab(
                $content.find('#cohort-btn'),
                $content.find('#section-cohort')),
            FunnelTab(
                $content.find('#funnel-btn'),
                $content.find('#section-funnel'))
        ];
        tabList.forEach(function (tab) {
            tab.button.click(function () {
                toggleToTab(tab);
            });
        });

        toggleToTab(tabList[0]);
    });

    window.setup_debug = function (element_id, edit_link, staff_context) {
        // stub function.
    };

}).call(this);
