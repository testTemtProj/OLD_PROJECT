var AdvertiseEditor = AdvertiseEditor || (function() {
	
	var patterns;			// Образцы выгрузок
	var advertise;			// Редактируемый информер
	
	/** Отрисовка информера с текущими настройками */
	function render() {		
		var o = advertise.options;
		o.Main.borderColor = $("#borderColor").val();
		o.Main.backgroundColor = $("#backgroundColor").val();
		o.Header.fontColor = $("#headerColor").val();
		o.Description.fontColor = $("#descriptionColor").val();
		o.Cost.fontColor = $("#priceColor").val();
		o.Header.fontUnderline = $("#headerUnderline").attr('checked');
		o.Nav.color = $("#arrowColor").val();
		o.Nav.backgroundColor = $("#arrowBgColor").val();
		o.Nav.logoColor = $("#logo-color").val();
		
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
				advertise.options = patterns[i].options;
				$("#admakerPreview").hide();			
				render();
				$("#admakerPreview").fadeIn();
				advertise.title = title + ', ' + lead0(d.getDate()) + '.' + lead0(d.getMonth() + 1) + '.' + d.getFullYear();
				$("#edit-informer-title").val(advertise.title);
				$("#informer-title").text(advertise.title);
				break;
			}
		};
	}
	
	/** Редактирование названия информера*/
	$('#edit-informer-title').keyup(function(){
		advertise.title = $(this).val();
		$("#informer-title").text(advertise.title); 
	})
	
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
	}


	function displayMessage(message) {
		$("#error-message").show().text(message).fadeOut(2500);
	}
	
	/** Сохранение информера */
	function save() {
		var result = TrimPath.processDOMTemplate("styleTemplate", advertise.options);
		var items = [];
		for (var i=0; i<advertise.options.Main.itemsNumber; i++)			// Шаблонизатор не умеет делать циклы по счётчику :(
			items.push(i);
		result += TrimPath.processDOMTemplate("contentTemplate", {items: items});
		advertise.non_relevant = advertise.non_relevant || {};
		advertise.non_relevant.action = $("#non-relevant").val();
		if (advertise.non_relevant.action == 'usercode')
			advertise.non_relevant.usercode = $('#user-code').val();
		else 
			advertise.non_relevant.usercode = '';

		$.ajax({
			url: '/advertise/save' + (advertise.guid? '?adv_id='+advertise.guid : '') ,
			type: 'POST',
			data: JSON.stringify({
				title: advertise.title,
				options: advertise.options,
				css: TrimPath.processDOMTemplate("styleTemplate", advertise.options),
				nonRelevant: advertise.non_relevant
			}),
			cache: false,
			dataType: 'json',
			contentType: "application/json; charset=utf-8",
			beforeSend: function() {
				$("#saveButton").attr("disabled", true);
			},
			success: function (result) {
				if (result.error == false && result.id) {
					advertise.guid = result.id;
					generateScriptCode(advertise.guid);
					$("#div-informer-code").fadeIn();
					displayMessage("Изменения успешно сохранены.");
				} else {
					if (result.error && result.error.message)
						displayMessage("Ошибка сохранения информера: " + result.error.message);
					else
						displayMessage("Ошибка сохранения информера!");
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
		render();
	})
	
	/** Устанавливает цвет */
	function setColor(selector, value) {
		$(selector).parent().parent().find('.testColor')
			.css("background-color", '#' + value)
			.ColorPickerSetColor(value);
		$(selector).val(value);
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
		} else {
			// Редактирование существующей выгрузки
			loadOptions(advertise.options);
			$("#informer-title").text(advertise.title);
			$("#edit-informer-title").val(advertise.title);
			$("#palette-preset").val('none');
			generateScriptCode(advertise.guid);
			var action = (advertise.non_relevant && advertise.non_relevant.action) || 'social';
			switch (action) {
				case 'usercode':
					setNonRelevantAction('usercode');
					$("#user-code").val(advertise.non_relevant.usercode);
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
