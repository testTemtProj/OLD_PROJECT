function sortByPrice(obj){
    return false;
}
jQuery.fn.onImagesLoaded = function(_cb){
    return this.each(function(){

        var $imgs = (this.tagName.toLowerCase() === 'img') ? $(this) : $('img', this), _cont = this, i = 0, _done = function(){
            if (typeof _cb === 'function') 
        _cb(_cont);
        };

        if ($imgs.length) {
            $imgs.each(function(){
                var _img = this, _checki = function(e){
                    if ((_img.complete) || (_img.readyState == 'complete' && e.type == 'readystatechange')) {
                        if (++i === $imgs.length) 
                _done();
                    }
                    else 
                if (_img.readyState === undefined) {
                    $(_img).attr('src', $(_img).attr('src')); // re-fire load event
                }
                }; // _checki \\
                $(_img).bind('load readystatechange', function(e){
                    _checki(e);
                });
                _checki({
                    type: 'readystatechange'
                }); // bind to 'load' event...
            });
        }
        else 
            _done();
    });
};

function minimizeDescription() {
    var term = $('#htxtFind').val();
    var pattern = new RegExp('('+term+')', 'gi');

    $('.description').each(function(){
        var description = $(this).html().trim().replace(/[\r|\n]/gi,' ').replace(/,$/gi,'');
        var searchPos = description.search(term);
        var cssClass = '';
        //        if (term) {
        //            var terms = term.split(' ');
        //            for(var termCounter=0;termCounter<terms.length;termCounter++) {
        //                var term = terms[termCounter];
        //
        //            }
        //        }
        if (term) {
            description = description.replace(pattern, "<b class=highlight>$1</b>");
        }

        if(term && searchPos>=200)
        cssClass = ' active';
    if(description.length > 200) {
        description = description.replace(/([^<]{160})(.*)/gi,
            "$1<a href='javascript:void(0);' class='show-more"+cssClass+"'><span class=dots>...</span> <span class=show>подробнее</span><span class=text>$2</span><span class=hide>скрыть</span></a>");
    }


    $(this).html(description);
    });
}

function scaleSize(maxW, maxH, currW, currH){
    var ratio = currH / currW;

    if(currW >= maxW && ratio <= 1){
        currW = maxW;
        currH = currW * ratio;
    } else if(currH >= maxH){
        currH = maxH;
        currW = currH / ratio;
    }

    return [currW, currH];
}

var imageCounter = 0;
var lightboxProperties = {
    imageLoading: '/js/jquery-lightbox/images/loading.gif',
    imageBtnClose: '/js/jquery-lightbox/images/close.gif'
}
var no_photo = [];
function refreshImage($image, $link, link, width) {    
    $($link).removeClass('lightbox');
    if (link) {
        if($link.parents('ul').hasClass('scroll-content')==false) {
            $link.attr('href', link);
            $link.addClass('lightbox');
            $link.lightBox(lightboxProperties);
        } else {

        }
    } else {
        no_photo.push($image.attr('id'));                       
        $image.attr('src', '/img/no-photo.png');
        //$image.
        $($link).removeClass('lightbox');

        $link.unbind('click');
        $link.removeAttr('href');
        if($link.parents('ul').hasClass('scroll-content')==true) {
            var $li = $link.parents('li');
            $li.hide();
        }
        $($image).parent().removeClass('lightbox');     
    }

    $image.removeAttr('new');

    if(typeof(width)!='undefined') {
        $image.attr('width', 100);
    }

    updateImages(++imageCounter);
}

function initScrolls() {
    //renderCompareList();
    //updateCompareList();
    ScrollLabelResize();
    /*
       $('img[src="/img/no-photo.png"]').each(function(){
       var $image = $(this);
       refreshImage($image, $image.parent(), false);
       })
       */
}

function updateImages(counter) {       
    if (typeof(counter) == 'undefined') {
        counter = 0; 
    }
    var $this = $('.image-file:eq('+counter+')');

            if($this.length == 0) {
                if($('[new=true]').length == 0) {
                    setTimeout(initScrolls, 500);
                }

                return false;
            }

            var id = $this.attr('id').replace('item-', '');
            var $link = $this.parent();
            var links = $('#item-thumb-' + id).html().trim().split('\n');
            var linksOrig = $('#item-orig-' + id).html().trim().split('\n');
            if(links.length > 0 && links[0]) {
                $this.attr('src', links[0]).load(function() {
                    refreshImage($this, $link, linksOrig[0]);
                }).error(function(){
                    try {
                        $this.attr('src', links[1]).load(function(){
                            refreshImage($this, $link, linksOrig[1], 100);
                        }).error(function(){
                            refreshImage($this, $link, false, 0);
                        })
                    } catch(e) {
                        refreshImage($this, $link, false, 0);
                    }
                });
            } else {
                refreshImage($this, $link, false);
            }
            if(no_photo.length>0){
                for (var x in no_photo) {
                    var tmp_parent = $('#' + no_photo[x]).parent();
                    tmp_parent.removeClass('lightbox');
                    tmp_parent.unbind('click');
                    tmp_parent.removeAttr('href');
                }
            }
}

$(document).ready(function(){
    if ($.browser.msie)
    IEFix();
/*$('.scroller').jScrollPane({
    autoReinitialise: true,
    maintainPosition: false
});
*/
minimizeDescription();
updateImages();
/*
   $(document).scroll(function() {
   var scrollTop = $(window).scrollTop();
   var documentHeight = $(document).height();
   var windowHeight = $(window).height();
   var pageHeight = $('body').height();
   var footerHeight = $('#footer').height()+50;
   var panelHeight = $('#left-bar').height()+450;

   var delta = documentHeight-scrollTop-panelHeight+footerHeight;

   if(delta < 0) {
   $('#left-bar').css({'margin-top':delta});
   } else {
   $('#left-bar').css({'margin-top':42});
   }
   if(windowHeight > pageHeight)
   $('#footer').css({position:'absolute', bottom:0});
   });
   $(document).trigger('scroll');
   */
$('.product-link').live('click', function(){
    var $link = $(this);
    var name = $('.title', $link).text();
    var url = $link.attr('href');
    var id = $link.attr('id').replace('product-', '');

    addToViewList(name, url, id, true);
    return true;
})

$('.show-more').live('click', function(){
    $(this).toggleClass('active')
});

$('#comparsion ul.categories li div.holder').not('.open').css('display', 'none');

$(".scroll-bar-start").not('.compare').not('.new').click(function(){
    ScrollBarSlide($(this), 'prev');
    return false;
});
$(".scroll-bar-end").not('.compare').not('.new').click(function(){
    ScrollBarSlide($(this), 'next');
    return false;
});
$(".scroll-bar-start.compare").click(function(){
    ScrollBarSlideC($(this), 'prev');
    return false;
});
$(".scroll-bar-end.compare").click(function(){
    ScrollBarSlideC($(this), 'next');
    return false;
});


$(".scroll-bar-start.new").mousedown(function(e){
    e.stopPropagation();
    e.preventDefault();
    var scroll = $(this).parents(".scroll-bar-container").find('.scroll');
    Slide(scroll, 24, true, 5000);
    return false;
});

$(".scroll-bar-end.new").mousedown(function(e){
    e.stopPropagation();
    e.preventDefault();
    var scroll = $(this).parents(".scroll-bar-container").find('.scroll');
    Slide(scroll, 900, true, 5000);
    return false;
});

$(".scroll-bar-start.new").mouseup(function(e){
    e.stopPropagation();
    e.preventDefault();
    var scroll = $(this).parents(".scroll-bar-container").find('.scroll');
    scroll.parents('div.holder').find('.scroll-pane').stop();
    scroll.stop();
    return false;
});

$(".scroll-bar-end.new").mouseup(function(e){
    e.stopPropagation();
    e.preventDefault();
    var scroll = $(this).parents(".scroll-bar-container").find('.scroll');
    scroll.parents('div.holder').find('.scroll-pane').stop();
    scroll.stop();
    return false;
});


$(".scroll-bar-container").not('.compare').not('.new').click(function(e){
    if(!$(e.target).is('div.new')){
        Slide($(this).find(".scroll"), e.pageX, true);
    }
});
$(".scroll-bar-container").not('.compare').not('.new').mousedown(function(e){
    if(!$(e.target).is('div.new')){
        $(this).mousemove(function(e){Slide($(this).find(".scroll"), e.pageX);});
    }
});
$(".scroll-bar-container.compare").click(function(e){
    SlideC($(this).find(".scroll"), e.pageX, true);
});
$(".scroll-bar-container.compare").mousedown(function(){
    $(this).mousemove(function(e){
        SlideC($(this).find(".scroll"), e.pageX);
    });
});

$(".scroll-bar-container").mouseup(function(e){
    if(!$(e.target).is('div.new')){
        setTimeout(function(){
            $('.scroll-bar-container').unbind('mousemove');
        }, 20);
    }
});


highligth("#compare li");
highligth(".buy-info li.row", true);
var l = $("#basket-list li").length;
$("#basket-count").text("(" + (l - 1) + ")");
if (l > 1) 
    $("#checkout").css("display", "block");
if (l > 4) 
    $("#basket .holder .scroll-up, #basket .holder .scroll-down").css("display", "block");
    $("#shops-holder, #leave-reply-form, #vendors-all, #markets-all, #delivery-box").css("display", "none");
    $("ul.category-list li div.holder .slider-wrap").css("opacity", 0.5);
    $("#price-dynamics-tab-link").click(function(){
        $(".main .product .holder .tab").removeClass("open");
        $("#price-dynamics").addClass("open");
        $(".main .product .holder-header ul li a").removeClass("active");
        $(".main .product .holder-header ul li a[href='#price-dynamics']").addClass("active");
        $.scrollTo("#price-dynamics", 500);
        return false;
    });
$("#shops, #brands").click(function(){
    $("#shops, #brands").parent("li").removeClass("active");
    $(this).parent("li").addClass("active");
    $("#shops-holder, #brands-holder").css("display", "none");
    $("#" + $(this).attr("id") + "-holder").css("display", "block");
    return false;
});
$("input[title], textarea[title]").live('focus', function(){
    if ($(this).attr('title') == $(this).attr('value')) {
        $(this).attr('value', '');
    }
});
$("input[title], textarea[title]").live('blur', function(){
    if ($(this).attr('value') == '') {
        $(this).attr('value', $(this).attr('title'));
    }
});
$("#header form ul li a").click(function(){
    $("#header form ul li").removeClass("active");
    $(this).parent().addClass("active");
    $("#area").attr("value", $(this).attr("accesskey"));
    return false;
});
$("ul.category-list li a.more").click(function(){
    var count = Math.floor($("#content").width() / $("ul.category-list > li").width(), 0);
    $("ul.category-list > li").each(function(index){
        if ((index % count) == 0) 
        $(this).css('clear', 'left');
        else 
        $(this).css('clear', 'none');
    });
    if ($(this).hasClass("open")) {
        $(this).prev("div.holder").animate({
            height: "168px"
        }, 400);
        $(this).removeClass("open");
    }
    else {
        $(this).prev("div.holder").animate({
            height: $(this).prev("div.holder").children("ul").children("li").length * 28
        }, 400);
        $(this).addClass("open");
    }
return false;
});
$("#left-bar div.block div.holder").each(function(){
    if (!$(this).hasClass("open")) 
    $(this).css("display", "none");
});
$("#left-bar div.block div.header a.toggle").click(function(){
    if ($(this).hasClass("open")) {
        $(this).removeClass("open");
        $(this).parent("div.header").next("div.holder").slideUp();
    }
    else {
        $(this).addClass("open");
        $(this).parent("div.header").next("div.holder").slideDown();
    }
return false;
});
$("#comparsion ul.categories li h2 a.toggle").click(function(){
    if ($(this).hasClass("open")) {
        $(this).removeClass("open");
        $(this).parent("h2").next("div.holder").slideUp();
    }
    else {
        $(this).addClass("open");
        $(this).parent("h2").next("div.holder").slideDown();
    }
return false;
});
$("ul.rating li a").click(function(){
    var score = parseFloat(this.innerHTML);
    var product_id = parseInt(this.parentNode.parentNode.id.replace('product-rating-', ''));
    $.post('/product/evaluate', {
        'score': score,
        'product_id': product_id
    }, function(data){
        var new_score = parseFloat(data['score']);
        var rating_element = $('#product-rating-' + product_id);
        var childrens = rating_element.children();
        childrens.each(function(){
            var element = $(this);
            element.removeClass('hover');
            element.removeClass('inactive');
            var current_rating = parseFloat($('a', element).text());
            if (current_rating <= new_score) {
                // добавлять не только active, но и left-active или right-acrive
                element.addClass('active');
            }
            else {
                element.removeClass('active');
            }
        });
    }, 'json');
    return false;
});
if ($.browser.msie && parseInt($.browser.version, 10) < 7) {
    //Rating hack for IE6 :(
    $("ul.rating li a").hover(function(){
        if ($(this).parent("li").hasClass('left')) 
        $(this).parent("li").css('background-position', '-6px 0');
        else 
        $(this).parent("li").css('background-position', '0 0');
    $(this).parent("li").prevAll().each(function(e){
        if ($(this).hasClass('left')) 
        $(this).css('background-position', '-6px 0');
        else 
        $(this).css('background-position', '0 0');
    });
    $(this).parent("li").nextAll().each(function(e){
        if ($(this).hasClass('left')) 
        $(this).css('background-position', '-19px 0');
        else 
        $(this).css('background-position', '-13px 0');
    });
    }, function(){
        if ($(this).parent("li").hasClass('left-active') && !$(this).parent("li").hasClass('left')) 
        $(this).parent("li").css('background-position', '-6px 0');
    if ($(this).parent("li").hasClass('left')) 
        $(this).parent("li").css('background-position', '-19px 0');
    if ($(this).parent("li").hasClass('right-active') && !$(this).parent("li").hasClass('right')) 
        $(this).parent("li").css('background-position', '0 0');
    if ($(this).parent("li").hasClass('right')) 
        $(this).parent("li").css('background-position', '-13px 0');
    });
    $(this).parent("li").prevAll().each(function(e){
        if ($(this).hasClass('left')) {
            if ($(this).hasClass('active')) 
        $(this).css('background-position', '-6px 0');
            else 
        $(this).css('background-position', '-19px 0');
        }
        else {
            if ($(this).hasClass('active')) 
        $(this).css('background-position', '0 0');
            else 
        $(this).css('background-position', '-13px 0');
        }
    });
    $(this).parent("li").nextAll().each(function(e){
        if ($(this).hasClass('left')) {
            if ($(this).hasClass('active')) 
        $(this).css('background-position', '-6px 0');
            else 
        $(this).css('background-position', '-19px 0');
        }
        else {
            if ($(this).hasClass('active')) 
        $(this).css('background-position', '0 0');
            else 
        $(this).css('background-position', '-13px 0');
        }
    });
}
else {
    $("ul.rating li a").hover(function(){
        $(this).parent("li").addClass("hover");
        $(this).parent("li").prevAll().addClass("hover");
        $(this).parent("li").nextAll().addClass("inactive");
    }, function(){
        $(this).parent("li").removeClass("hover");
        $(this).parent("li").prevAll().removeClass("hover");
        $(this).parent("li").nextAll().removeClass("inactive");
    });
}
$("#wishlist-link").click(function(){
    $(this).parent("li").addClass("active");
    $("#viewlist-link").parent("li").removeClass("active");
    $("#view-list").css("display", "none");
    $("#wish-list").css("display", "block");
    return false;
});
$("#viewlist-link").click(function(){
    $(this).parent("li").addClass("active");
    $("#wishlist-link").parent("li").removeClass("active");
    $("#wish-list").css("display", "none");
    $("#view-list").css("display", "block");
    return false;
});
/*
   $("div.block h2").click(function(){
   $(this).next("div.holder").slideToggle();
   return false;
   });
   */
$(".scroll-holder").scrollerVertical();
$("ul.category-list li div.holder").hover(function(){
        $(this).children(".slider-wrap").css("opacity", 1);
    }, function(){
        $(this).children(".slider-wrap").css("opacity", 0.5);
});

$(".add-to-cart").click(function(){
    $("#basket-list").append('<li><a href="#">Apple iPod shuffle 4 2Gb 3 4 5 3Gb 4Gb</a><a class="delete" href="#">delete</a><div class="fadeOut pngfix"></div></li>');
    $("#checkout").css("display", "block");
    var l = $("#basket-list li").length;
    $("#basket-count").text("(" + (l - 1) + ")");
    if (l > 4) {
        $("#basket .holder .scroll-up, #basket .holder .scroll-down").css("display", "block");
        $("ol#basket-list").scrollTo("max");
    }
    return false;
});

$("#basket-list li a.delete").live('click', function(){
    $(this).parent("li").remove();
    var l = $("#basket-list li").length;
    $("#basket-count").text("(" + (l - 1) + ")");
    if (l <= 1) 
    $("#checkout").css("display", "none");
    if (l <= 4) {
        $("#basket .holder .scroll-up, #basket .holder .scroll-down").css("display", "none");
        $("ol#basket-list").scrollTo(0);
        $("ol#basket-list").scrollTo("max");
    }
    return false;
});


$("#wishlist li a.delete").live('click', function(){
    var a = 6;
    if ($(this).parent().parent().parent().hasClass('single')) 
    var a = 2;
    var product_id = this.name;

    var viewlist_element = $("#viewlist li a[name='" + product_id + "']")[0];
    if(viewlist_element){
        viewlist_element = $(viewlist_element);
        plus_button = viewlist_element.next();
        if(plus_button.is('a')){
            plus_button.remove();
        }
        var name = viewlist_element.text();
        url = viewlist_element.attr('href');

        plus_button = $('<a/>', {
            class    : 'wishlist',
            href     : '#',
            text     : '<span>В вишлист</span>',
            onclick  : 'addToWishListFromViewList(this, \'' + name + '\', \'' + url + '\', \'' + product_id + '\');return false;'
        }).insertAfter(viewlist_element);
    }

    $(this).parent("li").remove();
    var l = $("#wishlist li").length;
    $("#wishlist-count").text("(" + (l - 1) + ")");
    if (l <= a) {
        $("#wish-list .scroll-up, #wish-list .scroll-down").css("display", "none");
        $("#wishlist").scrollTo(0);
        $("#wishlist").scrollTo("max");
    }
    return false;
});

$("#compare li a.delete").live('click', function(){
    var id = $(this).attr("id").replace('compare-', '');
    $(this).parent("li").remove();
    $("#checkbox-" + id).attr("checked", "");
    $("label[for=checkbox-" + id + "]").removeClass("ui-state-active");
    highligth("#compare li");
    return false;
});
$(".compare-box").click(function(){
    var id = $(this).attr("id").replace('checkbox-', '');
    if ($(this).is(":checked")) {
        $("#compare").append('<li><span>Apple iPod shuffle 4 2Gb 1 2 3 4 5 6 7</span><a class="delete" href="#" id="compare-' + id + '">delete</a><div class="fadeOut pngfix"></div></li>');
    }
    else {
        $("a#compare-" + id).parent("li").remove();
    }
highligth("#compare li");
});
//$(".scroll-pane").scrollerLabeled();
$("ul.names, ol#basket-list, ol#wishlist, ol#viewlist").scrollTo(0);
//$.scrollTo( 0 );
$(".compare-box").button();
$(".vendors li input").button();
$(".markets li input").button();
$('select.custom').selectmenu({
    style: 'dropdown'
});
$('.show_tip').mouseover(function(){
    $('div.proposal', this).show();
});
$('.show_tip').mouseout(function(){
    var $this = $('div.proposal', this)
    if (!$this.hasClass('opened')) 
    $('div.proposal', this).hide();
});
$('h2').hover(function(){
    $(this).addClass('hover');
}, function(){
    $(this).removeClass('hover');
})
/*
   $('a[target]').each(function(){
   $(this).attr('title', 'Открыть в новом окне');
   })
   */
$('.names a').each(function(){
    var $this = $(this);
    if ($this.attr('href') == document.location.pathname) {
        var text = $this.html();
        $this.parent().append('<strong>' + text + '</strong>');

        $('a').each(function(){
            var _this = $(this);                                               
            if(_this.attr('href') =='#'+text[0]){                                      
                $("#brands-holder ul.names").stop().scrollTo(_this.attr("href"), 1);

            }
        });
        $this.parent().find('.proposal').show().addClass('opened');
        $this.remove();
    }
})
try {
    $("#brands-holder .scroll-down, #shops-holder .scroll-down").click(function(){
        $(this).prev("ul.names").stop().scrollTo('+=172', 1000);
        return false;
    });
    $("#brands-holder .scroll-up, #shops-holder .scroll-up").click(function(){
        $(this).next("ul.names").stop().scrollTo('-=172', 1000);
        return false;
    });
    $("#basket .scroll-down").click(function(){
        var h = $("#basket-list li").outerHeight(true);
        $("ol#basket-list").stop().scrollTo('+=21', 1000);
        return false;
    });
    $("#basket .scroll-up").click(function(){
        var h = $("#basket-list li").outerHeight(true);
        $("ol#basket-list").stop().scrollTo('-=21', 1000);
        return false;
    });
    $("#wish-list .scroll-down").click(function(){
        $("ol#wishlist").stop().scrollTo('+=25', 1000);
        return false;
    });
    $("#wish-list .scroll-up").click(function(){
        $("ol#wishlist").stop().scrollTo('-=25', 1000);
        return false;
    });
    $("#view-list .scroll-down").click(function(){
        $("ol#viewlist").stop().scrollTo('+=25', 1000);
        return false;
    });
    $("#view-list .scroll-up").click(function(){
        $("ol#viewlist").stop().scrollTo('-=25', 1000);
        return false;
    });
    $("#brands-holder ul.alphabet li a").click(function(){
        $("#brands-holder ul.names").stop().scrollTo($(this).attr("href"), 1000);
        return false;
    });
    $("#shops-holder ul.alphabet li a").click(function(){
        $("#shops-holder ul.names").stop().scrollTo($(this).attr("href"), 1000);
        return false;
    });
    var myNewFlow = new ContentFlow('ContentFlow', {
        onclickActiveItem: function(el){

                               return;
                           },
        reflectionGap: 1,
        scaleFactor: 1.2
    });
} 
catch (e) {
}
$("#display-slider").slider({
    range: true,
min: 2,
max: 48,
values: [3, 36],
create: function(event, ui){                        
    $(this).children("a.ui-slider-handle:last").addClass("right").css('background-position', '-6px 0');
    $("#min-value-display").css("left", $(this).children("a.ui-slider-handle").eq(0).css("left"));
    $("#max-value-display").css("left", $(this).children("a.ui-slider-handle").eq(1).css("left"));
},
slide: function(event, ui){            
           $("#min-value-display").css("left", $(this).children("a.ui-slider-handle").eq(0).css("left"));
           $("#max-value-display").css("left", $(this).children("a.ui-slider-handle").eq(1).css("left"));
           $("#min-value-display").text(ui.values[0]);
           $("#max-value-display").text(ui.values[1]);
           $("#display-min").val(ui.values[0]);
           $("#display-max").val(ui.values[1]);
       }
       });
$(".main .product .holder-header ul li a").click(function(){
    $(".main .product .holder-header ul li a").removeClass("active");
    $(this).addClass("active");
    $(".main .product .holder .tab").removeClass("open");
    $($(this).attr("href")).addClass("open");
    $('select.custom').selectmenu("destroy");
    $('select.custom').selectmenu({
        style: 'dropdown'
    });
    return false;
});
if (!$.browser.msie || $.browser.version > 6) 
    $(".tooltip").mopTip({
        'w': 250,
        'style': "overOut",
        'get': "#tooltip"
    });
$("#leave-reply").click(function(){
    $("#leave-reply-form").css("display", "block");
    return false;
});
$("#delivery-select").click(function(){
    $("#delivery-box").css("display", "block");
    return false;
});
$("#leave-reply-form a.close").click(function(){
    $("#leave-reply-form").css("display", "none");
    return false;
});
$("#delivery-box a.close").click(function(){
    $("#delivery-box").css("display", "none");
    return false;
});


$("#vendors-popular-link").click(function(){
    $.cookie('vendors-popular', 1);
    $(this).addClass("active");
    $("#vendors-all-link").removeClass("active");
    $("#vendors-popular").css("display", "block");
    $("#vendors-all").css("display", "none");
    return false;
});

$("#vendors-all-link").click(function(){
    $.cookie('vendors-popular', 0);
    $(this).addClass("active");
    $("#vendors-popular-link").removeClass("active");
    $("#vendors-all").css("display", "block");
    return false;
});



//    $("#vendors-popular-link").click(function(){
//        $.cookie('vendors-popular', 1);
//        $(this).addClass("active");
//        $("#vendors-all-link").removeClass("active");
//        $("#vendors-popular").show();
//        $("#vendors-all").hide();
//        return false;
//    });
//    
//    $("#vendors-all-link").click(function(){
//        $.cookie('vendors-popular', 0);
//        $(this).addClass("active");
//        $("#vendors-popular-link").removeClass("active");
//        $("#vendors-all").show();
//        $("#vendors-popular").hide();
//        return false;
//    });
if ($.cookie('vendors-popular') != 1) {
    $("#vendors-all-link").click();
}
$("#markets-popular-link").click(function(){
    $.cookie('markets-popular', 1);
    $(this).addClass("active");
    $("#markets-all-link").removeClass("active");
    $("#markets-popular").css("display", "block");
    $("#markets-all").css("display", "none");
    return false;
});
$("#markets-all-link").click(function(){
    $.cookie('markets-popular', 0);
    $(this).addClass("active");
    $("#markets-popular-link").removeClass("active");
    $("#markets-all").css("display", "block");
    return false;
});
if ($.cookie('markets-popular') != 1) {
    $("#markets-all-link").click();
}
$("a.item").click(function(){
    return false;
});
$("#delivery-button").click(function(){
    $("#delivery-select span").text($("#town-select").val());
    $("#delivery-box").css("display", "none");
    return false;
});
$("ul.comparsion-items li.item a.delete").click(function(){
    compareItemDelete($(this));
    return false;
});

/*        
          JSON.stringify = JSON.stringify || function (obj) {
          var t = typeof (obj);
          if (t != "object" || obj === null) {
// simple data type
if (t == "string") obj = '"'+obj+'"';
return String(obj);
}
else {
// recurse array or object
var n, v, json = [], arr = (obj && obj.constructor == Array);
for (n in obj) {
v = obj[n]; t = typeof(v);
if (t == "string") v = '"'+v+'"';
else if (t == "object" && v !== null) v = JSON.stringify(v);
json.push((arr ? "" : '"' + n + '":') + String(v));
}
return (arr ? "[" : "{") + String(json) + (arr ? "]" : "}");
}
};
*/
try {
    json_stringify = JSON.stringify;
} 
catch (e) {
    json_stringify = function(obj){
        var t = typeof(obj);
        if (t != "object" || obj === null) {
            // simple data type
            if (t == "string") 
                obj = '"' + obj + '"';
            return String(obj);
        }
        else {
            // recurse array or object
            var n, v, json = [], arr = (obj && obj.constructor == Array);
            for (n in obj) {
                v = obj[n];
                t = typeof(v);
                if (t == "string") 
                    v = '"' + v + '"';
                else 
                    if (t == "object" && v !== null) 
                        v = json_stringify(v);
                json.push((arr ? "" : '"' + n + '":') + String(v));
            }
            return (arr ? "[" : "{") + String(json) + (arr ? "]" : "}");
        }
    };
}

});
function renderCompareList(){
    $('ul.comparsion-items li.item').width($('#comparsion').width() / 4);
    $('ul.comparsion-items').each(function(){
        $(this).height($(this).children('li.item').height());
        $(this).width($(this).children('li.item').width() * $(this).children('li.item').length + 55);
    });
}

function updateCompareList(){
    $('ul.comparsion-items li.item div.description ul li h3 span').css('display', 'block');
    $('ul.comparsion-items li.item div.description').removeClass('odd');
    $('ul.comparsion-items li.item div.description:odd').addClass('odd');
    $('ul.comparsion-items li.item div.description ul li h3.t1 span').not($('ul.comparsion-items li.item div.description ul li h3.t1 span')[0]).css('visibility', 'hidden');
    $('ul.comparsion-items li.item div.description ul li h3.t2 span').not($('ul.comparsion-items li.item div.description ul li h3.t2 span')[0]).css('visibility', 'hidden');
    $('ul.comparsion-items li.item div.description ul li h3.t3 span').not($('ul.comparsion-items li.item div.description ul li h3.t3 span')[0]).css('visibility', 'hidden');
    $('ul.comparsion-items li.item div.description ul li h3.t4 span').not($('ul.comparsion-items li.item div.description ul li h3.t4 span')[0]).css('visibility', 'hidden');
}

function compareItemDelete(e){
    var block = e.parent().parent().parent().prev('h2').parent('li');
    var countH = e.parent().parent().parent().prev('h2').children('span');
    var count = e.parent('li').parent('ul').children('li').length - 1;
    e.parent('li').remove();
    countH.text(count);
    if (count <= 0) 
        block.fadeOut();
    $('ul.comparsion-items li.item div.description ul li h3 span').css('visibility', 'visible');
    $('ul.comparsion-items li.item div.description ul li h3.t1 span').not($('ul.comparsion-items li.item div.description ul li h3.t1 span')[0]).css('visibility', 'hidden');
    $('ul.comparsion-items li.item div.description ul li h3.t2 span').not($('ul.comparsion-items li.item div.description ul li h3.t2 span')[0]).css('visibility', 'hidden');
    $('ul.comparsion-items li.item div.description ul li h3.t3 span').not($('ul.comparsion-items li.item div.description ul li h3.t3 span')[0]).css('visibility', 'hidden');
    $('ul.comparsion-items li.item div.description ul li h3.t4 span').not($('ul.comparsion-items li.item div.description ul li h3.t4 span')[0]).css('visibility', 'hidden');
}

function highligth(el, odd){
    $(el).removeClass("even-row");
    if (odd) 
        $(el + ":odd").addClass("even-row");
    else 
        $(el + ":even").addClass("even-row");
}

$(window).resize(function(){
    ScrollLabelResize();
    //$(".scroll-pane").scrollerLabeled();
    var count = Math.floor($("#content").width() / $("ul.category-list > li").width(), 0);
    $("ul.category-list > li").each(function(index){
        if((index % count) == 0)
        $(this).css('clear', 'left');
        else
        $(this).css('clear', 'none');
    });
});

function addToWishList(name, url, product_id, refresh){

    if (isInStorage(product_id + 'w') && (refresh == true)) {
        return false;
    }
    var a = 6;
    if ($('#wish-list').hasClass('single')) 
        var a = 1;
    $("#wishlist").append('<li><a target="_blank" href="' + url + '">' + name + '</a><a name="' + product_id + '" class="delete" href="#" onclick="removeFromStorage(\'' + product_id + 'w\');">delete</a><div class="fadeOut pngfix"></div></li>');
    var viewlist_element = $("#viewlist li a[name='" + product_id + "']")[0];
    if(viewlist_element){
        viewlist_element = $(viewlist_element);
        plus_button = viewlist_element.next();
        if(plus_button.is('a')){
            plus_button.remove();
        }
    }

    var l = $("#wishlist li").length;
    $("#wishlist-count").text("(" + (l - 1) + ")");
    if (l > a) 
        $("#wish-list .scroll-up, #wish-list .scroll-down").css("display", "block");
    $("#wishlist").scrollTo("max");
    if (refresh == true) {
        saveToStorage(product_id + 'w', name + '::' + url);
    }

}

function addToViewList(name, url, product_id, refresh){
    if (isInStorage('v_' + product_id + 'v') && (refresh == true)) {
        return false;
    }
    var a = 6;
    if ($('#view-list').hasClass('single')) 
        var a = 1;
    if (isInStorage(product_id + 'w')) 
        $("#viewlist").append('<li><a name="' + product_id + '" target="_blank" href="' + url + '">' + name + '</a><div class="fadeOut pngfix"></div></li>');
    else 
        $("#viewlist").append('<li><a name="' + product_id + '" target="_blank" href="' + url + '">' + name + '</a><a class="wishlist" href="#" onclick="addToWishListFromViewList(this, \'' + name + '\', \'' + url + '\', \'' + product_id + '\');return false;"><span>В вишлист</span></a><div class="fadeOut pngfix"></div></li>');
    var l = $("#viewlist li").length;
    $("#view-count").text("(" + (l - 1) + ")");
    if (l > a) 
        $("#view-list .scroll-up, #view-list .scroll-down").css("display", "block");
    $("#viewlist").scrollTo("max");
    if (refresh == true) {
        saveToStorage(product_id + 'v', name + '::' + url);
    }
}

function addToWishListFromViewList(element, name, url, product_id){
    var offset = $(element).offset();
    var offsetBlock = $("#view-list").offset();
    $(element).remove();
    var id = "id_" + Math.round(Math.random() * (100 - 1) + 1);
    $("body").append('<a class="wishlist-moved" href="#" id="' + id + '"><span>В вишлист</span></a>');
    $("#" + id).css("top", offset.top + "px").css("left", offset.left + "px");
    $("#" + id).animate({
        top: offsetBlock.top - 15 + "px",
        left: offsetBlock.left + 80 + "px"
    }, 1500, null, function(){
        $("#" + id).fadeOut();
        setTimeout(function(){
            $("#" + id).remove();
        }, 1000);
    });
    addToWishList(name, url, product_id, true);
    return false;
}


function markProductInViewList(product_id){
}

function unmarkProductInViewList(product_id){
}

function ScrollLabelResize() {
    $(".scroll-bar[unselectable=on]").each(function(){
        var $this = $(this);
        var left = $(".scroll-bar").width() / $this.find('span').length;
        var start = left / 2 - 36;
        $this.find('span').each(function(){
            $(this).css('left', start);
            start += left;
            $(this).onselectstart = function() { return false; };
            $(this).unselectable = "on";
            $(this).css('-moz-user-select', 'none');
        });
        var itemCount = $this.parents('.holder').find('.scroll-pane li:visible').length;
        var width = itemCount * 135;
        $this.parents('.holder').find('.scroll-pane ul').css({width: width});
        if (itemCount < 7) {
            $this.parents('.holder').find('.scroll-bar-container').hide();
        }
    });
}

function Slide(object, left, animate, latency){
    if(!latency){
        latency = 500;
    }
    var left_parent = object.parent().offset().left;
    var new_left = left - object.parent().offset().left - (object.width() / 2);
    var max_left = object.parent().width() - object.width();
    if(new_left < 25) new_left = 25;
    if(max_left < new_left) new_left = max_left;
    var percent =  Math.floor( (new_left - 25) / ((object.parent().width() - object.width()) / 100), 0);
    var scroll_pane_left = (object.parents('div.holder').find('.scroll-pane ul').width() - object.parents('div.holder').find('.scroll-pane').width()) / 100 * percent
        if(animate == true) {
            object.stop().animate({'left': new_left}, latency);
            object.parents('div.holder').find('.scroll-pane').animate({scrollLeft: scroll_pane_left}, latency);
        } else {
            object.css('left', new_left);
            object.parents('div.holder').find('.scroll-pane').scrollLeft(scroll_pane_left);
        }
    return true;
}

function ScrollBarSlide(object, action){
    var scroll = object.parents(".scroll-bar-container").find('.scroll');
    var scroll_center_position = scroll.offset().left + (scroll.width() / 2);
    var end;
    if(action == 'next'){
        object.parents(".scroll-bar-container").find('.scroll-bar span').each(function(index){
            var span_center = $(this).offset().left + ($(this).width() / 2);
            if(span_center > scroll_center_position + 5 && !end) {
                Slide(scroll, span_center, true);
                end = true;
            }
        });
    } else {
        var prev;
        object.parents(".scroll-bar-container").find('.scroll-bar span').each(function(index){
            var span_center = $(this).offset().left + ($(this).width() / 2);
            if(span_center < scroll_center_position)prev = span_center;
        });
        Slide(scroll,  prev, true);
    }
    return true;
}

function ScrollBarSlideC(object, action){
    var h = object.parents('div.holder').find('ul.comparsion-items').position().left;
    var w = object.parents('div.holder').find('ul.comparsion-items li').width();
    if (action == 'prev'){
        SlideC(scroll,  h+w, true);
    }
    if (action == 'next'){
        SlideC(scroll,  h-w, true);
    }
    return true;
}

function SlideC(object, left, animate){
    if ($.browser.msie) {
        if(parseInt($.browser.version, 10) < 7){
            object.parents('div.holder').css("width", $('#holder').width());
        }
    }
    var o = object.parent().offset();
    var left_parent = o.left;
    var p_w = object.parent().width();
    var w = object.width();
    var new_left = left - left_parent - (w / 2);
    var max_left = p_w - w;
    if(new_left < 25) new_left = 25;
    if(max_left < new_left) new_left = max_left;
    var c1 = p_w - w;
    var c2 = c1 / 100;
    var c3 = new_left - 25;
    var percent = Math.floor( c3 / c2);
    var scroll_pane_left = (object.parents('div.holder').find('ul.comparsion-items').width() - object.parents('div.holder').width()) / 100 * percent;
    if(animate == true) {
        object.stop().animate({'left': new_left}, 500);
        object.parents('div.holder').find('ul.comparsion-items').animate({'left': '-'+scroll_pane_left}, 500);
    } else {
        object.css('left', new_left);
        object.parents('div.holder').find('ul.comparsion-items').scrollLeft('-'+scroll_pane_left);
    }
    synchronizeSliders(object, new_left);
    return true;
}
function synchronizeSliders(obj, left){
    var duplicate = obj.parent('.scroll-bar-wrap').parent('.scroll-bar-container').parent('.holder').children('.scroll-bar-container').children('.scroll-bar-wrap').children('.scroll');
    duplicate.css('left', left);
}
function IEFix(){
    $('ul.rating li').css('border-left', 'medium none');
    disableSelection($('.holder .scroll-pane, .holder .scroll-bar-container'));
}
function disableSelection(target){
    target.attr('unselectable', 'on');
    target.bind('onselectstart', function(){
        return false;
    });
}

function apply_filters(url, params){
    var form = $('#filters-form');
    var price_min = $('#price-min', form).attr('value');
    var price_max = $('#price-max', form).attr('value');
    var currency = $('#currency-select').attr('value');
    var markets = $('.markets input:checked');
    var vendors = $('.vendors input:checked');
    var query = $("#htxtFind").val();


    result_params = '?price_min=' + price_min + '&price_max=' + price_max + '&currency=' + currency;

    if (query) 
        result_params += '&query=' + query

            var params = params.split('&');
    for (var i = 0; i < params.length; i++) {
        if (!params[i].search('sort_by')) 
            result_params += '&' + params[i];
        if (!params[i].search('sort_order')) 
            result_params += '&' + params[i];
    }

    if (markets.length) {

        result_params += '&m_id=[';

        markets.each(function(){
            var id = this.id;
            id = id.replace('market-', '');
            result_params += id + ','
        });
        result_params = result_params.substring(0, result_params.length - 1) + ']';
    }

    if (vendors.length) {
        result_params += '&v_id=[';

        vendors.each(function(){
            var id = this.id;
            id = id.replace('vendor-', '');
            result_params += id + ','
        });
        result_params = result_params.substring(0, result_params.length - 1) + ']';
    }


    url = url.substring(0, url.length - 1) + '/1'
        window.location = url + result_params;
}

function reset_filters(url, params, price_max){
    var markets = $('.markets input:checked');
    var vendors = $('.vendors input:checked');
    var form = $('#filters-form');
    $('#price-min', form).attr('value', 0);
    $('#price-max', form).attr('value', price_max);

    vendors.each(function(){
        $(this).next().removeClass('ui-state-active');
        $(this).next().attr('aria-pressed', 'false');
        $(this).attr('checked', false);
    });

    markets.each(function(){
        $(this).next().removeClass('ui-state-active');
        $(this).next().attr('aria-pressed', 'false');
        $(this).attr('checked', false);
    });
    apply_filters(url, params);
}



function saveWishlistToCookie(){
    var wishlist = $('#wishlist');
    var toCookie = '';
    wishlist.children().each(function(){
        if (!$(this).hasClass('empty')) {
            var href = $('a', this).attr('href');
            var name = $('a', this).text();
            var obj = {};
            toCookie += name + '::' + href + ';;';
        }
    });
    expDate = new Date();
    expDate.setMonth(expDate.getMonth() + 1);
    setCookie('wishlist', toCookie, expDate.toUTCString(), '/');
}

function toCompareList(element, name, url){
    var id = $(element).attr("id").replace('checkbox-', '');
    if ($(element).is(":checked")) {
        $("#compare").append('<li><span>' + name + '</span><a class="delete" href="#" id="compare-' + id + '">delete</a><div class="fadeOut pngfix"></div></li>');
    }
    else {
        $("a#compare-" + id).parent("li").remove();
    }
    highligth("#compare li");
}

function getCookie(name){
    var cookie = " " + document.cookie;
    var search = " " + name + "=";
    var setStr = null;
    var offset = 0;
    var end = 0;
    if (cookie.length > 0) {
        offset = cookie.indexOf(search);
        if (offset != -1) {
            offset += search.length;
            end = cookie.indexOf(";", offset)
                if (end == -1) {
                    end = cookie.length;
                }
            setStr = unescape(cookie.substring(offset, end));
        }
    }
    return (setStr);
}

function setCookie(name, value, expires, path, domain, secure){
    document.cookie = name + "=" + escape(value) +
        ((expires) ? "; expires=" + expires : "") +
        ((path) ? "; path=" + path : "") +
        ((domain) ? "; domain=" + domain : "") +
        ((secure) ? "; secure" : "");
}

function redirectToLocation(url){
    window.open(url);
}

function isInStorage(key){

    if (typeof(Storage) != 'undefined' && Storage.get(key)) 
        return true;
    return false;
}

function saveToStorage(key, data){
    if (typeof(Storage) != 'undefined') 
        Storage.put(key, data);
}

function getFromStorage(key){
    if (typeof(Storage) != 'undefined') 
        return Storage.get(key);
    return false;
}

function removeFromStorage(key){
    if (typeof(Storage) != 'undefined') 
        Storage.remove(key);
}

function updateStorage(){

}

function _redirectTo(product){
    url = $(product).attr('href');
    name = $(product).text();
    product_id = $(product).attr('id').replace("product-", "")
        addToViewList(name, url, product_id, true);
    //redirectToLocation(url);
    return true;
}
