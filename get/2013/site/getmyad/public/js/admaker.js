function AdMaker()
{
	Array.prototype.has = function(value) {
		for (var i=0; i<this.length; i++)
			if (this[i] == value)
				return true;
		return false;
	}
	
	function createColorPicker(selector){
		$(selector).ColorPicker({
			color: '#0000ff',
			onShow: function(colpkr){
				$(colpkr).fadeIn(200);
				return false;
			},
			onHide: function(colpkr){
				$(colpkr).fadeOut(200);
				return false;
			},
			onChange: function(hsb, hex, rgb){
				$(selector).css('color', '#' + hex);
				$(selector).val(hex);
				render();
			}
		}).bind('keyup', function(){
			$(this).ColorPickerSetColor(this.value);
		})		
	}
	
	/**
	 * Создаёт аккордион настроек
	 */
	function createOptionsSelector() {
		function blockOptions(selector, group) {
			$(selector).append('<div><span class="optionsGroup">Размер:</span>' +
						' <span>	ширина <input type="text" onkeyup="admaker.render()" id="width' + group + '" value="auto" size="4" />' +
						' высота <input type="text" onkeyup="admaker.render()" id="height' + group + '" value="auto" size="4" /> </span> ' + 
						' <br style="clear: both" />' +
						'<span class="optionsGroup"> Граница: </span> ' +
						'<span> цвет <input type="text" id="borderColor' + group + '" value="000000" size="6" />'+
						'ширина: <input type="text" onkeyup="admaker.render()" id="borderWidth' + group + '" value="0" size="1" /> </span>' +
						'<br style="clear: both" />' + 
						'<span class="optionsGroup">Положение:</span>' +
						'<span>слева <input type="text" id="left' + group + '" value="0" size="5" />' +
							 'сверху <input type="text" id="top' + group + '" value="0" size="5"/> </span>' +
						'<br style="clear: both" />' +
						'<span class="optionsGroup">Спрятать:</span>' +
								'<input type="checkbox" onchange="admaker.render()" id="hide' + group + '" value="hide"/> </span>' +
						'<br style="clear: both" />' +
						'<span class="optionsGroup">Выравнивание:</span>' +
						'	<select onchange="admaker.render()" id="align' + group + '" name="align' + group + '"> ' +
						'	<option value="center">по центру</option>' + 
						'	<option value="left">слева</option>' + 
						'	<option value="right">справа</option>' + 
						'	</select>' + 
						'<br style="clear: both" />' +
					'</div>');
					

			createColorPicker('#borderColor' + group);
		}
		
		function fontOptions(selector, group) {
			$(selector).append(
						'<span class="optionsGroup">Шрифт:</span>' +
						'<span>цвет <input type="text" onkeyup="admaker.render()" id="fontColor' + group + '" value="000000" size="6" />' +
							 'размер <input type="text" onkeyup="admaker.render()" id="fontSize' + group + '" value="12" size="2"/> ' +
							 '<b>b</b> <input type="checkbox" onchange="admaker.render()" id="fontBold' + group + '" value="true"/> </span>' + 
							 '<u>u</u> <input type="checkbox" onchange="admaker.render()" id="fontUnderline' + group + '" value="true"/> </span>' + 
						'<span class="optionsGroup">. </span>' +
						'	<select onchange="admaker.render()" id="fontFamily' + group + '" name="fontFamily' + group + '"> ' +
						'	<option value=\'Arial, "Helvetica CY", "Nimbus Sans L", sans-serif;\'>Arial</option>' + 
						'	<option value=\'Verdana, "Geneva CY", "DejaVu Sans", sans-serif;\'>Verdana</option>' + 
						'	<option value=\'"Times New Roman", "Times CY", "Nimbus Roman No9 L", serif;\'>Times New Roman</option>' + 
						'	</select>' + 
						'<br style="clear: both" />');
			createColorPicker('#fontColor' + group);
		}
		
		function loadOptions(options) {
			for (var group in options) {
				for (var o in options[group]) {
					var edit = document.getElementById(o + group);
					var newValue = options[group][o];
					if (edit && edit.value)
						edit.value = newValue;
					if (edit && (newValue === true))
						edit.checked = true;
				}
			}
		}
		
		blockOptions("#mainOptions", 'Main', render);
		$("#mainOptions").append('<span>цвет фона<input type="text" id="backgroundColorMain" value="ffffff" size="6" /></span>');
		$("#mainOptions").append('<span>кол-во предложений<input type="text" onkeyup="admaker.render()" id="itemsNumberMain" value="6" size="2" /></span>');
        var checked = '';
        if (attractorChecked) checked = 'checked';
		$("#mainOptions").append('<br/><span>Отслеживать в Attractor: <input id="trackAttractor" name="trackAttractor" type="checkbox" '+checked+'/></span>');

		createColorPicker("#backgroundColorMain");
		
		blockOptions('#advertiseOptions', 'Advertise');
		
		blockOptions('#headerOptions', 'Header');
		fontOptions('#headerOptions', 'Header');
		
		blockOptions('#descriptionOptions', 'Description');
		fontOptions('#descriptionOptions', 'Description');
		
		blockOptions('#costOptions', 'Cost');
		fontOptions('#costOptions', 'Cost');
		
		blockOptions('#imageOptions', 'Image');

		$("#navOptions").append(
						'<br style="clear: both" />' +
						'<span class="optionsGroup">Стрелка:</span>' +
						'<span>цвет<input type="text" id="colorNav" value="ffffff" size="6" /></span>' + 
						'<span>фон<input type="text" id="backgroundColorNav" value="7070ff" size="6" /></span>' +
						'<select onchange="admaker.render()" id="navPositionNav" name="navPositionNav"> ' +
						'<option value="top-left">слева вверху</option>' + 
						'<option value="bottom-left">слева внизу</option>' + 
						'<option value="top-right">справа вверху</option>' + 
						'<option value="bottom-right">справа внизу</option>' +
						'</select>' + 
						'<br style="clear: both" />' +
						'<span class="optionsGroup">Логотип:</span>' +
						'<select onchange="admaker.render()" id="logoPositionNav" name="logoPositionNav"> ' +
						'<option value="top-left">слева вверху</option>' + 
						'<option value="bottom-left">слева внизу</option>' + 
						'<option value="top-right">справа вверху</option>' + 
						'<option value="bottom-right">справа внизу</option>' +
						'</select>' + 
						'<select onchange="admaker.render()" id="logoColorNav" name="logoColorNav"> ' +
						'<option value="black">чёрный</option>' + 
						'<option value="color">цветной</option>' + 
						'<option value="blue">синий</option>' + 
						'<option value="white">белый</option>' + 
						'</select>' + 
						'Спрятать: <input type="checkbox" onchange="admaker.render()" id="logoHideNav" value="hide"/>' +
						'<br style="clear: both" />' +
						'<span class="optionsGroup">Время перезагрузки</span>' +
						'<span><input type="text" id="auto_reload" size="6" /></span>' + 
                        '<br style="clear: both" />' +
						'</span');
		createColorPicker("#backgroundColorNav");
		createColorPicker("#colorNav");		
		loadOptions(initialOptions);
		
	}
	
	

	$("#admakerOptions").accordion().draggable();	
	createOptionsSelector();
	$("#refreshButton").click(render);
	$("#printButton").click(function() {
		var data = getData();
	    var result = TrimPath.processDOMTemplate("styleTemplate", data);
		var items = [];
		for (var i=0; i<data.Main.itemsNumber; i++)			// Шаблонизатор не умеет делать циклы по счётчику :(
			items.push(i);
		result += TrimPath.processDOMTemplate("contentTemplate", {
			items: items
		});
		console.log(result);
		console.log(getData());
	});
	
	$("#saveButton").click(function() {
		var data = getData();
		$.ajax({
			url: '/advertise/save?adv_id=' + CurrentAdvertiseId,
			type: 'POST',
			data: JSON.stringify({
				options: data,
				css: TrimPath.processDOMTemplate("styleTemplate", data),
                trackAttractor: $("#trackAttractor").attr("checked")
			}),
			dataType: 'json',
			contentType: "application/json; charset=utf-8",
			success: function (result) {
				if (!result.error)
					alert('OK!');
                else
                    alert("Ошибка сохранения: \n" + result.message);
			} 
		})
	});
	
	
	function getData() {
		function selectedValue(id) {
			var o = document.getElementById(id);
			var value = null;
			try {
				value = o.options[o.selectedIndex].value;
			} catch(e) {
			}
			return value;
		} // end selectedValue()
		
		
		var sections = ["Header", 'Main', 'Advertise', 'Description', 'Cost', 'Image'];
		var data = {};
		for (var i=0; i<sections.length; i++) {
			var group = sections[i];
			data[group] = {
				left:		$('#left' + group).val(),
				top: 		$('#top' + group).val(),
				width: 		$('#width' + group).val(),
				height:		$('#height' + group).val(),
				borderColor:$('#borderColor' + group).val(),
				borderWidth:$('#borderWidth' + group).val(),
				fontColor: 	$('#fontColor' + group).val(),
				fontSize: 	$('#fontSize' + group).val(),
				fontBold:	$("#fontBold" + group).is(":checked"),
				fontUnderline: $("#fontUnderline" + group).is(":checked"),
                fontFamily: $("#fontFamily" + group).val(),
				hide:		$("#hide" + group).is(":checked"),
				align:		$("#align" + group).val()
			};
            if (data[group].fontFamily == 'Verdana, "Geneva CY", "DejaVu Sans", sans-serif;')
                data[group].fontSize -= 2;
		}
		data['Main']['backgroundColor'] = document.getElementById('backgroundColorMain').value;
		data['Main']['itemsNumber'] = document.getElementById('itemsNumberMain').value;
		data['Nav'] = {}
		data['Nav']['backgroundColor'] = document.getElementById('backgroundColorNav').value;
		data['Nav']['color'] = document.getElementById('colorNav').value;
		data['Nav']['navPosition'] = selectedValue('navPositionNav');
		data['Nav']['logoPosition'] = selectedValue('logoPositionNav');
		data['Nav']['logoColor'] = selectedValue('logoColorNav');
		data['Nav']['logoHide'] = $("#logoHideNav").is(":checked");
	
		return data;
	}
	
	
	function render() {
		var data = getData();
	    var result = TrimPath.processDOMTemplate("styleTemplate", data);
		var items = [];
		for (var i=0; i<data.Main.itemsNumber; i++)			// Шаблонизатор не умеет делать циклы по счётчику :(
			items.push(i);
		result += TrimPath.processDOMTemplate("contentTemplate", {items: items});
	    document.getElementById('admakerPreview').innerHTML = result;
		
		var draggableOptions = {
			stop: function(event, ui) {
				var c = ui.helper.attr('class');
				var group = '';
				if (c.indexOf('advHeader') >= 0) 
					group = 'Header';
				if (c.indexOf('advDescription') >= 0) 
					group = 'Description';
				if (c.indexOf('advCost') >= 0)
					group = 'Cost';
				if (c.indexOf('advImage') >= 0) 
					group = 'Image';
				if (group == '') return;
				document.getElementById('top' + group).value = ui.position.top;
				document.getElementById('left' + group).value = ui.position.left;

				render();
			},
			snap: true,
			snapTolerance: 10,
			snapMode: 'inner'
		}	
		$(".advHeader").draggable(draggableOptions);
		$(".advDescription").draggable(draggableOptions);
		$(".advCost").draggable(draggableOptions);
		$(".advImage").draggable(draggableOptions);
		$("#mainContainer").resizable({
			stop: function(event, ui){
				document.getElementById('widthMain').value = ui.size.width + 'px';
				document.getElementById('heightMain').value = ui.size.height + 'px';
				render();
			}
		});
	}
	
	render();
	
	return {
		render: render
	}
}

var admaker = AdMaker();
