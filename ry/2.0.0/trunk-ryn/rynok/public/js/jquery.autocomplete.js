/*
 * Autocomplete - jQuery plugin 1.0.2
 *
 * Copyright (c) 2007 Dylan Verheul, Dan G. Switzer, Anjesh Tuladhar, JГ¶rn Zaefferer
 *
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
 *
 * Revision: $Id: jquery.autocomplete.js 5747 2008-06-25 18:30:55Z joern.zaefferer $
 *
 */

;(function($) {

    function clearFromTags(str) {
        while (str.indexOf('<b>') > -1)
            str = str.replace('<b>', '').replace('</b>', '');

        while (str.indexOf('<i>') > -1)
            str = str.replace('<i>', '').replace('</i>', '');

        return str;
    }



    $.fn.extend({
        autocomplete: function(urlOrData, options) {
            var isUrl = typeof urlOrData == "string";
            options = $.extend({}, $.Autocompleter.defaults, {
                url: isUrl ? urlOrData : null,
                data: isUrl ? null : urlOrData,
                delay: isUrl ? $.Autocompleter.defaults.delay : 10,
                max: options && !options.scroll ? 10 : 150
            }, options);

            // if highlight is set to false, replace it with a do-nothing function
            options.highlight = options.highlight || function(value) { return value; };

            // if the formatMatch option is not specified, then use formatItem for backwards compatibility
            options.formatMatch = options.formatMatch || options.formatItem;

            options.moreString = options.moreString || "ещё";

            return this.each(function() {
                new $.Autocompleter(this, options);
            });
        },
        result: function(handler) {
            return this.bind("result", handler);
        },
        /*	selectionChanged: function(handler) {
        return this.bind("selectionChanged", handler);
        },*/
        search: function(handler) {
            return this.trigger("search", [handler]);
        },
        flushCache: function() {
            return this.trigger("flushCache");
        },
        setOptions: function(options) {
            return this.trigger("setOptions", [options]);
        },
        unautocomplete: function() {
            return this.trigger("unautocomplete");
        }
    });

    $.Autocompleter = function(input, options) {

        var KEY = {
            UP: 38,
            DOWN: 40,
            RIGHT: 39,
            LEFT: 37,
            DEL: 46,
            TAB: 9,
            RETURN: 13,
            ESC: 27,
            COMMA: 188,
            PAGEUP: 33,
            PAGEDOWN: 34,
            BACKSPACE: 8,
            SPACE: 32
        };

        // Create $ object for input element
        var $input = $(input).attr("autocomplete", "off").addClass(options.inputClass);

        var timeout;
        var previousValue = "";
        var cache = $.Autocompleter.Cache(options);
        var hasFocus = 0;
        var lastKeyPressCode;
        var config = {
            mouseDownOnSelect: false
        };

        fnClearTimeOut = function() { clearTimeout(timeout); }
        var select = $.Autocompleter.Select(options, input, selectCurrent, config, onChange, fnClearTimeOut);

        var blockSubmit;



        // prevent form submit in opera when selecting with return key
        $.browser.opera && $(input.form).bind("submit.autocomplete", function() {
            if (blockSubmit) {
                blockSubmit = false;
                return false;
            }
        });

        // only opera doesn't trigger keydown multiple times while pressed, others don't work with keypress at all
        $input.bind(($.browser.opera ? "keypress" : "keydown") + ".autocomplete", function(event) {
            // track last key pressed
            lastKeyPressCode = event.keyCode;
            switch (event.keyCode) {

                case KEY.UP:
                    event.preventDefault();
                    if (select.visible()) {
                        select.prev();
                        if (!select.selected()) {
                            $input.val(previousValue);
                        }
                    } else {
                        onChange(0, true);
                    }
                    break;

                case KEY.DOWN:
                    event.preventDefault();
                    if (select.visible()) {
                        select.next();
                    } else {
                        onChange(0, true);
                    }
                    break;

                case KEY.RIGHT:
                    if (select.visible() && select.selected()) {
                        event.preventDefault();
                        if (select.listsCount() == 1)
                            spacePressed();
                        else
                            select.right();
                    } else {
                        //onChange(0, true);
                    }
                    break;

                case KEY.LEFT:
                    if (select.visible() && select.selected()) {
                        event.preventDefault();
                        select.left();
                    } else {
                        //onChange(0, true);
                        //alert(select.selected());
                    }
                    break;

                case KEY.PAGEUP:
                    event.preventDefault();
                    if (select.visible()) {
                        select.pageUp();
                    } else {
                        onChange(0, true);
                    }
                    break;

                case KEY.PAGEDOWN:
                    event.preventDefault();
                    if (select.visible()) {
                        select.pageDown();
                    } else {
                        onChange(0, true);
                    }
                    break;

                // matches also semicolon 
                case options.multiple && $.trim(options.multipleSeparator) == "," && KEY.COMMA:
                case KEY.RETURN:
                    if (selectCurrent()) {
                        // stop default to prevent a form submit, Opera needs special handling
                        event.preventDefault();
                        blockSubmit = true;
                        return false;
                    }
                    break;

                case KEY.ESC:
                    $input.val(previousValue);
                    event.preventDefault();
                    select.hide();
                    break;

                case KEY.TAB:
                case KEY.SPACE:
                    if (spacePressed())
                        event.preventDefault();
                    else {
                        clearTimeout(timeout);
                        timeout = setTimeout(onChange, options.delay);
                    }
                    break;

                default:
                    clearTimeout(timeout);
                    timeout = setTimeout(onChange, options.delay);
                    break;
            }
        }).focus(function() {
            // track whether the field has focus, we shouldn't process any
            // results if the field no longer has focus
            hasFocus++;
        }).blur(function() {
            hasFocus = 0;
            if (!config.mouseDownOnSelect) {
                hideResults();
            }
        }).click(function() {
            // show select when clicking in a focused field
            if (hasFocus++ > 1) {
                if (!select.visible()) {
                    onChange(0, true);
                } else {
                    hideResults();
                }
            }
        }).bind("search", function() {
            // TODO why not just specifying both arguments?
            var fn = (arguments.length > 1) ? arguments[1] : null;
            function findValueCallback(q, data) {
                var result;
                if (data && data.length) {
                    for (var i = 0; i < data.length; i++) {
                        if (data[i].result.toLowerCase() == q.toLowerCase()) {
                            result = data[i];
                            break;
                        }
                    }
                }
                if (typeof fn == "function") fn(result);
                else $input.trigger("result", result && [result.data, result.value]);
            }
            $.each(trimWords($input.val()), function(i, value) {
                request(value, findValueCallback, findValueCallback);
            });
        }).bind("flushCache", function() {
            cache.flush();
        }).bind("setOptions", function() {
            $.extend(options, arguments[1]);
            // if we've updated the data, repopulate
            if ("data" in arguments[1])
                cache.populate();
        }).bind("unautocomplete", function() {
            select.unbind();
            $input.unbind();
            $(input.form).unbind(".autocomplete");
        });


        function spacePressed() {
            if (select.visible() && select.selected() && options.spaceToContinue) {
                var selected = select.selected();
                var v = selected.value;
                //var items = select.items();
                // Если последний результат, то срабатываем как ENTER
                if (selected.data.childCount == 0) {
                    hideResultsNow();
                    $input.trigger("result", [v, v]);
                } else {
                    /*!$input.trigger("selectionChanged", [v+' ', true]);!*/
                    $input.val(clearFromTags(v) + ' ');
                    onChange(0, true);
                }

                return true;
            }
            else
                return false;

        }

        function selectCurrent() {
            var selected = select.selected();
            if (!selected)
                return false;

            var v = clearFromTags(selected.result);
            previousValue = v;

            if (options.multiple) {
                var words = trimWords($input.val());
                if (words.length > 1) {
                    v = words.slice(0, words.length - 1).join(options.multipleSeparator) + options.multipleSeparator + v;
                }
                v += options.multipleSeparator;
            }

            $input.val(v);
            hideResultsNow();
            $input.trigger("result", [selected.data, selected.value]);
            return true;
        }

        function onChange(crap, skipPrevCheck) {

            if ((lastKeyPressCode == KEY.DEL) && !$.browser.opera) {
                select.hide();
                return;
            }

            var currentValue = $input.val();

            /*if (  !skipPrevCheck &&  currentValue == previousValue ) {
            return;
            }
            */
            previousValue = currentValue;

            //currentValue = lastWord(currentValue);
            if (currentValue.length >= options.minChars) {
                $input.addClass(options.loadingClass);
                if (!options.matchCase)
                    currentValue = currentValue.toLowerCase();
                request(currentValue, receiveData, hideResultsNow);
            } else {
                stopLoading();
                select.hide();
            }
        };

        function trimWords(value) {
            if (!value) {
                return [""];
            }
            var words = value.split(options.multipleSeparator);
            var result = [];
            $.each(words, function(i, value) {
                if ($.trim(value))
                    result[i] = $.trim(value);
            });
            return result;
        }

        function lastWord(value) {
            if (!options.multiple)
                return value;
            var words = trimWords(value);
            return words[words.length - 1];
        }

        // fills in the input box w/the first match (assumed to be the best match)
        // q: the term entered
        // sValue: the first matching result
        function autoFill(q, sValue) {
            // autofill in the complete box w/the first match as long as the user hasn't entered in more data
            // if the last user key pressed was backspace, don't autofill

            if ((lastKeyPressCode == KEY.SPACE) || (lastKeyPressCode == KEY.RIGHT)) {
                var v = previousValue;
                var items = select.items();
                /*			var s = select.selected();
                // Если последний результат, то срабатываем как ENTER
                alert(s);
                if (s.data.childCount == 0 ) {
                hideResultsNow();
                $input.trigger("result", [v, v]);
                return true;
                }*/
            }

            if (options.autoFill && (lastWord($input.val()).toLowerCase() == q.toLowerCase()) && lastKeyPressCode != KEY.BACKSPACE) {
                // fill in the value (keep the case the user has typed)
                $input.val($input.val() + sValue.substring(lastWord(previousValue).length));
                // select the portion of the value not typed by the user (so the next character will erase)
                $.Autocompleter.Selection(input, previousValue.length, previousValue.length + sValue.length);
            }

            return false;
        };

        function hideResults() {
            clearTimeout(timeout);
            timeout = setTimeout(hideResultsNow, 200);
        };

        function hideResultsNow() {
            var wasVisible = select.visible();
            select.hide();
            clearTimeout(timeout);
            stopLoading();
            if (options.mustMatch) {
                // call search and run callback
                $input.search(
				function(result) {
				    // if no value found, clear the input box
				    if (!result) {
				        if (options.multiple) {
				            var words = trimWords($input.val()).slice(0, -1);
				            $input.val(words.join(options.multipleSeparator) + (words.length ? options.multipleSeparator : ""));
				        }
				        else
				            $input.val("");
				    }
				}
			);
            }
            /*		if (wasVisible)
            // position cursor at end of input field
            $.Autocompleter.Selection(input, input.value.length, input.value.length);
            */
        };

        function receiveData(q, data) {
            if (data && data.length /*&& hasFocus */) {
                stopLoading();
                select.display(data, q);
                if (!autoFill(q, data[0].value)) {
                    if ($input.val() != '')
                        select.show();
                }
            } else {
                hideResultsNow();
                //opera.postError('receiveData error!');
                //alert('a');
            }
        };

        function request(term, success, failure) {
            //opera.postError('request ' + term);
            if (!options.matchCase)
                term = term.toLowerCase();
            var data = cache.load(term);
            // recieve the cached data
            if (data && data.length) {
                success(term, data);
                // if an AJAX url has been supplied, try loading the data now
            } else if ((typeof options.url == "string") && (options.url.length > 0)) {

                var extraParams = {
                    timestamp: +new Date()
                };
                $.each(options.extraParams, function(key, param) {
                    extraParams[key] = typeof param == "function" ? param() : param;
                });

                //opera.postError('Sending ajax request: ' + lastWord(term));
                $.ajax({
                    // try to leverage ajaxQueue plugin to abort previous requests
                    /*mode: "abort",*/
                    mode: "abort",
                    // limit abortion to this input
                    port: "autocomplete" + input.name,
                    dataType: 'text', //options.dataType,
                    url: options.url,
                    data: $.extend({
                        q: lastWord(term),
                        limit: options.max
                    }, extraParams),
                    success: function(data) {
                        //opera.postError('First ajax response');
                        //opera.postError('begin to parse ');
                        var parsed = options.parse && options.parse(data) /*|| parse(data)*/;
                        //opera.postError('parsed ok');
                        cache.add(term, parsed);
                        /*var endtime = new Date();
                        var t = endtime - extraParams.timestamp; 
                        alert('response recieved in ' + t + ' ms ');*/
                        success(term, parsed);
                    }
                });
            } else {
                // if we have a failure, we need to empty the list -- this prevents the the [TAB] key from selecting the last successful match
                select.emptyList();
                failure(term);
            }
        };

        function parse(data) {
            var parsed = [];
            var rows = data.split("\n");
            for (var i = 0; i < rows.length; i++) {
                var row = $.trim(rows[i]);
                if (row) {
                    row = row.split("|");
                    parsed[parsed.length] = {
                        data: row,
                        value: row[0],
                        result: options.formatResult && options.formatResult(row, row[0]) || row[0]
                    };
                }
            }
            return parsed;
        };

        function stopLoading() {
            $input.removeClass(options.loadingClass);
        };

    };

    $.Autocompleter.defaults = {
        inputClass: "ac_input",
        resultsClass: "ac_results",
        loadingClass: "ac_loading",
        minChars: 1,
        delay: 150,
        matchCase: false,
        matchSubset: false,
        matchContains: false,
        cacheLength: 10,
        max: 100,
        mustMatch: false,
        extraParams: {},
        selectFirst: true,
        formatItem: function(row) { return row[0]; },
        formatMatch: null,
        autoFill: false,
        width: 0,
        multiple: false,
        multipleSeparator: ", ",
        highlight: function(value, term, data) {

            if (data.charsEntered > 0) {
                // Подсветка подсказок по WEB
                var completeWordsIndex = value.substr(0, data.charsEntered + 1).lastIndexOf(' ');
                var completeWords = value.substr(0, completeWordsIndex);
                var currentTyping = value.substring(completeWordsIndex, data.charsEntered);

                return '<span class="WordComplete">' +
					completeWords +
					'</span>' +
					currentTyping +
                //value.substr(0, data.charsEntered) + 
					"<span class=\"strong\">" +
					value.substring(data.charsEntered) +
					"</span>";
            } else {
                // Подсветка подсказок новостей
                while (value.indexOf('<b>') > -1)
                    value = value.replace('<b>', '<span class="newsSuggestComplete">').replace('</b>', '</span>');
                while (value.indexOf('<i>') > -1)
                    value = value.replace('<i>', '<span class="newsSuggestComplete">').replace('</i>', '</span>');
                value = '<span class="newsSuggest">' + value + '</span>';
                return value;
            }

            /*return  value.replace(new RegExp("^(?![^&;]+;)(?!<[^<>]*)(" + term.replace(/([\^\$\(\)\[\]\{\}\*\.\+\?\|\\])/gi, "\\$1") + ")(?![^<>]*>)(?![^&;]+;)", "gi"), "$1<span class=\"strong\">") + "</span>";*/
        },
        scroll: false,
        scrollHeight: 180
    };

    $.Autocompleter.Cache = function(options) {

        var data = {};
        var length = 0;

        function matchSubset(s, sub) {
            if (!options.matchCase)
                s = s.toLowerCase();
            var i = s.indexOf(sub);
            if (i == -1) return false;
            return i == 0 || options.matchContains;
        };

        function add(q, value) {
            if (length > options.cacheLength) {
                flush();
            }
            if (!data[q]) {
                length++;
            }
            data[q] = value;
        }

        function populate() {
            if (!options.data) return false;
            // track the matches
            var stMatchSets = {},
			nullData = 0;

            // no url was specified, we need to adjust the cache length to make sure it fits the local data store
            if (!options.url) options.cacheLength = 1;

            // track all options for minChars = 0
            stMatchSets[""] = [];

            // loop through the array and create a lookup structure
            for (var i = 0, ol = options.data.length; i < ol; i++) {
                var rawValue = options.data[i];
                // if rawValue is a string, make an array otherwise just reference the array
                rawValue = (typeof rawValue == "string") ? [rawValue] : rawValue;

                var value = options.formatMatch(rawValue, i + 1, options.data.length);
                if (value === false)
                    continue;

                var firstChar = value.charAt(0).toLowerCase();
                // if no lookup array for this character exists, look it up now
                if (!stMatchSets[firstChar])
                    stMatchSets[firstChar] = [];

                // if the match is a string
                var row = {
                    value: value,
                    data: rawValue,
                    result: options.formatResult && options.formatResult(rawValue) || value
                };

                // push the current match into the set list
                stMatchSets[firstChar].push(row);

                // keep track of minChars zero items
                if (nullData++ < options.max) {
                    stMatchSets[""].push(row);
                }
            };

            // add the data items to the cache
            $.each(stMatchSets, function(i, value) {
                // increase the cache size
                options.cacheLength++;
                // add to the cache
                add(i, value);
            });
        }

        // populate any existing data
        setTimeout(populate, 25);

        function flush() {
            data = {};
            length = 0;
        }

        return {
            flush: flush,
            add: add,
            populate: populate,
            load: function(q) {
                if (!options.cacheLength || !length)
                    return null;
                /* 
                * if dealing w/local data and matchContains than we must make sure
                * to loop through all the data collections looking for matches
                */
                if (!options.url && options.matchContains) {
                    // track all matches
                    var csub = [];
                    // loop through all the data grids for matches
                    for (var k in data) {
                        // don't search through the stMatchSets[""] (minChars: 0) cache
                        // this prevents duplicates
                        if (k.length > 0) {
                            var c = data[k];
                            $.each(c, function(i, x) {
                                // if we've got a match, add it to the array
                                if (matchSubset(x.value, q)) {
                                    csub.push(x);
                                }
                            });
                        }
                    }
                    return csub;
                } else
                // if the exact item exists, use it
                    if (data[q]) {
                    return data[q];
                } else
                    if (options.matchSubset) {
                    for (var i = q.length - 1; i >= options.minChars; i--) {
                        var c = data[q.substr(0, i)];
                        if (c) {
                            var csub = [];
                            $.each(c, function(i, x) {
                                if (matchSubset(x.value, q)) {
                                    csub[csub.length] = x;
                                }
                            });
                            return csub;
                        }
                    }
                }
                return null;
            }
        };
    };

    $.Autocompleter.Select = function(options, input, select, config, onChange, clearTimeout) {
        var CLASSES = {
            ACTIVE: "ac_over"
        };

        var listItems,
		active = -1,
		activeList = -1,
		data,
		term = "",
		needsInit = true,
		element,
		pp,
		parentDiv,
		navElement,
		navLeft,
		navRight,
		list,
		lists = [];

        // Create results
        function init() {
            if (!needsInit)
                return;

            //setTimeout(updateNavigation, 25);

            $t = $(options.appendTo);

            pp = $("<div/>")
            //.css("border", "1px solid green")
			.css("position", "absolute")
			.addClass("topContainer")
			.appendTo(options.appendTo);

            parentDiv = $("<div/>")
            //.appendTo(options.appendTo)
		 .appendTo(pp)
		 .addClass("container");
            //.css("position", "absolute")
            //.css("width", options.width);


            element = $("<table/>")
		.hide()
            //.css("width", "100%")
            //.css("position", "absolute")
            //.appendTo(options.appendTo)
		.appendTo(parentDiv)
		.addClass(options.resultsClass);
            //.css("width", options.width);


            navElement = $("<div />")
			.addClass("navContainer")
			.appendTo(pp)
			.click(function() {
			    clearTimeout();
			    input.focus();
			});

            navLeft = $('<a href="#"> <b> << </b> · · · </a>')
			.addClass("yottosOrange")
			.click(function(event) {
			    clearTimeout();
			    event.stopPropagation();
			    scrollColumnLeft();
			    input.focus();
			}).appendTo(navElement);


            $("<span>")
			.css("width", "100%")
			.html("•")
            //.html("ещё")
            //.css("font-size", "0.8em")
			.css("color", "#777")
			.appendTo(navElement);

            navRight = $('<a href="#"> · · · <b> >> </b> </a>')
			.addClass("yottosBlue")
			.click(function(event) {
			    clearTimeout();
			    event.stopPropagation();
			    scrollColumnRight();
			    input.focus();
			}).appendTo(navElement);



            /*navLeft = $("<span>").html('<a href="#"> <- ещё </a>')
            .css("text-align", "left")
            .css("left", "4px")		
            .css("bottom", "4")
            //	.css("position", "absolute")
            .appendTo(navEl);

			
		navRight = $("<span>").html('<a href="#">ещё -> </a>')
            .css("margin-left", parentDiv.width() - 150)		
            .css("bottom", "4")
            .css("width", "500px")
            //.css("position", "absolute")
            .css("border", "1px solid red")
            .appendTo(navEl);
            */



            //		.appendTo(parentDiv);
			
            function onWindowResize() {
				/*
				 * Отрисовка подсказок
				 * todo: сделать нормально определения размера и положения инпута 
				 */
                pp.css("left", $t.position().left)
			  .css("top", $t.position().top + $t.height()+26)
                var w = $(input).width()+5;
                pp.width(w);
                parentDiv.width(w);
                element.width(w);
                options.maxColumnWidth = w;
				temp_obj = $t; 
//				alert(temp_obj.position());
							
            }

            var resizeTimer = null;
            $(window).bind('resize', function() {
                if (resizeTimer) clearTimeout(resizeTimer);
                resizeTimer = setTimeout(onWindowResize, 100);
            });


            onWindowResize();
            mainRow = $("<tr/>").appendTo(element);
            needsInit = false;
        }


        // Прокручивает на одну колонку вправо
        function scrollColumnRight() {
            var offset = 0;
            var scroll = parentDiv.scrollLeft();
            var x = 0;

            for (i = 0; i < lists.length; i++) {
                offset += lists[i].width() + 2;
                if (offset > (scroll + parentDiv.width())) {
                    x = offset;
                    break;
                }
            }

            if (!x)
                return;

            parentDiv.scrollLeft(x);
            updateNavigation();
        }


        // Прокрутка на одну колонку влево
        function scrollColumnLeft() {
            var offset = 0,
			scroll = parentDiv.scrollLeft(),
			x = 0;

            for (i = 0; i < lists.length; i++) {
                x = offset;
                offset += lists[i].width() + 2;
                if (offset >= scroll)
                    break;
            }

            parentDiv.scrollLeft(x);
            updateNavigation();
        }


        function createColumn(header, colNumber) {
            currentCell = $("<td/>").appendTo(mainRow).addClass("column");
            $("<h3/>").html(header).appendTo(currentCell);

            list = $("<ul/>").appendTo(currentCell).mouseover(function(event) {
                if (target(event).nodeName && target(event).nodeName.toUpperCase() == 'LI') {
                    active = $("li").removeClass(CLASSES.ACTIVE).index(target(event));
                    activeList = colNumber;
                    $(target(event)).addClass(CLASSES.ACTIVE);
                    list = lists[activeList];
                    listItems = list.find("li");
                }
            }).click(function(event) {

                active = $("li").index(target(event));
                list = lists[colNumber];
                listItems = list.find("li");

                $(target(event)).addClass(CLASSES.ACTIVE);
                select();
                //throw('active: ' + active);
                // TODO provide option to avoid setting focus again after selection? useful for cleanup-on-focus
                input.focus();
                return false;
            }).mousedown(function() {
                config.mouseDownOnSelect = true;
            }).mouseup(function() {
                config.mouseDownOnSelect = false;
            });

            lists[colNumber] = list;
            if (colNumber % 2 == 0) list.addClass("col_odd");
            else list.addClass("col_even");
        }

        function target(event) {
            var element = event.target;
            while (element && element.tagName != "LI")
                element = element.parentNode;
            // more fun with IE, sometimes event.target is empty, just ignore it then
            if (!element)
                return [];
            return element;
        }


        function updateNavigation() {
            var scroll = parentDiv.scrollLeft();
            var visible = false;

            if (scroll > 0) {
                //navLeft.show();
                navLeft.removeClass("inactive");
                navLeft.addClass("yottosOrange");
                visible = true;
                //alert(scroll);
            }
            else {
                navLeft.removeClass("yottosOrange");
                navLeft.addClass("inactive");
            }

            if ((scroll + parentDiv.width()) >= element.width() - 20) {
                navRight.removeClass("yottosBlue");
                navRight.addClass("inactive");
            }
            else {
                navRight.removeClass("inactive");
                navRight.addClass("yottosBlue");
                visible = true;
            }

            if (visible && !options.suppressHorizontalScroll)
                navElement.show();
            else
                navElement.hide();

        }

        function moveSelect(step) {
            listItems.removeClass(CLASSES.ACTIVE);
            movePosition(step);

            var activeItem = listItems.slice(active, active + 1).addClass(CLASSES.ACTIVE);

            // Посылаем сигнал об изменении выделения
            if (active >= 0) {
                //var v = activeItem.text();
                v = $.data(activeItem[0], "ac_data").value;
                //$input.val(v);
                //hideResultsNow();
                //if (active >= 0)
                /*!$(input).trigger("selectionChanged", [v, false]);!*/
                $(input).val(clearFromTags(v));

            }


            // ...

            if (options.scroll) {
                var offset = 0;
                listItems.slice(0, active).each(function() {
                    offset += this.offsetHeight;
                });
                if ((offset + activeItem[0].offsetHeight - list.scrollTop()) > list[0].clientHeight) {
                    list.scrollTop(offset + activeItem[0].offsetHeight - list.innerHeight());
                } else if (offset < list.scrollTop()) {
                    list.scrollTop(offset);
                }
            }

            ensureCursorVisible();
            // ----------------------------
        };

        function movePosition(step) {
            active += step;
            if (active < 0) {
                active = -1;
            } else if (active >= listItems.size()) {
                active = listItems.size() - 1;
            }
        }

        function limitNumberOfItems(available) {
            return options.max && options.max < available
			? options.max
			: available;
        }



        // Возвращает смещение колонки с индексом col
        function columnOffset(col) {
            var offset = 0;
            for (i = 0; i < col; i++)
                offset += lists[i].width() + 2; 						/* 2 = расстояние между ячейками таблицы */

            return offset;
        }


        // Проверяет, что выделение видимо (при необходимости прокручивает список)
        function ensureCursorVisible() {

            var offset = columnOffset(activeList);
            var scroll = parentDiv.scrollLeft();
            var window = parentDiv.width();
            var w = lists[activeList].width();
            var direction = 0;
            var x = 0;

            if ((offset + w) > (scroll + window)) {
                direction = 1;
                x = offset + w - window;
            }
            else if (offset < scroll) {
                direction = -1;
                x = offset;
            }
            else
                return;

            parentDiv.scrollLeft(x);
            updateNavigation();


        }


        // Сдвигает выделение влево или вправо на step шагов
        function moveColumn(step) {
            var a = activeList + step;
            if ((a >= lists.length) || (a < 0))
                return;
            listItems.removeClass(CLASSES.ACTIVE);
            activeList = a;
            list = lists[a];
            listItems = list.find("li");
            moveSelect(0);
        }

        function fillList() {
            lists = [];
            mainRow.empty();
            currentTheme = '';
            var max = limitNumberOfItems(data.length);
            var col = 0;
            for (var i = 0; i < max; i++) {
                if (!data[i])
                    continue;
                if (data[i].data.theme != currentTheme) {
                    currentTheme = data[i].data.theme;
                    createColumn(data[i].data.theme, col);
                    col++;
                    //				currentRow = $("<td/>").appendTo(mainRow);
                    //			list = $("<ul/>").appendTo(currentRow);
                }
                var formatted = options.formatItem(data[i].data, i + 1, max, data[i].value, term);
                //formatted = data[i].data.to;
                if (formatted === false)
                    continue;

                var li = $("<li/>").html(options.highlight(formatted, term, data[i].data)).addClass(i % 2 == 0 ? "ac_even" : "ac_odd").appendTo(list)[0];


                //  Дата новости
                if (data[i].data.dt != undefined) {
                    $('<span>').html(data[i].data.dt).addClass("newsDate").appendTo(li);
                }


                if (data[i].data.childCount >= 1) {
                    $('<a>').attr("href", "javascript:void(0)").html(options.moreString + ' >>').addClass("more").appendTo(li)
						.click(function(event) {
						    event.stopPropagation();
						    var activeItem = target(event);
						    var v = $.data(activeItem, "ac_data").value;
						    /*!$(input).trigger("selectionChanged", [v, false]);!*/
						    $(input).val(v + ' ');
						    $(input).focus();
						    onChange(0, true);
						});
                }

                $.data(li, "ac_data", data[i]);
            }
            list = lists[0];
            listItems = lists[0].find("li");
            activeList = 0;
            parentDiv.scrollLeft(0);
            if (options.selectFirst) {
                listItems.slice(0, 1).addClass(CLASSES.ACTIVE);
                active = 0;
                //			activeList = 0;
            } else {
                active = -1;
            }


            // apply bgiframe if available
            if ($.fn.bgiframe)
                list.bgiframe();

            // РЎС‡РёС‚Р°РµРј С€РёСЂРёРЅСѓ РїРѕРґСЃРєР°Р·РєРё. Р•СЃР»Рё С‚РµРјР°С‚РёРє РјР°Р»Рѕ, С‚Рѕ СЃСѓР¶Р°РµРј (РґР»СЏ РїСѓС‰РµР№ РєСЂР°СЃРѕС‚С‹)
            if (options.maxColumnWidth > 0) {
                var width = 0;
                $.each(lists, function() {
                    width += options.maxColumnWidth;
                });
                if (width <= parentDiv.width()) {
                    $("<td/>").width(parentDiv.width() - width).appendTo(mainRow);
                }
            }

            setTimeout(updateNavigation);
        }

        return {
            display: function(d, q) {
                init();
                data = d;
                term = q;
                fillList();
            },
            next: function() {
                moveSelect(1);
            },
            prev: function() {
                moveSelect(-1);
            },
            right: function() {
                moveColumn(1);
            },
            left: function() {
                moveColumn(-1);
            },

            pageUp: function() {
                if (active != 0 && active - 8 < 0) {
                    moveSelect(-active);
                } else {
                    moveSelect(-8);
                }
            },
            pageDown: function() {
                if (active != listItems.size() - 1 && active + 8 > listItems.size()) {
                    moveSelect(listItems.size() - 1 - active);
                } else {
                    moveSelect(8);
                }
            },
            hide: function() {
                pp && pp.hide();
                parentDiv && parentDiv.hide();
                element && element.hide();
                listItems && listItems.removeClass(CLASSES.ACTIVE);
                active = -1;
            },
            visible: function() {
                return element && element.is(":visible");
            },
            current: function() {
                return this.visible() && (listItems.filter("." + CLASSES.ACTIVE)[0] || options.selectFirst && listItems[0]);
            },
            show: function() {
                var offset = $(input).offset();
                pp.show();
                parentDiv.show();
                element.css({
                    width: typeof options.width == "string" || options.width > 0 ? options.width : $(input).width(),
                    top: offset.top + input.offsetHeight,
                    left: offset.left
                }).show();
                if (options.scroll) {
                    list.scrollTop(0);
                    list.css({
                        maxHeight: options.scrollHeight,
                        overflow: 'auto'
                    });

                    if ($.browser.msie && typeof document.body.style.maxHeight === "undefined") {
                        var listHeight = 0;
                        listItems.each(function() {
                            listHeight += this.offsetHeight;
                        });
                        var scrollbarsVisible = listHeight > options.scrollHeight;
                        list.css('height', scrollbarsVisible ? options.scrollHeight : listHeight);
                        if (!scrollbarsVisible) {
                            // IE doesn't recalculate width when scrollbar disappears
                            listItems.width(list.width() - parseInt(listItems.css("padding-left")) - parseInt(listItems.css("padding-right")));
                        }
                    }

                }
            },
            selected: function() {
                if ((active == -1) || (activeList == -1))
                    return false;

                var selected = listItems && listItems.filter("." + CLASSES.ACTIVE)/*.removeClass(CLASSES.ACTIVE) */;
                return selected && selected.length && $.data(selected[0], "ac_data");
            },
            emptyList: function() {
                list && list.empty();
            },
            listsCount: function() {
                return lists.length;
            },
            items: function() {
                return listItems;
            },
            unbind: function() {
                list && list.empty();
                //element && element.remove();		/* !!! */
                parentDiv.remove();
            }
        };
    };

    $.Autocompleter.Selection = function(field, start, end) {
        if (field.createTextRange) {
            var selRange = field.createTextRange();
            selRange.collapse(true);
            selRange.moveStart("character", start);
            selRange.moveEnd("character", end);
            selRange.select();
        } else if (field.setSelectionRange) {
            field.setSelectionRange(start, end);
        } else {
            if (field.selectionStart) {
                field.selectionStart = start;
                field.selectionEnd = end;
            }
        }
        field.focus();
    };

})(jQuery);