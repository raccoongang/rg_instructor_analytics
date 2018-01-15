function FunnelTab(button, content) {
    var funnelTab = new Tab(button, content);

    function updateFunnel() {
        function onSuccess(response) {
            console.log(response)
        }

        function onError() {
            alert("Can not load statistic fo select course");
        }

        $.ajax({
            traditional: true,
            type: "POST",
            url: "api/funnel/",
            success: onSuccess,
            error: onError,
            dataType: "json"
        });

    }

    funnelTab.loadTabData = updateFunnel;

    return funnelTab;
};
