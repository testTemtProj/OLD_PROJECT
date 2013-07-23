$(document).ready(function() {
	$("ul#switch > li > span").click(function(){
		var lang_block_id = $(this).attr("class");
		$("div[id^='fields']").css('display','none');
		$('#'+lang_block_id).css('display', 'block');
	    });
    });