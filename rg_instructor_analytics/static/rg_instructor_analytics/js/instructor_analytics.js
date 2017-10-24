(function () {
    'use strict';
    var CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2';

    var tabList = [];

    function Tab(button, content) {
        this.button = button;
        this.content = content;
        this.setActive = function (isActive) {
            if (isActive) {
                content.addClass('active-section');
                button.addClass('active-section');
            } else {
                content.removeClass('active-section');
                button.removeClass('active-section');
            }
        }
    }

    function toogleToTab(tab) {
        tabList.forEach(function (t) {
            t.setActive(t === tab)
        })
    }

    $(function () {
        var $content;
        $content = $('.' + CSS_INSTRUCTOR_CONTENT);
        tabList = [
            new Tab(
                $content.find('#enrollment-stats-btn'),
                $content.find('#section-enrollment-stats')),
            new Tab(
                $content.find('#problems-btn'),
                $content.find('#section-problem')),
            new Tab(
                $content.find('#gradebook-btn'),
                $content.find('#section-gradebook'))
        ];
        tabList.forEach(function (tab) {
            tab.button.click(function () {
                toogleToTab(tab)
            })
        });
        toogleToTab(tabList[0])
    });

}).call(this);