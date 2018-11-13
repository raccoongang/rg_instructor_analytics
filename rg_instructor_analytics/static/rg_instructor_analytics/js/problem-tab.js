/**
* Implementation of Tab for the problem tab
* @returns {Tab}
* @class old realisation
*/
function ProblemTab(button, content) {
    var problemTab = new Tab(button, content);
    var problemDetail = problemTab.content.find("#problem-body");
    var timeFilter = new TimeFilter(content, updateHomeWork);
    var $tabBanner = content.find('.tab-banner');
    var $tabContent = content.find('.tab-content');

    function openLocation(){
        problemTab.content.find(`*[data-edxid="${problemTab.locationToOpen.value}"]`).click();
        problemTab.locationToOpen = undefined;
    }

    /**
    * Homework`s stats drawer
    */
    function updateHomeWork() {
        function onSuccess(response) {
            var $homework = $('#problem-homeworks-stats-plot');
            var maxAttempts = Math.max(...response.attempts);
            var countAttempts = [Math.min(...response.attempts), maxAttempts / 2, maxAttempts];
            var correctAnswer = [...response.correct_answer];
            var subsectionId = response.subsection_id;
            var yAxis = [...response.names];
            var xAxisRight = ['0', '50%', '100%'];

            var bars = '',
                index = 0;
            for (let item in yAxis) {
                let attempts = (100 * response.attempts[index]) / maxAttempts;
                let percent = correctAnswer[index] * 100;
                let barHeight = 'auto';

                if (!percent && !attempts) {
                    barHeight = 0;
                }
                
                bars += `
                        <li
                            class="plot-bar-vert"
                            style="width: ${(100 - yAxis.length) / yAxis.length}%; height: ${barHeight}"
                            data-attribute="${index}"
                            data-edxid="${subsectionId[index]}"
                        >
                            <div class="plot-bar-attempts" style="height: ${attempts}%">
                                <span class="plot-bar-value">${response.attempts[index].toFixed(1)}</span>
                            </div>
                            <div class="plot-bar-percent" style="height: ${percent}%">
                                <span class="plot-bar-value">${percent.toFixed(1)}%</span>
                            </div>
                            <div class="plot-click-me">${django.gettext('DETAILS')}</div>
                        </li>
                `
                index++;
            }
            bars = `<ul class="plot-body">${bars}</ul>`;

            // build 'X' axis
            let axis = ``;
            let small;
            if (yAxis.length > 10) {small = 'small'}
            yAxis.forEach((item) => {
                axis += `
                <li 
                    class="hw-xaxis ${small}" 
                    style="min-width: ${(100 - yAxis.length) / yAxis.length}%;"
                    >
                        <div>${item}</div>
                </li>`
            });
            axis = `<ul class="x-axis">${axis}</ul>`;
            bars += axis;

            // build left 'Y' axis
            axis = '';
            countAttempts.forEach((item) => {
                axis += `<li>${item.toFixed(1)}</li>`
            });
            axis = `<ul class="y-axis-l">${axis}</ul>`;
            bars += axis;

            // build right 'Y' axis
            axis = '';
            xAxisRight.forEach((item) => {
                axis += `<li>${item}</li>`
            });
            axis = `<ul class="y-axis-r">${axis}</ul>`;
            bars += axis;

            $homework.html(bars);

            $homework.off('click');
            $homework.on('click', function (e) {
                $('.enrollment-title-1.hidden, .enrollment-title-text-1.hidden,  .enrollment-legend-holder__square-1').removeClass('hidden');
                if ($(e.target).closest('li').data()) {
                    let attr = $(e.target).closest('li').data();
                    loadHomeWorkProblems(response.problems[attr.attribute]);
                }
            });
            if (small) {
                $('.plot-bar-vert').on('mouseover', function (e) {

                    let attr = $(this).data('attribute');

                    $('.hw-xaxis').removeClass('hover');
                    $('.hw-xaxis')[attr].classList.add('hover');
                });
                $('.plot-bar-vert').on('mouseleave', function (e) {
                    $('.hw-xaxis').removeClass('hover');
                });
            }
            if (problemTab.locationToOpen) {
                openLocation();
            }
        }

        function onError() {
            alert("Can't load data for selected course!");
        }

        $.ajax({
            type: "POST",
            url: "api/problem_statics/homework/",
            data: timeFilter.timestampRange,
            dataType: "json",
            traditional: true,
            success: onSuccess,
            error: onError,
            beforeSend: timeFilter.setLoader,
            complete: timeFilter.removeLoader,
        });
    }

    /**
    * `Homework` problem statistics
    * @param hwProblem string id of the problem
    */
    function loadHomeWorkProblems(hwProblem) {
        function onSuccess(response) {
            const correct = response.correct;
            const incorrect = response.incorrect;
            const absIncorrect = incorrect.map(x => Math.abs(x));
            const yAxis = Array.from(new Array(correct.length), (x, i) => i + 1);
            const maxCorrect = Math.max(...correct) || 1;
            const maxIncorrect = Math.max(...absIncorrect) || 1;
            let totalMax = 0;
            maxCorrect>maxIncorrect ? totalMax = maxCorrect : totalMax = maxIncorrect;
            const xAxis = [totalMax, totalMax / 2, 0, totalMax / 2, totalMax];

            let index = 0;
            let bars = '';

            for (let item in yAxis) {
                const correctBar = 100 * correct[index] / totalMax;
                const incorrectBar = Math.abs(100 * incorrect[index] / totalMax);
                let barHeight = 'auto';
                if (!correctBar && !incorrectBar) {
                    barHeight = 0;
                }
                bars += `
                        <li class="plot-bar-vertical"
                            style="width: ${(100 - yAxis.length) / yAxis.length}%; height: ${barHeight}"
                            data-attribute="${index}"
                        >
                            <span>${correct[index]}</span>
                            <div class="correct-bar" style="height:${correctBar/2}%">
                                
                            </div>
                            <span class="second-num">${Math.abs(incorrect[index])}</span>
                            <div class="incorrect-bar" style="height:${incorrectBar/2}%">
                                
                            </div>
                            <div class="plot-click-me">${django.gettext('DETAILS')}</div>
                        </li>
                        `
                index++;
            }
            bars = `<ul class="plot-body">${bars}</ul>`;
            // build y axis
            let axis = '';
            yAxis.forEach(item=>{
                axis += `<li style="width: ${(100 - yAxis.length) / yAxis.length}%">${item}</li>`;
            });
            axis = `<ul class="x-axis">${axis}</ul>`;
            bars += axis;
            // build x axis
            axis = '';
            xAxis.forEach(item=>{
                axis += `<li><div>${item.toFixed(1)}</div></li>`
            });
            axis = `<ul class="y-axis-l">${axis}</ul>`
            bars += axis;
            
            $('#problems-stats-plot').html(bars);

            $('#problems-stats-plot').off('click');
            $('#problems-stats-plot').on('click', function (e) {
                if ($(e.target).closest('li').data()) {
                    let attr = $(e.target).closest('li').data();
                    displayProblemView(hwProblem[attr.attribute]);
                }
            });
        }

        function onError() {
            alert("Can't load data for selected course!");
        }

        $.ajax({
            type: "POST",
            url: "api/problem_statics/homeworksproblems/",
            data: {
                problems: hwProblem,
                from: timeFilter.timestampRange.from,
                to: timeFilter.timestampRange.to,
            },
            dataType: "json",
            traditional: true,
            success: onSuccess,
            error: onError,
            beforeSend: timeFilter.toggleLoader,
            complete: timeFilter.toggleLoader,
        });

    }

    /**
    * function for the render problem body
    * @param stringProblemID string problem id
    */
    function displayProblemView(stringProblemID) {
        function onSuccess(response) {
            problemDetail.html(response.html);
            let problemsWrapper = problemDetail.find(".problems-wrapper");
            let problemBody = problemsWrapper.attr("data-content");
            problemsWrapper.html(problemBody);

            //hide problem debug info
            problemsWrapper.find('.status-icon').hide();
            problemsWrapper.find('.submit').hide();
            problemDetail.find('.instructor-info-action').hide();
            problemDetail.find('.status').remove();

            bindPlotsPopupForProblem(problemsWrapper, stringProblemID)
        }

        function onError() {
            alert("Can't load data for selected course!");
        }

        $.ajax({
            type: "POST",
            url: "api/problem_statics/problem_detail/",
            data: { problem: stringProblemID },
            dataType: "json",
            traditional: true,
            success: onSuccess,
            error: onError,
            beforeSend: timeFilter.setLoader,
            complete: timeFilter.removeLoader,
        });
    }

    function loadTabData() {
      try {
        var courseDatesInfo = $('.course-dates-data').data('course-dates')[problemTab.tabHolder.course];
        if (courseDatesInfo.course_is_started) {
            $tabBanner.prop('hidden', true);
            $tabContent.prop('hidden', false);

            timeFilter.startDate = moment(courseDatesInfo.course_start * 1000);
            timeFilter.minDate = timeFilter.startDate;
            timeFilter.endDate = moment();

            timeFilter.makeActive(content.find(".js-datepicker-btn"));
            timeFilter.setMinDate();

            updateHomeWork();
        } else {
            $tabBanner.prop('hidden', false);
            $tabContent.prop('hidden', true);
        }
      }
      catch (error) {
        console.error(error);
      }

    }

    problemTab.loadTabData = loadTabData;

    problemTab.content
      .find('.close')
      .click(function (item) {
        problemTab.content.find('.modal-for-plot').hide()
    });

    return problemTab;
}

/**
* add buttons for show plot for problem`s question
* @param problem div with problem`s render
* @param stringProblemID string problem id
*/
function bindPlotsPopupForProblem(problem, stringProblemID) {
    var avalivleQuestions = [OpetionQuestion, RadioOptionQuestion, MultyChoseQuestion];
    var questionsDivs = problem.find(".wrapper-problem-response");
    var isAdded;

    questionsDivs.each(function (index) {
        var html = $(questionsDivs[index]);
        isAdded = false;

        for (var i = 0; i < avalivleQuestions.length; i++) {
            var question = avalivleQuestions[i](html, stringProblemID);
            if (question.isCanParse()) {
                question.applyToCurrentProblem(html);
                html.append(`
                <div id="model_plot" class="modal-for-plot">
                    <div>
                        <div id="problem-question-plot"></div>
                    </div>
                </div>`);
                isAdded = true;
                break;
            }
        }
        if (!isAdded) {
            $('<p>We can`t display plot for this question.</p>').appendTo(html);
        }
    });
}

/**
* Base class for questions
* @param questionHtml layout with question
* @param stringProblemID string id of question`s problem
* @class old realisation
* @abstract
*/
function BaseQuestion(questionHtml, stringProblemID) {
    this.questionHtml = questionHtml;
    this.problemID = stringProblemID;

    /**
        * abstract method for indicate, can instance of question correct parse given html
            * @abstract
                */
    this.isCanParse = function () {
        throw new Error("missing implementation")
    };

    /**
    * abstract method, that provide information for question statistics request
    * @return object with the body:
    * return {
    *       type: string // string marker for the given question
    *       questionID: string, // id of the question
    *       answerMap: JSON string // json with relation between the real data and its representation in the database
    *  }
    *
    * @abstract
    */
    this.getRequestMap = function () {
        throw new Error("missing implementation")
    };

    /**
    * function for displaying server's as the bar plot
    * @param data server response. Object with key - name of the position and value - value of the position
    */
    this.displayBar = function (data) {
        const plot_popup = this.questionHtml.parent().find('.modal-for-plot');
        plot_popup.show();

        var x = [];
        var y = [];
        Object.keys(data).forEach(function (key) {
            y.push(key);
            x.push(data[key]);
        });
        let plot = '';
        idx = 0;
        let maxValue = Math.max(...x);

        for (let item in x) {
            let name = y[idx++];
            let value = x[item];
            plot += `
              <li class="plot-row">
                <span class="plot-name">${name}</span>
                <div class="plot-bar-holder">
                   <div class="plot-bar" style="width: ${(value * 100) / maxValue}%"></div>
                </div>
                <span class="plot-value">${value}</span>
              </li>`
        }
        plot = `<ul>${plot}</ul>`;
        this.questionHtml.parent().find('#problem-question-plot').html(plot);
    };

    /**
    * call`s when receive response with statistics for the question
    * @param response
    */
    this.onGettingStat = function (response) {
        switch (response.type) {
            case 'bar':
                this.displayBar(response.stats);
                break;
        }
    };

    this.onGettingStatFail = function () {
        console.log("something bad headings")
    };

    /**
    * apply given instance to some question of the problem
    * @param html layout for inserting the button to display the plot
    */
    this.applyToCurrentProblem = function (html) {
        const $plotBtn = $('<button>Show Plot</button>');
        $plotBtn.appendTo(html);
        $plotBtn.click((item) => {
            var requestMap = this.getRequestMap();
            requestMap.problemID = this.problemID;
            $(item.target).toggleClass('active');
            if ($(item.target).hasClass('active')) {
                $(item.target).html('Hide Plot');
                this.questionHtml.parent().find('.modal-for-plot').removeClass('hidden');
                $.ajax({
                    traditional: true,
                    type: "POST",
                    url: "api/problem_statics/problem_question_stat/",
                    data: requestMap,
                    success: (response) => this.onGettingStat(response),
                    error: () => this.onGettingStatFail(),
                    dataType: "json"
                });
            } else {
                $(item.target).html('Show Plot');
                this.questionHtml.parent().find('.modal-for-plot').addClass('hidden');
            }
        });
    };
}

/**
* Implementation for the drop down question
* @param questionHtml
* @param stringProblemID
* @return {OpetionQuestion}
* @class old realisation
* @extends BaseQuestion
*/
function OpetionQuestion(questionHtml, stringProblemID) {
    const optionQuestion = new BaseQuestion(questionHtml, stringProblemID);
    const question = optionQuestion.questionHtml.find('.option-input');
    optionQuestion.questionHtml = question.length === 1 ? $(question[0]) : null;

    optionQuestion.isCanParse = function () {
        return this.questionHtml !== null
    };

    optionQuestion.getRequestMap = function () {
        const selectRoot = this.questionHtml.find('select');
        const optionsItem = selectRoot.find('option');
        const id2ValueMap = {};
        optionsItem.each(index => {
            let itemID = optionsItem[index].value
            if (!itemID.endsWith('dummy_default')) {
                id2ValueMap[itemID] = optionsItem[index].text
            }
        });
        return {
            type: 'select',
            questionID: selectRoot.attr('name').replace('input_', ''),
            answerMap: JSON.stringify(id2ValueMap)
        }

    };

    return optionQuestion;
}

/**
* Implementation for the single choice question
* @param questionHtml
* @param stringProblemID
* @return {RadioOptionQuestion}
* @class old realisation
* @extends BaseQuestion
*/
function RadioOptionQuestion(questionHtml, stringProblemID) {
    const optionQuestion = new BaseQuestion(questionHtml, stringProblemID);
    const question = optionQuestion.questionHtml.find('.choicegroup');
    optionQuestion.questionHtml = question.length === 1 ? $(question[0]) : null;
    if (optionQuestion.questionHtml) {
        optionQuestion.options = optionQuestion.questionHtml.find('input[type="radio"]');
    }

    optionQuestion.isCanParse = function () {
        return optionQuestion.options && optionQuestion.options.length > 0;
    };

    optionQuestion.getRequestMap = function () {
        const id2ValueMap = {};
        this.options.each(index =>
            id2ValueMap[this.options[index].value] = $(this.options[index].parentNode).text().trim());
        return {
            type: 'select',
            questionID: this.questionHtml.attr('id').replace('inputtype_', ''),
            answerMap: JSON.stringify(id2ValueMap)
        }
    };

    return optionQuestion;
}


/**
* Implementation for the question with checkbox
* @param questionHtml
* @param stringProblemID
* @return {MultyChoseQuestion}
* @class old realisation
* @extends RadioOptionQuestion
*/
function MultyChoseQuestion(questionHtml, stringProblemID) {
    const multyChooseQuestion = new RadioOptionQuestion(questionHtml, stringProblemID);
    if (multyChooseQuestion.questionHtml) {
      multyChooseQuestion.options = multyChooseQuestion.questionHtml.find('input[type="checkbox"]');
    }

    var baseRequestMapFunction = multyChooseQuestion.getRequestMap;
    multyChooseQuestion.getRequestMap = function () {
        var result = baseRequestMapFunction.call(this);
        result.type = 'multySelect';
        return result;
    };

    return multyChooseQuestion;
}

