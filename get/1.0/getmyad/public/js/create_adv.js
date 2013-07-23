var temp;
var ans = "";
var xclr = "ffffff";

var yclr = "0000ff";
var CostfontSize;
var TextfontSize = 11;
var HeaderfontSize;
var fnts;
//конвертация десятичных чисел в hex 
function decToHex(n){ return Number(n).toString(16); }
 
function hexTodec (hex){ return parseInt(hex,16); }
function rgb(r,g,b){
	var str="#";
	//ебанный стыд
	str+=decToHex(Math.floor(r));
	str+=decToHex(Math.floor(g));
	str+=decToHex(Math.floor(b));
	str = str.replace("#","");
	return str;
}


var hoverColor;
function splitRGB(color){	
		var rgb = color.replace(/[# ]/g, "").replace(/^(.)(.)(.)$/, '$1$1$2$2$3$3').match(/.{2}/g);
		for (var i = 0; i < 3; i++) 
			rgb[i] = parseInt(rgb[i], 16);
		return {
			'r': rgb[0],
			'g': rgb[1],
			'b': rgb[2]
		}
	};

//функция которая вызывается при загрузке информера, и вычисляет цвет навигации
function load_document(){
	//if(document.getElementById('xcolor')==null)return;	
	yclr = splitRGB($('#arrowColor').val());//splitRGB(document.getElementById('xcolor').style.backgroundColor);
	xclr = splitRGB($('#arrowBgColor').val());//splitRGB(document.getElementById('ycolor').style.backgroundColor);	
	var cr=2;
	var cg=2;
	var cb=2;
/*
    if(yclr['r']<200)cr=1.5;
	if(yclr['g']<200)cg=1.5;
	if(yclr['b']<200)cb=1.5;
*/		
	hoverColor=rgb((xclr['r']+yclr['r'])/cr,(xclr['g']+yclr['g'])/cg,(xclr['b']+yclr['b'])/cb);	
	
}

//**код  

function change(cl){

	load_document();
	var divs = document.getElementsByTagName("DIV");
	for (var i = 0; i < divs.length; i++) {
		if (divs[i].className == cl) 
		divs[i].style.backgroundColor ="#"+ hoverColor;
		}	
}

function change1(cl){
	var divs = document.getElementsByTagName("DIV");
	for (var i = 0; i < divs.length; i++) {
		if (divs[i].className == cl)
		divs[i].style.backgroundColor ="#"+ $('#arrowColor').val(); 			
		if (divs[i].className == cl + "1") {			
			divs[i].style.backgroundColor = "#"+$('#arrowBgColor').val();
		}
	}
}
//**/
var AdvertiseEditor = AdvertiseEditor || (function() {
	
	var patterns;			// Образцы выгрузок
	var advertise;			// Редактируемый информер
	
	/** Отрисовка информера с текущими настройками */
	function render() {		
		var o = advertise.options;
		o.Main.borderColor = $("#borderColor").val();
		o.Main.backgroundColor = $("#backgroundColor").val();
		o.Main.fontFamily = $('#headerFont').val();		
		o.Header.fontColor = $("#headerColor").val();
		o.Description.fontColor = $("#descriptionColor").val();
		o.Cost.fontColor = $("#priceColor").val();
		o.Cost.fontFamily = $('#priceFont').val();	
		o.Cost.fontSize=CostfontSize;			
		o.Header.fontUnderline = $("#headerUnderline").attr('checked');
		o.Nav.color = $("#arrowColor").val();				
		o.Nav.backgroundColor = $("#arrowBgColor").val();
		o.Nav.hovercolor = hoverColor;
		o.Nav.logoColor = $("#logo-color").val();				
		o.Header.fontFamily = $('#headerFont').val();
		o.Header.fontSize = HeaderfontSize;
		o.Description.fontFamily = $('#textFont').val();
		o.Description.fontSize = TextfontSize;	
		if (parseInt(o.Main.width) < 200) {
			o.Nav.path = "http://cdnt.yottos.com/getmyad/logos/yot/";
			o.Nav.logoWidth = 45;
		} else {
			o.Nav.path = "http://cdnt.yottos.com/getmyad/logos/";
			o.Nav.logoWidth = 100;
		}
	    var result = TrimPath.processDOMTemplate("styleTemplate", o);
		var items = [];
		for (var i=0; i<o.Main.itemsNumber; i++)			// Шаблонизатор не умеет делать циклы по счётчику :(
			items.push(i);
		result += TrimPath.processDOMTemplate("contentTemplate", {items: items});
	    $("#admakerPreview").html(result);
	}
	
	/** Загружает шаблон с заголовком title**/ 
	function loadPattern(title) {
		for (var i = patterns.length - 1; i >= 0; i--) {
			if (patterns[i].title == title) {
				var guid = patterns[i].guid;
				var lead0 = function(x) { return (x >= 10)? x : "0" + x; }
				var d = new Date();
                advertise.height = patterns[i].height;
                advertise.width = patterns[i].width;
				advertise.options = patterns[i].options;
				$("#admakerPreview").hide();	
				TextfontSize = advertise.options.Description.fontSize;	
				HeaderfontSize = advertise.options.Header.fontSize;
				CostfontSize = advertise.options.Cost.fontSize;
				fnts = 	TextfontSize;	
/*
 
				if ($('#textFont').val() == 'Verdana, "Geneva CY", "DejaVu Sans", sans-serif;') 
				{					
					TextfontSize = TextfontSize - 2;			
				}
				if ($('#headerFont').val() == 'Verdana, "Geneva CY", "DejaVu Sans", sans-serif;') 
				{
					HeaderfontSize = HeaderfontSize - 2;			
				}
				if ($('#priceFont').val() == 'Verdana, "Geneva CY", "DejaVu Sans", sans-serif;') 
				{
					CostfontSize = CostfontSize - 2;			
				}	*/				
				render();
				$("#admakerPreview").fadeIn();
				advertise.title = title + ', ' + lead0(d.getDate()) + '.' + lead0(d.getMonth() + 1) + '.' + d.getFullYear();
				$("#edit-informer-title").val(advertise.title);
				printInformerTitle();
				break;
			}
		};
	}
	
	/** Выводит название и сайт информера */
	function printInformerTitle() {
		$("#informer-title").text(advertise.domain + ', ' + advertise.title);
	}
	
	/** Редактирование названия информера*/
	$('#edit-informer-title').keyup(function(){
		advertise.title = $(this).val();
		printInformerTitle(); 
	})
	
	/** Выбор домена информера*/
	$('#informer-site').change(function(){
		advertise.domain = $(this).val();
		printInformerTitle(); 
	})
	
	$('#textFont').change(function(){
		if ($('#textFont').val() == 'Verdana, "Geneva CY", "DejaVu Sans", sans-serif;') {		
			TextfontSize = TextfontSize - 2;			
		}
		else {			
			TextfontSize = fnts;
		};
			render();
	});
	$('#headerFont').change(function(){	
		render();
	});
	$('#priceFont').change(function(){	
		render();
	});
	$('#textSize').keyup(function(){					
			render();
	});
	$('#headerSize').keyup(function(){	
		render();
	});
	$('#priceSize').keyup(function(){	
		render();
	});			
	/** Выбор размера информера из списка "другие размеры" */
	$('#size select').change(function(){
		var title = $(this).val();
		loadPattern(title);
	})

	/** Выбор размера информера */
	$(".listSizes a").click(function() {
		var title = $(this).text();
		loadPattern(title);
	})
	
	/**Цвет навигации*/
	$('#arrowColor').change(function(){			
		xclr = splitRGB($("#arrowColor").val());
		yclr = splitRGB($("#arrowBgColor").val());		
		//var bgclr = 
		
		hoverColor=rgb((xclr['r']+yclr['r'])/2,(xclr['g']+yclr['g'])/2,(xclr['b']+yclr['b'])/2);
		// $("#arrowBgColor").val(bgclr);
	});	
	
	
	/** Установка текстовых полей цветовой гаммы */
	function loadOptions(options) {
		var o = options;		
		setColor("#borderColor", o.Main.borderColor);
		setColor("#backgroundColor", o.Main.backgroundColor);
		setColor("#headerColor", o.Header.fontColor);
		setColor("#descriptionColor", o.Description.fontColor);
		setColor("#priceColor", o.Cost.fontColor);
		setColor("#arrowColor", o.Nav.color);
		setColor("#arrowBgColor", o.Nav.backgroundColor);
		setColor("#logo-color", o.Nav.logoColor);		
		$("#headerUnderline").attr('checked', o.Header.fontUnderline);
		$('#textFont').val(o.Description.fontFamily);		
		$('#priceFont').val(o.Cost.fontFamily);
		$('#headerFont').val(o.Description.fontFamily);
		TextfontSize = o.Description.fontSize;		
		fnts = TextfontSize; 
		HeaderfontSize = o.Header.fontSize;
		CostfontSize = o.Cost.fontSize;	
	}


	function displayMessage(message) {
		$("#error-message").show().text(message).fadeOut(2500);
	}
	
	/** Сохранение информера */
	function save() {
		var result = TrimPath.processDOMTemplate("styleTemplate", advertise.options);
		temp = advertise.options;
		var items = [];
		for (var i = 0; i < advertise.options.Main.itemsNumber; i++)			// Шаблонизатор не умеет делать циклы по счётчику :(
			items.push(i);
		result += TrimPath.processDOMTemplate("contentTemplate", {items: items});
		advertise.non_relevant = advertise.non_relevant || {};
		advertise.non_relevant.action = $("#non-relevant").val();
		if (advertise.non_relevant.action == 'usercode')
			advertise.non_relevant.userCode = $('#user-code').val();
		else 
			advertise.non_relevant.userCode = '';

		
		$.ajax({
			url: '/advertise/save' + (advertise.guid? '?adv_id='+advertise.guid : '') ,
			type: 'POST',
			data: JSON.stringify({
				title: advertise.title,
				options: advertise.options,
				domain: advertise.domain,
				css: TrimPath.processDOMTemplate("styleTemplate", advertise.options),
				nonRelevant: advertise.non_relevant,
                height: advertise.height,
                width: advertise.width
			}),
			cache: false,
			dataType: 'json',
			contentType: "application/json; charset=utf-8",
			beforeSend: function() {
				$("#saveButton").attr("disabled", true);
			},
			success: function (result) {	
			ans = result;						
				if (result.error == false && result.id) {					
					advertise.guid = result.id;
					generateScriptCode(advertise.guid);
					$("#div-informer-code").fadeIn();
					displayMessage("Изменения успешно сохранены.");
				} else {
					if (result.error && result.error.message)
						displayMessage("Ошибка сохранения информера: " + result.error.message);
					else
						displayMessage("Ошибка сохранения информера!" + result.message);
				}
			},
			error: function () {
				displayMessage("Ошибка сохранения запроса! Попробуйте сохранить ещё раз.");
			},
			complete: function() {
				$('#saveButton').removeAttr("disabled");			
			} 
		})		
	} // end save
	
	$("#saveButton").click(save);
	
	/**
	 *  Не даёт выбрать белый логотип на белом фоне, синий -- на синем и т.д.
	 */ 
	function DisableColor(){
	    var cl = $("#backgroundColor").val();
		var rgb = splitRGB(cl);
		var selectedColor = $("select#logo-color").val();
	    $('select[@name=logo-color] option:disabled').removeAttr('disabled');
	
	    if (rgb['r'] >= 200 && rgb['g'] >= 200 && rgb['b'] >= 200) {
	        $('select[@name=logo-color] option:contains("белый")').attr('disabled', 'disabled');
	        if (selectedColor == "white") {
	            $("#logo-color :first").attr("selected", "selected");
	            $("#logo-color :first").click();
	        }
	    }
	    if (Math.abs(rgb['r'] - 66) <= 50 && Math.abs(rgb['g'] - 99) <= 50 && Math.abs(rgb['b'] - 221) <= 50) {
	        $('select[@name=logo-color] option:contains("синий")').attr('disabled', 'disabled');
	        if (selectedColor == "blue") {
	            $("#logo-color :last").attr("selected", "selected");
	            $("#logo-color :last").click();
	        }
	    }
	    if (Math.abs(rgb['r'] - 33) <= 50 && Math.abs(rgb['g'] - 33) <= 50 && Math.abs(rgb['b'] - 37) <= 90) {
	        $('select[@name=logo-color] option:contains("чёрный")').attr('disabled', 'disabled');
	        if (selectedColor == "black") {
	            $("#logo-color :first").attr("selected", "selected");
	            $("#logo-color :first").click();
	        }
	    }
		return;
		var rgb = splitRGB(cl);
		cl = $("#arrowBgColor").val();
		var bg = splitRGB(cl);
		if (Math.abs(rgb['r'] - bg['r']) <= 50 && Math.abs(rgb['g'] - bg['g']) <= 50 && Math.abs(rgb['b'] - bg['b']) <= 50) {
			var r = decToHex(255-bg['r']);
			var g = decToHex(255-bg['g']);
			var b = decToHex(255-bg['r']);		
			$("#arrowBgColor").val(r+g+b);			
		};	
		cl = $("#arrowColor").val();
		var rgb1 = splitRGB(cl);
		cl = $("#arrowBgColor").val();
		var bg = splitRGB(cl);
		if (Math.abs(rgb1['r'] - bg['r']) <= 50 && Math.abs(rgb1['g'] - bg['g']) <= 50 && Math.abs(rgb1['b'] - bg['b']) <= 50) {
			var r = decToHex(255-bg['r']);
			if (len(r)<2)r=r+"0";
			var g = decToHex(255-bg['g']);
			if (len(g)<2)g+="0";
			var b = decToHex(255-bg['r']);
			if (len(b)<2)b+="0";
			var bgcolor=r+g+b;
			//переделать!!!
//			if(bgcolor.lenght<6)bgcolor="000000";
//			$("#arrowBgColor").val(bgcolor);			
		};	
	};	

	/** Сheckbox "подчёркиваниe", выбор логотипа */
	$("#headerUnderline, #logo-color").change(render);
	
	/** Обработчик редактирования текстовых полей цветов */
	$('#color input:text').change(function(){
		$(this).parent().parent().find('.testColor').css("background-color", '#' + $(this).val());
		$(this).parent().parent().find('.testColor').ColorPickerSetColor($(this).val());
		DisableColor();				
	})
	
	$('#color input:text').keyup(function(){
		$(this).parent().parent().find('.testColor').css("background-color", '#' + $(this).val());
		$(this).parent().parent().find('.testColor').ColorPickerSetColor($(this).val());
		DisableColor();		
		render();
			
	})
	
	/** Устанавливает цвет */
	function setColor(selector, value) {
		$(selector).parent().parent().find('.testColor')
			.css("background-color", '#' + value)
			.ColorPickerSetColor(value);
		$(selector).val(value);
	}
	/*Устанавливает шрифт*/
	function setFont(selector, value){
		$(selector).css('font-family',value);
	} 
	
	/** Выбор preset палитры */
	$("#palette-preset").change(function() {		
		var palette = {
			'yasnost': {
				border: 'ffffff',
				background: 'ffffff',
				header: '0000FF',
				description: '4a4a4a',
				price: '008000',
				arrow: 'ffffff',
				arrowBg: '0000FF',
				logo: 'color'
			},
			'black_red': {
				border: '000000',
				background: 'ffffff',
				header: '000000',
				description: '4a4a4a',
				price: 'e00000',
				arrow: '000000',
				arrowBg: 'ffffff',
				logo: 'color'
			},
			'smoke': {
				border: '919191',
				background: '696969',
				header: 'ffffff',
				description: 'f2f2f2',
				price: 'f4ff9e',
				arrow: '000000',
				arrowBg: 'ffffff',
				logo: 'white'
			},
			'nega': {
				border: 'e6dbca',
				background: 'ffe8d6',
				header: '4d403c',
				description: '4a4a4a',
				price: '804545',
				arrow: 'ffe8d6',
				arrowBg: '804545',
				logo: 'color'
			}
		};
		var v = $(this).val();
		if (v in palette) {
			var p = palette[v];
			setColor("#borderColor", p.border);
			setColor("#backgroundColor", p.background);
			setColor("#headerColor", p.header);
			setColor("#descriptionColor", p.description);
			setColor("#priceColor", p.price);
			setColor("#arrowColor", p.arrow);
			setColor("#arrowBgColor", p.arrowBg);
			$("#logo-color").val(p.logo);
			render();
		}		
	});
	
	
	/** Составляет код рекламной выгрузки */
	function generateScriptCode(informerId) {
	$("#informer-code").val('<scr' + 'ipt type="text/javascript"><!--\n' + 
							'yottos_advertise = "' + informerId + '";\n' +
							'//-->\n' + 
							'</scr' + 'ipt>\n' +
							'<script type="text/javascript" src="http://cdn.yottos.com/getmyad/_a.js">' +
							'</sc' + 'ript>');							
							
	}
	
	/**
	 * Устанавливает действие в случае отсутствия релевантной рекламы.
	 * @param {Object} action		задаваемое действие, если не передаётся,
	 * 								то используется значение из формы
	 */
	function setNonRelevantAction(action) {		
		if (typeof(action) != 'string')
			action = $("#non-relevant").val();
		else
			$("#non-relevant").val(action);
		if (action == "usercode") {
			$("#user-code").show();
			$('#hintCode').show();
		}
		else {
			$("#user-code").hide();
			$('#hintCode').hide();
		}
			//$('#hintCode').css("dispaly","inline");
	}
	
	/** Инициализация интерфейса */
	function initInterface() {
		function createColorPicker(selector){
			$(selector).parent().parent().find('.testColor').ColorPicker({
				color: '#0000ff',
				onShow: function(colpkr){
					$(colpkr).fadeIn(00);
					return false;
				},
				onHide: function(colpkr){
					$(colpkr).fadeOut(00);
					return false;
				},
				onChange: function(hsb, hex, rgb){
					//$(selector).css('color', '#' + hex);
					$(selector).val(hex);
					$(selector).parent().parent().find('.testColor')
						.css("background-color", '#' + hex);
						
					$(selector).parent().parent().find('input').val(hex);
					DisableColor();
					render();								
				}
			}).bind('keyup', function(){
				$(this).ColorPickerSetColor(this.value);				
			})
		} // end createColorPicker()
		
		createColorPicker('#borderColor');
		createColorPicker('#headerColor');
		createColorPicker('#descriptionColor');
		createColorPicker('#priceColor');
		createColorPicker('#backgroundColor');
		createColorPicker('#arrowColor');
		createColorPicker('#arrowBgColor');
		
		// Щелчёк по вкладке "Мои информеры" */
		$("#tabs").tabs().bind('tabsselect', function (e,ui) {
			if (ui.index == 0) {
				window.location = '/private/index#informers';
				return true;
			}
			else 
				return true;	
		});

		$("#size .navigation-arrow").click(function () {
			$("#tabs").tabs("select", 2);
		});
		$("#color .navigation-arrow").click(function () {
			$("#tabs").tabs("select", 3);
		});
		$("#font .navigation-arrow").click(function () {
			$("#tabs").tabs("select", 4);
		});
		$("#informer-code").click(function() {
			this.select();
		});
		$("#non-relevant").change(setNonRelevantAction);
		$("#logo-color, #color .navigation-arrow").hover(DisableColor);
		
	} // end init()
	
	
	/**
	 * Строит интерфейс пользователя. 
	 */
	
	function init(options)
	{		
		advertise = options.advertise;
		patterns = options.patterns || {};
		initInterface();
		if (!advertise) {
			// Создание новой выгрузки
			advertise = {};
			$($(".listSizes a")[0]).click();
			$("#palette-preset").val('yasnost');
			$("#palette-preset").change();
			$("#div-informer-code").hide();
			$("#informer-site").change();
		} else {
			// Редактирование существующей выгрузки
			loadOptions(advertise.options);
			temp = advertise.options;
			$("#edit-informer-title").val(advertise.title);
			$("#palette-preset").val('none');
			$("#informer-site").val(advertise.domain);
			advertise.domain = $("#informer-site").val();
			printInformerTitle();
			generateScriptCode(advertise.guid);
			var action = (advertise.non_relevant && advertise.non_relevant.action) || 'social';
			switch (action) {
				case 'usercode':
					setNonRelevantAction('usercode');
					$("#user-code").html(advertise.non_relevant.userCode);
				break;

				case 'social':
				default:
					setNonRelevantAction('social');
				break;
			}
			render();
			
		}
		
	}
	
	return {
		init: init
		
		}
	
})();
