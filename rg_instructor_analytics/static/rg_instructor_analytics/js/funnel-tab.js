function FunnelTab(button, content) {
    'use strict';
    var funnelTab = new Tab(button, content);
    var timeFilter = new TimeFilter(content, updateFunnel);
    var $tabBanner = content.find('.tab-banner');
    var $tabContent = content.find('.tab-content');

    funnelTab.courseStructureView = $tabContent;

    function openLocation() {
        var items = [funnelTab.viewContent.find(
            '*[data-edxid="' + funnelTab.locationToOpen.value + '"]'
        )];
        while (!items.slice(-1)[0].hasClass('funnel-item-0')) {
            items.push(items.slice(-1)[0].parent())
        }
        items.map(function (el) {
            return el.click()}
        );
        funnelTab.locationToOpen = undefined;
    }

    function updateFunnel() {
        function onSuccess(response) {
            funnelTab.courseStructure = response.courses_structure;

            funnelTab.viewContent = funnelTab.courseStructureView.find('.content');
            funnelTab.viewContent.empty();
            funnelTab.viewContent.append(generateFunnel(funnelTab.courseStructure));
            $('.funnel-item-0').on('click', function (e) {
                $(e.target).closest('.funnel-item').toggleClass('active');
            });

            if(funnelTab.locationToOpen) {
                openLocation();
            }
        }

        function generateFunnel(data) {
            return data.map(function (el) {
              return (el.level > 2) ? '' : generateFunnelItem(el, generateFunnel(el.children))
            }).join(' ');
        }

        function generateFunnelItem(item, children) {
            var tpl = _.template(
              '<div class="<%= className %>" data-edxid="<%= itemId %>">' +
                  '<div class="funnel-item-content">' +
                      '<span class="funnel-item-incoming"><%= incoming %></span>' +
                      '<span class="funnel-item-outgoing"><%= outcoming %></span>' +
                      '<span class="funnel-item-name"><%= itemName %></span>' +
                      '<span class="funnel-item-stuck">stuck: <%= stuck %></span>' +
                  '</div>' +
                  '<%= children %>' +
              '</div>'
            );

            return tpl({
              className: 'funnel-item funnel-item-' + item.level,
              itemId: item.id,
              itemName: item.name,
              incoming: item.student_count_in,
              outcoming: item.student_count_out,
              stuck: item.student_count,
              children: children,
            })
        }

        function onError() {
            alert('Can not load statistic for the selected course');
        }

        $.ajax({
            type: 'POST',
            url: 'api/funnel/',
            data: timeFilter.timestampRange,
            dataType: 'json',
            traditional: true,
            success: onSuccess,
            error: onError,
            beforeSend: timeFilter.setLoader,
            complete: timeFilter.removeLoader,
        });
    }

    function loadTabData() {
      try {
        var courseDatesInfo = $('.course-dates-data').data('course-dates')[funnelTab.tabHolder.course];
        var startDate = moment();

        if (courseDatesInfo.course_is_started) {
            $tabBanner.prop('hidden', true);
            $tabContent.prop('hidden', false);

            timeFilter.startDate = moment(courseDatesInfo.course_start * 1000);
            timeFilter.minDate = timeFilter.startDate;
            timeFilter.endDate = moment();
            timeFilter.makeActive(content.find(".js-datepicker-btn"));
            timeFilter.setMinDate();

            updateFunnel();

        } else {
            $tabBanner.prop('hidden', false);
            $tabContent.prop('hidden', true);
        }
      }
      catch (error) {
        console.error(error);
      }

    }

    funnelTab.loadTabData = loadTabData;

    return funnelTab;
}
