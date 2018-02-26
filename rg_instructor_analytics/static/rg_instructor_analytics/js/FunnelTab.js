function FunnelTab(button, content) {
    'use strict';
    var funnelTab = new Tab(button, content);
    funnelTab.courseStructureView = content.find('#course-structure');

    function updateFunnel() {
        function onSuccess(response) {
            console.log(response);
            funnelTab.courseStructure = response.courses_structure;

            const viewContent = funnelTab.courseStructureView.find('.content');
            viewContent.empty();
            viewContent.append(generateFunnel(funnelTab.courseStructure));
        }

        function generateFunnel(data) {
            return data.map(el => el.level > 2 ? '' : `${generateFunnelItem(el,generateFunnel(el.children))}`).join(' ');
        }

        function generateFunnelItem(item, children) {
            const name = item.name;
            const incoming = item.incoming;
            const stuck = item.stuck;
            const out = item.out;
            const className = `funnel-item-${item.level}`;
            return `<div class="${className}">
                       incoming::${incoming}  stuck::${stuck}  out::${out}   type::${className} name::${name}  
                       ${children}
                    </div>`
        }

        function onError() {
            alert('Can not load statistic for the selected course');
        }

        $.ajax({
            traditional: true,
            type: 'POST',
            url: 'api/funnel/',
            success: onSuccess,
            error: onError,
            dataType: 'json'
        });
    }

    funnelTab.loadTabData = updateFunnel;

    return funnelTab;
}
