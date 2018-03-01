function SuggestionTab(button, content) {
    'use strict';
    var suggestionTab = new Tab(button, content);

    function updateSuggestion() {
        function onFilterInfoLoad(response) {
            console.log(response);
            const generatedHtml = response.norm.map(renderNormInfo).join('\n');
            const norms = suggestionTab.content.find('#suggestion-norm-content');
            norms[0].innerHTML = generatedHtml;
            norms.find(".filter-form").submit(e => {
                e.preventDefault();
                const form = $(e.target);
                applayFilter(form.serializeArray(), form.data().intent);
            });
        }

        function renderNormInfo(norma) {
            return (
                `<div class="norma-wrapper">
                    <div class="title">${norma.title}</div>
                    <div class="description">${norma.description}</div>
                    <div class="filter-list">
                        ${norma.filters.map(renderFilter(norma.intent)).join('')}
                    </div>
                </div>`
            );
        };

        function renderFilter(intent) {
            return (filter) => {
                return (
                    `<form class="filter-form" data-intent="${intent}" action="">
                        <div class="title">${filter.title}</div>
                        ${filter.items.map(renderFilterItem).join('')}
                        <input type="submit" value="Submit">
                    </form>`
                );
            }
        }

        function renderFilterItem(item) {
            return (
                `<label class="title">
                    ${item.title}
                    <input type="text" name="${item.name}" value="${item.value}">
                </label>`
            );
        };

        function renderResultItem(item) {
            return (`
            <div class = "suggestion-filter-result">
                <div class="title">${item.displayLabel}</div>
                <div class="go_to_problem" data-itemid="${item.elementId}">Go to item</div>
            </div>
            `)
        }

        function onFilterSuccces(data) {
            suggestionTab.content.find('#suggestion-results').append(data.information.map(renderResultItem).join(''));
        }


        function onFilterError() {
            alert("Can not load statistic for select course");
        }

        function applayFilter(formData, intent) {
            $.ajax({
                traditional: true,
                type: 'POST',
                url: 'api/suggestion/',
                success: onFilterSuccces,
                error: onFilterError,
                data: {intent: intent, data: JSON.stringify(formData)},
                dataType: 'json'
            });
        }

        function onFilterInfoLoadError() {
            alert("Can not load statistic for select course");
        }

        $.ajax({
            traditional: true,
            type: 'POST',
            url: 'api/suggestion/',
            success: onFilterInfoLoad,
            error: onFilterInfoLoadError,
            data: {intent: 'get_norm_list'},
            dataType: 'json'
        });
    }

    suggestionTab.loadTabData = updateSuggestion;

    return suggestionTab;
}
