/*CUSTOM SELECT*/
function enableSelectBoxes(boxName, select)
{   
    select = typeof select !== 'undefined' ? select : null;
    $('div.selectBox'+ boxName).each(function(){
        $(this).children('span.selected'+ boxName +',span.selectArrow'+ boxName).click(function(){
            if($(this).parent().children('div.selectOptions'+ boxName).css('display') == 'none'){
                $(this).parent().children('div.selectOptions'+ boxName).css('display','block');
                $(this).parent().children('span.selectArrow'+ boxName).css('color','#9ecf00');
                $(this).parent().children('span.selected'+ boxName +',span.selectArrow'+ boxName).css('background-color','#ffffff');
            }
            else
            {
                $(this).parent().children('div.selectOptions'+ boxName).css('display','none');
            }
        });
        
        $(this).find('span.selectOption'+ boxName).click(function(){
            $(this).parent().css('display','none');
            $(this).closest('div.selectBox'+ boxName).attr('value',$(this).attr('value'));
            $(this).parent().siblings('span.selected'+ boxName).html($(this).html());
        });
        if (select){
            if ($(this).children('span.selected'+ boxName).text().length < 1){
                $('div.selectBox'+ boxName).children('div.selectOptions'+ boxName).children('span.selectOption'+ boxName).each(function( index ) {
                    if (this.attributes['value'].value == select){
                        $('div.selectBox'+ boxName).children('span.selected'+ boxName).html($(this).text());
                    }
                });
            }
        }
    }); 
}
/*SET LANG*/
function setLang(lang)
{   
    var oXMLHttpRequest = new XMLHttpRequest;
    oXMLHttpRequest.open("GET", "/main/lang?lang="+lang, false);
    oXMLHttpRequest.onreadystatechange  = function() {
        if (this.readyState == XMLHttpRequest.DONE) {
                window.location.reload(false);
        }
    }
    oXMLHttpRequest.send(null);
}
/*MENU URL STYLE */
function style_menu_url(id){
    $(id + ' a').each(function () {
        var location = window.location.href;
        var link = this.href;
        if(location == link) {
            $(this).parent().addClass('active-menu');
            $(this).addClass('active-menu');
        }
    });
}
function accordion_menu(){
    $("#accordion > li > div").click(function(){

        if(false == $(this).next().is(':visible')) {
            $('#accordion ul').slideUp(300);
        }
        $(this).next().slideToggle(300);
    });
    $("#accordion > li > ul > li > div").click(function(){

        if(false == $(this).next().is(':visible')) {
            $('#accordion li > ul > li > ul').slideUp(300);
        }
        $(this).next().slideToggle(300);
    });

    $('#accordion ul:eq(0)').show();
}
