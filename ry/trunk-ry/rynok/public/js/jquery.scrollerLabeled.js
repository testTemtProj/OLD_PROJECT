jQuery.fn.scrollerLabeled = function(options){
	var options = jQuery.extend({
		LeftMargin: 10,
		RightMargin: 10
	}, options);
	return this.each(function() {
		 //scrollpane parts
		var scrollPane = jQuery(this);
		if (scrollPane.length == 0)
		  return;
		var scrollContent = scrollPane.children('.scroll-content');
		var items = scrollContent.children('li');
		var scrollBar = scrollPane.next('.scroll-bar-container').children('.scroll-bar-wrap').children('.scroll-bar');
		var scrollPaneWidth = scrollPane.width();
		var scrollContentWidth = scrollContent.width();
		var totalItems = items.size();
		var itemWidth = items.eq(0).outerWidth() + options.LeftMargin + options.RightMargin;
		var Group1First = 0;
		var Group2First, Group3First, Group4First, Group5First;
		var _gr1 = items.filter('.group1');
		var group1 = _gr1.length * _gr1.eq(0).outerWidth();
		var _gr2 = items.filter('.group2');
		var group2 = _gr2.length * _gr2.eq(0).outerWidth();
		var _gr3 = items.filter('.group3');
		var group3 = _gr3.length * _gr3.eq(0).outerWidth();
		var _gr4 = items.filter('.group4');
		var group4 = _gr4.length * _gr4.eq(0).outerWidth();
		var _gr5 = items.filter('.group5');
		var group5 = _gr5.length * _gr5.eq(0).outerWidth();
		//fixed items width calculation
		//scrollContentWidth = group1 + group2 + group3 + group4 + group5;
		scrollContentWidth = totalItems * itemWidth;
		scrollContent.width(scrollContentWidth);
		//Calculate proportional position
		var visibleAreaWidth = scrollPane.width() - scrollContentWidth;
		var action = '';
		//build slider
		var scrollbar = scrollBar.slider({
		  min: 0,
		  max: 100,
		  animate: 500,
		  stop: function(e, ui) {
			//if (action == 'stop')
				scrollContent.css('left', Math.round(ui.value / 100 * (visibleAreaWidth)) + 'px');
			//action = 'stop';
		  },
		  start: function(e, ui) {
			//if (action == 'start')
				scrollContent.css('left', Math.round(ui.value / 100 * (visibleAreaWidth)) + 'px');
			//action = 'start';
		  },
		  slide: function(e, ui) {
			//if (action == 'slide')
				scrollContent.css('left', Math.round(ui.value / 100 * (visibleAreaWidth)) + 'px');
			//action = 'slide';
		  }
		});
		//append icon to handle
		var handleHelper = scrollbar.find(".ui-slider-handle")
			  .mousedown(function() {
				scrollbar.width(handleHelper.width());
			  })
			  .mouseup(function() {
				scrollbar.width('100%');
			  })
			  .append('<span class="ui-icon"><span class="ui-cursor">&nbsp;</span></span>')
			  .wrap('<div class="ui-handle-helper-parent"></div>').parent();
		//change overflow to hidden now that slider handles the scrolling
		scrollPane.css('overflow', 'hidden');
		//size scrollbar and handle proportionally to scroll distance
		function sizeScrollbar() {
		  var remainder = scrollContent.width() - scrollPane.width();
		  var proportion = scrollPane.width() / scrollContent.width(); //remainder / scrollContent.width();
		  var handleSize = jQuery('.slider-lb:eq(0)').width(); //scrollPane.width() * proportion; // - (proportion * scrollPane.width());
		  var pos = jQuery(jQuery(jQuery(scrollPane.next('.scroll-bar-container').children(".scroll-bar-start")).prev(".scroll-bar-wrap").children(".scroll-bar").children(".slider-lb1"))).position();
		  scrollbar.find('.ui-slider-handle').css({
			width: handleSize+100,
			left: pos.left-50
		  });
		//  var scrollContentWidth = 1200;
		  handleHelper.width('').width(scrollbar.width() - handleSize - 150);
		  var scrollBarSize = jQuery(".scroll-bar-container").width()-100;
		  var offsetFactor = Math.round(handleSize / 2) + 14; // for left padding scrollbar
		  Group2First = (group1 * scrollBarSize) / (scrollContentWidth)
		  Group3First = ((group1 + group2) * scrollBarSize) / (scrollContentWidth)
		  Group4First = ((group1 + group2 + group3) * scrollBarSize) / (scrollContentWidth)
		  jQuery(".slider-lb2").css('left', (Group2First + offsetFactor + 50) + 'px');
		  jQuery(".slider-lb3").css('left', (Group3First + offsetFactor + 100) + 'px');
		  /*trick to handle overlapping labels*/
		  var group5Offset = (scrollBarSize - jQuery(".slider-lb5").width());
		  var group4Offset = Group4First + offsetFactor;
		  var fwLength = jQuery(".slider-lb4").width();
		  if ((group4Offset + fwLength) > group5Offset) group4Offset -= ((group4Offset + fwLength) - group5Offset) + 35;
		  if (((group4Offset + fwLength) - group5Offset) < 10) group4Offset -= 30;
		  Group4First = group4Offset - offsetFactor;
		  jQuery(".slider-lb4").css('left', group4Offset+150+'px');
		  jQuery(".slider-lb5").css('left', group5Offset+50+'px');
		}
		//reset slider value based on scroll content position
		function resetValue() {
		  var remainder = scrollPane.width() - scrollContentWidth;
		  var leftVal = scrollContent.css('left') == 'auto' ? 0 : parseInt(scrollContent.css('left'));
		  var percentage = Math.round(leftVal / remainder * 100);
		  scrollbar.slider("value", percentage);
		}
		//if the slider is 100% and window gets larger, reveal content
		function reflowContent() {
		  var showing = scrollContent.width() + parseInt(scrollContent.css('left'));
		  var gap = scrollPane.width() - showing;
		  if (gap > 0) {
			scrollContent.css('left', parseInt(scrollContent.css('left')) + gap);
		  }
		}
		var ratio = 0;
		//change handle position on window resize
		jQuery(window)
			  .resize(function() {
				resetValue();
				sizeScrollbar();
				reflowContent();
				ratio = _setRatio();
			  });
		//init scrollbar size
		setTimeout(function() {
		  sizeScrollbar();
		  ratio = _setRatio();
		}, 10); //safari wants a timeout
		function _setRatio() {
		  return handleHelper.width() / parseInt(scrollbar.slider('option', 'max'));
		}
		function moveItemToPos(index, left) {
			var pos = scrollContent.children("li.group"+index).eq(0).position();
			scrollbar.find('.ui-slider-handle').animate({'left': left - 50}, 500);
			if (scrollContent.width()-pos.left < scrollPaneWidth)
				pos.left = scrollContent.width()-scrollPaneWidth;
			scrollContent.animate({ 'left': -pos.left }, 500);
			}
		var _actualIndex = 1;
		jQuery(scrollPane.next('.scroll-bar-container').children(".scroll-bar-start")).bind('click', function() {
			if (_actualIndex > 1) {
				_actualIndex -= 1;
				}
			var pos = jQuery(jQuery(this).prev(".scroll-bar-wrap").children(".scroll-bar").children(".slider-lb" + (_actualIndex))).position();
			moveItemToPos (_actualIndex, pos.left);
		});
		jQuery(scrollPane.next('.scroll-bar-container').children(".scroll-bar-end")).bind('click', function() {
		if (_actualIndex < 5) {
			_actualIndex += 1;
			}
			var pos = jQuery(jQuery(this).prev(".scroll-bar-start").prev(".scroll-bar-wrap").children(".scroll-bar").children(".slider-lb" + (_actualIndex))).position();
			moveItemToPos (_actualIndex, pos.left);
		});
		jQuery(scrollPane.next('.scroll-bar-container').children('.scroll-bar-wrap').children('.scroll-bar').children(".slider-lb1")).bind('click', function() {
		  _actualIndex = 1;
			var pos = jQuery(this).position();
			moveItemToPos (_actualIndex, pos.left);
		});
		jQuery(scrollPane.next('.scroll-bar-container').children('.scroll-bar-wrap').children('.scroll-bar').children(".slider-lb2")).bind('click', function() {
		  _actualIndex = 2;
			var pos = jQuery(this).position();
			moveItemToPos (_actualIndex, pos.left);
		});
		jQuery(scrollPane.next('.scroll-bar-container').children('.scroll-bar-wrap').children('.scroll-bar').children(".slider-lb3")).bind('click', function() {
		  _actualIndex = 3;
			var pos = jQuery(this).position();
			moveItemToPos (_actualIndex, pos.left);
		});
		jQuery(scrollPane.next('.scroll-bar-container').children('.scroll-bar-wrap').children('.scroll-bar').children(".slider-lb4")).bind('click', function() {
		  _actualIndex = 4;
			var pos = jQuery(this).position();
			moveItemToPos (_actualIndex, pos.left);
		});
		jQuery(scrollPane.next('.scroll-bar-container').children('.scroll-bar-wrap').children('.scroll-bar').children(".slider-lb5")).bind('click', function() {
		  _actualIndex = 5;
			var pos = jQuery(this).position();
			moveItemToPos (_actualIndex, pos.left);
		});
	});
};
