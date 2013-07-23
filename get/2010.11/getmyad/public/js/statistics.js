/**
 * 	Вспомогательные методы для работы с графиками
 */
var isAdvertiseChartEnabled = {};			// Словарь отмеченных выгрузкок {title: true|false}
var plotOptions = {
	series: {
		points: {show: true},
		lines: {show: true}
	},
	grid: {
		hoverable: true,
	    backgroundColor: { colors: ["#fff", "#e7e7e7"] },
		mouseActiveRadius: 15
	},
	xaxis: { 
		mode: "time",
		monthNames: ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'],
		timeformat: '%d %b'
	},
	legend: {
		noColumns: 1,
		labelFormatter: function(label, series) {
			var enabled = 'isAdvertiseChartEnabled["' + label + '"]';
			var res = "<input type='checkbox' ";
			if (isAdvertiseChartEnabled[label]) res += 'checked ';
			res += "onclick='" + enabled + " = !" + enabled + "; drawChartUsingFilter(); '/>" + label;
			return res; 
		},
		container: "#chartLegend"
	}
};	

// Строит графики c учётом выставленных параметров
function drawChartUsingFilter() {
	var data = [];
	$.each(chartData, function(index, one) {
		if (isAdvertiseChartEnabled[one.adv.domain + ', ' + one.adv.title])
			data.push({
				label: one.adv.domain + ', ' + one.adv.title,
				data: one.data
			});
		else
			data.push({
				label: one.adv.domain + ', '+ one.adv.title,
				data: []
			});
	});
	$.plot($("#chart"), data, plotOptions);		
}
/*********************************************************************************/



$(document).ready(function() {
	var dateRangeParams = {};
		
	/**
	 * Создание пользовательского интерфейса
	 */	
	function prepareUi() {
		// Сводный отчёт по всем рекламным выгрузкам
		$("#tableAllAdvertise").jqGrid({
            datatype: function(postdata) {
				this.addJSONData(summaryReportData);
			},
            mtype: 'GET',
            colNames: ['Площадка', 'Показов', 'Переходов', 'Уникальных',
                    'CTR', 'CTR уникальных', 'Цена средняя', 'Сумма'],
            colModel: [
              { name: 'Title', index: 'Площадка', width: 200, align: 'left', sortable: false },
              { name: 'Impressions', index: 'Показов', width: 90, align: 'center', sortable: false },
              { name: 'RecordedClicks', index: 'Переходов', width: 90, align: 'center', sortable: false },
              { name: 'UniqueClicks', index: 'Уникальных переходов', width: 95, align: 'center', sortable: false },
              { name: 'CTR', index: 'CTR', width: 60, align: 'center', sortable: false },
              { name: 'CTR_Unique', index: 'CTR уникальных переходов', width: 105, align: 'center', sortable: false},
			  { name: 'Cost', index: 'Cost', width: 100, align: 'center', sortable: false},
			  { name: 'Summ', index: 'Summ', width: 100, align: 'center', sortable: false},
			  ],
            caption: "Статистика по всем рекламным площадкам",
            footerrow: true,
            userDataOnFooter: true,
			rownumbers: true,
			height: 'auto',
			rownumWidth: 40,
			rowNum:30,
			forceFit: true,
			multiselect: false,
			subGrid: true,
			subGridRowExpanded: function(subgrid_id, row_id) {
				var subgrid_table_id = subgrid_id + "_t";
				var pager_id = "p_" + subgrid_table_id;
				$('#' + subgrid_id).html('<table id="' + subgrid_table_id + '" class="scroll"></table><div id="'
										+ pager_id + '" class="scroll"></div>');
				var url = '/advertise/daysSummary?'+ dateRangeParams + '&adv=' + row_id ;
				
				$("#" + subgrid_table_id).jqGrid({
		            url: url,
		            datatype: 'json',
		            mtype: 'GET',
		            colNames: ['Дата', 'Показов', 'Переходов', 'Уникальных',
		                    'CTR', 'CTR уникальных', 'Цена средняя', 'Сумма'],
		            colModel: [
		              { name: 'Title', index: 'Дата', width: 200, align: 'center', sortable: false, classes: 'subgrid_cell' },
		              { name: 'Impressions', index: 'Показов', width: 90, align: 'center', sortable: false, classes: 'subgrid_cell' },
		              { name: 'RecordedClicks', index: 'Переходов', width: 90, align: 'center', sortable: false, classes: 'subgrid_cell' },
		              { name: 'UniqueClicks', index: 'Уникальных', width: 95, align: 'center', sortable: false, classes: 'subgrid_cell' },
		              { name: 'CTR', index: 'CTR', width: 60, align: 'center', sortable: false, classes: 'subgrid_cell' },
		              { name: 'CTR_Unique', index: 'CTR уникальных переходов', width: 105, align: 'center', sortable: false, classes: 'subgrid_cell' },
					  { name: 'Cost', index: 'Cost', width: 95, align: 'center', sortable: false, classes: 'subgrid_cell' },
					  { name: 'Summ', index: 'Summ', width: 90, align: 'center', sortable: false, classes: 'subgrid_cell' }
					  ],
					pager: pager_id,
					beforeSelectRow: function(rowid, e) {
						return false;
					}

				})
			},
			subGridRowColapsed: function(subgrid_id, row_id) {
			}
        });
		
		
		// Статистика, разбитая по датам
		$("#tableStatsByDays").jqGrid({
            url: '/advertise/daysSummary',
            datatype: 'json',
            mtype: 'GET',
            colNames: ['Дата', 'Показов', 'Переходов', 'Уникальных',
                    'CTR', 'CTR уникальных'],
            colModel: [
              { name: 'Title', index: 'Дата', width: 100, align: 'center', sortable: false },
              { name: 'Impressions', index: 'Показов', width: 90, align: 'center', sortable: false },
              { name: 'RecordedClicks', index: 'Переходов', width: 90, align: 'center', sortable: false },
              { name: 'UniqueClicks', index: 'Уникальных', width: 95, align: 'center', sortable: false },
              { name: 'CTR', index: 'CTR', width: 100, align: 'center', sortable: false },
              { name: 'CTR_Unique', index: 'CTR уникальных', width: 100, align: 'center', sortable: false}],
//            viewrecords: true,
            caption: "Статистика за каждый день по всем рекламным площадкам",
      			gridview: true,
      			rownumbers: true,
      //			height: 'auto',
      			rownumWidth: 40,
      			rowNum:30,
      			forceFit: true,
      			hiddengrid: true,
      			pager: "#pagerStasByDays"
        });
		
		
		
		// Операции со счётом: приход
		$("#tableAccountIncome").jqGrid({
            url: '/private/accountIncome',
            datatype: 'json',
            mtype: 'GET',
            colNames: ['Дата', 'Уникальных переходов', 'Средняя цена', 'Сумма'],
            colModel: [
              { name: 'Date', index: 'Date', width: 90, align: 'center', sortable: false },
              { name: 'Unique', index: 'Unique', width: 120, align: 'center', sortable: false },
              { name: 'Cost', index: 'Cost', width: 100, align: 'center', sortable: false },
              { name: 'Summ', index: 'Summ', width: 100, align: 'center', sortable: false}],
            caption: "Начисления на счёт",
      			gridview: true,
      			rownumbers: true,
      			rownumWidth: 40,
      			rowNum: 20,
      			forceFit: true,
      			pager: "#pagerAccountIncome"
        });
		
		// Операции со счётом: вывод денег
		$("#tableAccountMoneyOut").jqGrid({
            url: '/private/moneyOutHistory',
            datatype: function(postdata) {
				this.addJSONData(moneyOutHistory);
			},
            mtype: 'GET',
            colNames: ['Дата', 'Тип платежа', 'Сумма', 'Примечания'],
            colModel: [
              { name: 'Date', index: 'Date', width: 80, align: 'center', sortable: false },
              { name: 'PaymentType', index: 'PaymentType', width: 120, align: 'center', sortable: false },
              { name: 'Summ', index: 'Summ', width: 100, align: 'center', sortable: false},
			        { name: 'Comment', index: 'Comment', width: 200, align: 'center', sortable: false}],
            caption: "Вывод денег",
			      gridview: true,
			      rownumbers: false,
      			rowNum:30,
			      forceFit: true,
			      toolbar: [true, 'top'],
			      pager: "#pagerAccountMoneyOut",
			      beforeSelectRow: function(rowid, e) {				
      				if (rowid){					
      					if($("#tableAccountMoneyOut").getRowData(rowid)['Comment'] == "заявка обрабатывается...")
      					     buttonRejectMoneyOutRequest.attr('disabled', false);
      					else
            				 buttonRejectMoneyOutRequest.attr('disabled', true);
      					}
      				return true;
    			  }
        });	
        
        $("#managersSummary").jqGrid('navGrid', '#toolbarMoneyOutRequest', {edit:false, add:false, del: false});
        var buttonRejectMoneyOutRequest = $("<input type='button' id='btnRejectMoneyOut' value='Отозвать заявку'/>");
        buttonRejectMoneyOutRequest.attr('disabled', true).click(function() {         
           $("#dialogCancelRequest").dialog('open');
        });   
        $("#t_tableAccountMoneyOut").append(buttonRejectMoneyOutRequest);   
//--------------------------------------------------------------------------------------
  
		// Список существующих информеров (для редактирования)
		$("#tableExistingInformers").jqGrid({
		  // url: 'private/accountDomains',
		  // datatype: 'json',
			datatype: function(postdata) {
				this.addJSONData(domains);
				for (var i = 0; i < $("#tableExistingInformers").getGridParam("reccount"); i++) 
					if ($("#tableExistingInformers").getCell(i + 1, 'Domain') == '') {
						$("#tableExistingInformers").setCell(i + 1, 'Domain', 'Информеры, не привязанные к домену');
					}
				
			},
            mtype: 'GET',
			height: 'auto',
			colNames: ['Сайт'],
			colModel: [{ name: 'Domain', index: 'Domain', width: 465}],
			caption: "Список существующих информеров",
			rownumbers: true,
			//pager: "#pagerExistingInformers",
			subGrid: true,
			subGridBeforeExpand: function(subgrid_id, row_id) {
				var index = $("#tableExistingInformers").jqGrid('getRowData', row_id).Domain.indexOf('ожидает подтверждения', 0);
				if (index != -1) return false;	
			},
			subGridRowExpanded: function(subgrid_id, row_id) {
				var subgrid_table_id = subgrid_id + "_t";
				var pager_id = "p_" + subgrid_table_id;
				$('#' + subgrid_id).html('<table id="' + subgrid_table_id + '" class="scroll"></table><div id="'
										+ pager_id + '" class="scroll"></div>');
				var row = $("#tableExistingInformers").jqGrid('getRowData', row_id);
				if (row.Domain == 'Информеры, не привязанные к домену')
					domain = '';
				else domain = row.Domain	
				var url = '/advertise/domainsAdvertises?domain=' + domain;
				$("#" + subgrid_table_id).jqGrid({
		            url: url,
					height: 'auto',
		            datatype: 'json',
		            mtype: 'GET',
		            colNames: ['Информер', ''],
		            colModel: [
		              { name: 'Title', index: 'Title', width: 340, align: 'center', sortable: false, classes: 'subgrid_cell' },
		              { name: 'Guid', index: 'Guid', width: 100, align: 'center', sortable: false, classes: 'subgrid_cell' },
					  ],
					//pager: pager_id,
					beforeSelectRow: function(rowid, e) {
						return false;
					}
					,
					loadComplete: function() {
						for (var i = 0; i < $("#" + subgrid_table_id).getGridParam("reccount"); i++) 
							$("#" + subgrid_table_id).setCell(i + 1,'Guid','<a href="/advertise/edit?ads_id=' + $("#" + subgrid_table_id).getCell(i + 1,'Guid') + '#size">Править</a>');
							
							
					}

				})
			}

		});
	
						
		var datePickerOptions = {
			duration: '',
			onSelect: function(dateText, inst) {
				refreshData();
			}
		}
		
		$("#dateStart").datepicker(datePickerOptions).datepicker('hide');
		$("#dateEnd").datepicker(datePickerOptions).datepicker('hide');
		$("#dateFilterOneDay").datepicker(datePickerOptions).datepicker('hide');
		
		
		
		// Строим графики. Изначально показываем все выгрузки
		for (i=0; i<advertiseList.length; i++)
			isAdvertiseChartEnabled[advertiseList[i].domain + ', ' + advertiseList[i].title] = true;
			 //+ ' ' +one.adv.domain
		drawChartUsingFilter();

		function showTooltip(x, y, contents) {
	        $('<div id="tooltip">' + contents + '</div>').css( {
	            position: 'absolute',
	            display: 'none',
	            top: y + 10,
	            left: x + 10,
	            border: '1px solid #fdd',
	            padding: '2px',
	            'background-color': '#fee',
	            opacity: 0.80
	        }).appendTo("body").show();
		}
		var prevPoint = null;
		$("#chart").bind("plothover", function (event, pos, item) {
			if (item) {
				if (prevPoint == item.datapoint) 
					return;
				prevPoint = item.datapoint;
				$("#tooltip").remove();
				var y = item.datapoint[1].toFixed(0);
				var dt = new Date(item.datapoint[0]);
				var monthNames = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
				showTooltip(item.pageX, item.pageY,
					"<p style='text-align: center; font-weight: bold; margin: 0'>" + item.series.label + "</p>" +
					"Уникальных: " + y + "<br />" +
					"Дата: " +  dt.getDate() + " " + monthNames[dt.getMonth()] + " " + dt.getFullYear() );
			}
			else {
				$("#tooltip").remove();
				prevPoint = null;
			}
		});


		$("#tabs").tabs();
		$("#tabs>ul>li:last-child").attr('style', 'position: absolute; right: 10px; top:5px');	// Отодвигаем вкладку "Помощь" вправо
		

		$("#showGrowingInfo, #showGrowingInfo2").click(function() {
			$("#tabs").tabs("select", 3);
			nextContents();
			return false;
		});
		
		$("#btnRegisterDomain").click(function() {
			$("#dialogRegisterDomain").dialog('open');
		});
		
		
		$("#removeUploadFactura").hide();
		$("#removeUploadFactura").click(
		  function() {
  		  $.getJSON("/private/removeUploadFactura", 
    		  function(data) {
    		    if (data.error) {
    		      if (data.msg)
    		        $("#moneyOut_errorMessage").html(data.msg);
    		      else
    		         $("#moneyOut_errorMessage").html('Ошибка удаления файла!');
    		    }
    		    else {
    		      $("#removeUploadFactura").hide();
    		      $("#uploadButton").show();
    		      $('#factura_files').text('');
    		    }
    		  }
  		);
  	 }	
		);
		
		
          new Ajax_upload('uploadButton', {
            action: "/private/uploadFactura",
            responseType: "json",
            onSubmit : function(file , ext){
              $('#uploadButton').text('Загружается ' + file);
              this.disable(); 
            },
            onComplete : function(file, response){
              if (response.error) {
                $('#factura_files').text('Ошибка добавления файла!');
                $("#moneyOut_wait").hide();
                $('#uploadButton').text('Добавить счёт-фактуру');
                $('#uploadBUtton').show();
                $('#removeUploadFactura').hide();
              } 
              else {
                this.enable();
                $('#uploadButton').hide();
                $('#uploadButton').text('Добавить счёт-фактуру');
                $('#removeUploadFactura').show();
                $("#moneyOut_wait").hide();
                $('#factura_files').text(file);
              }
            }   
          });
 

	}  // end prepareUi()
	
	// -----------------------------------------
	
	
	
		
	/*
	 * Перезагружает таблицу доменов/информеров
	 */	
/*	   function reloadTableExistingInformers() {
      $('#tableExistingInformers')
        .jqGrid('setGridParam',{datatype: "json"})
        .jqGrid('setGridParam',{url: "private/accountDomains"})
        .trigger("reloadGrid");
  }
*/		

/* В диалоге вывода средств отображение полей в соответствии с типом вывода средств*/
  function showRightMoneyOutBlock(){
                var val = $("#moneyOut_paymentType").val();
                switch (val) {
                  case 'card':
                    $("#moneyOut_card").show()
                    $("#moneyOut_webmoney").hide();
                    $("#moneyOut_factura").hide();
                    $("#moneyOut_errorMessage").html('');
                    $("#moneyOut_linkHelp").hide('');
                    break;
                  case 'webmoney_z':
                    $("#moneyOut_webmoney").show();
                    $("#moneyOut_factura").hide();
                    $("#moneyOut_card").hide();
                    $("#moneyOut_errorMessage").html('');
                    $("#moneyOut_linkHelp").show('');
                    break;
                  case 'factura' :
                    $("#moneyOut_factura").show();
                    $("#moneyOut_webmoney").hide();
                    $("#moneyOut_card").hide();
                    $("#moneyOut_errorMessage").html('');
                    $("#moneyOut_linkHelp").hide('');
                    break;  
                  default:
                    $("#moneyOut_webmoney").show();
                    $("#moneyOut_banking").hide();
                    $("#moneyOut_card").hide();
                    $("#moneyOut_errorMessage").html('');
                    $("#moneyOut_linkHelp").show('');
                    break;
                }
               }
               showRightMoneyOutBlock();
              
              $("#moneyOut_paymentType").change(function() {
                showRightMoneyOutBlock();
              });
              
/*----------------------------------------------*/        


	/**
	 * Обновляет данные с учётом текущих настроек фильтров.
	 */				
	function refreshData()
	{
		var params = '';					// Параметры запроса
		
		var filterPreset = document.getElementById("filterpreset");
		var dayStart = new Date();
		var dayEnd = new Date();
		var today = new Date();

		switch (filterPreset.options[filterPreset.selectedIndex].value) {
			case 'today':
				dayEnd = dayStart = today;
				break;
			case 'yesterday':
				dayStart.setDate(today.getDate() - 1);
				dayEnd = dayStart;
				break;
			case 'thisweek':
				//						dayStart.setDate(today.getDate() - 1)
				break;
			case 'lastweek':
				dayStart.setDate(today.getDate() - 7);
				dayEnd = today;
				break;
			case 'lastmonth':
				dayStart.setDate(today.getDate() - 30);
				dayEnd = today;
				break;
			case 'range':
				dayStart = $('#dateStart').val();
				dayEnd = $('#dateEnd').val();
				break;
			case 'oneday':
				dayStart = dayEnd = $('#dateFilterOneDay').val();
				break;
			case 'off':
				dayStart = dayEnd = '';
			default:
				break;
		}	

		// Форматирует дату для передачи серверу
		function formatDate(date) {
			if (!date.getMonth)
				return date;
			var m = date.getMonth()+1;
			var d = date.getDate();
			return (d<10? "0" + d : d) + '.' + (m<10? "0" + m : m) + "." + date.getFullYear() ;
		}
		
		dayStart = formatDate(dayStart);
		dayEnd = formatDate(dayEnd);
		
		dateRangeParams = $.param({
			'dateStart': dayStart,
			'dateEnd': dayEnd
		});
		params = dateRangeParams;

		// Обновляем таблицу статистики всех выгрузок
		$('#tableAllAdvertise')	.jqGrid('setGridParam',{datatype: "json"})
								.jqGrid('setGridParam',{url: "/advertise/allAdvertises?" + params})
								.trigger("reloadGrid");
		// Показываем выбранный диапазон на графике
		var date1 = null, //new Date(2000,0,0),
			date2 = null; //new Date(2020,0,0);
		if (dayStart != '')
			date1 = new Date(Number(dayStart.slice(6,10)),
							 Number(dayStart.slice(3,5)) - 1,
							 Number(dayStart.slice(0,2)))
		if (dayEnd != '')
			date2 = new Date(Number(dayEnd.slice(6,10)),
							 Number(dayEnd.slice(3,5)) - 1,
							 Number(dayEnd.slice(0,2)))
							 
		if (date1 && date2 && (date2-date1 < 1000*60*60*24*7))
			date1.setDate(date2.getDate() - 7);
		
		var utc = (new Date()).getTimezoneOffset() * 60000;
		plotOptions.xaxis.min = date1? date1.getTime() + utc : null;
		plotOptions.xaxis.max = date2? date2.getTime() + utc : null;
		drawChartUsingFilter();


	} // end refreshData()
	

	
	
	/** Выбор пресета фильтра */
	$("#filterpreset").change(function () {
		var o = $("#filterpreset");
		var val = o.val();
		if (val == "range") {
			$("#filterByRangeOptions").show();
			$("#filterByOneDayOptions").hide();
		}
		else if (val == "oneday") {
			$("#filterByOneDayOptions").show();
			$("#filterByRangeOptions").hide();
		}
		else {
			$("#filterByOneDayOptions").hide();
			$("#filterByRangeOptions").hide();
		}
		refreshData();
	}); // end filterpreset.click()

	/** Изменяет значения поля ввода даты на daysOffset дней */			
	function changeDatePickerBy(input, daysOffset) {
		var dateFormat = input.datepicker('option', 'dateFormat');
		var date = new Date();
		try {
			date = $.datepicker.parseDate(dateFormat, input.val());
			date.setDate(date.getDate() + daysOffset);
		} catch (e) {
			date = new Date();
		}
		input.datepicker('setDate', date);
	}
	
	$("#setPrevDay").click(function() {
		changeDatePickerBy($('#dateFilterOneDay'), -1);
		refreshData();
	});
	$("#setNextDay").click(function() {
		changeDatePickerBy($('#dateFilterOneDay'), +1);
		refreshData();
	});

	/** Перезагружает таблицу истории вывода денежных средств */
	function reloadMoneyOutHistoryGrid() {
 		$('#tableAccountMoneyOut')
			.jqGrid('setGridParam',{datatype: "json"})
			.jqGrid('setGridParam',{url: "/private/moneyOutHistory"})
			.trigger("reloadGrid");
	}
	
	/**
	 * Форма заявки на вывод денежных средств. 
	 */
	 
	var ua = navigator.userAgent.toLowerCase();
  var isChrome = (ua.indexOf("chrome") != -1);
 
	 
	 
	$("#moneyOut").dialog({
		autoOpen: false,
		width: 450,
		height: 'auto',
		resizable: false,
		modal: !isChrome,
		title: 'Заявка на вывод средств',
		open: function(event, ui) {
			$("#moneyOut_errorMessage").html('');
			$("#moneyOut_summ").val(Math.round(accountSumm - 0.5).toString()).focus();
			$("#moneyOut_cardSumm").val(Math.round(accountSumm - 0.5).toString()).focus();
			$("#moneyOut_facturaSumm").val(Math.round(accountSumm - 0.5).toString()).focus();
			$("#moneyOut_comment").val('');
		},
		buttons: {
			'Отправить заявку': function() {
				$('#moneyOut_form').ajaxSubmit({
					dataType: 'json',
					beforeSubmit: function() {
						$("#moneyOut_wait").show();
					},
					success: 
					    function(reply) {
                if (reply.error) {
			             if (reply.error_type == "authorizedError")
				               window.location.replace("/");
                   else if (reply.msg)
				               $("#moneyOut_errorMessage").html(reply.msg);
			             else
				               $("#moneyOut_errorMessage").html("Неизвестная ошибка.");
                }
						    else {
							     $("#moneyOut").dialog('close');
		               $("<div>" +
					   	 "<span style=\"float:left; margin:0 7px 50px 0;\"><img src=\"/img/info-icon.png\" /></span>" +
						 "<b>Заявка успешно принята!</b><br/>" + 
						 "<p>На ваш e-mail поступит ссылка подтверждения данной заявки. " + 
						 "Заявка должна быть одобрена в течение трёх дней.</p></div>").dialog({
		                      modal: true,
		                      resizable: false,
		                      buttons: {OK: function() {
		                        	reloadMoneyOutHistoryGrid();
		                      	$(this).dialog('close');
		                      }}
		                    });
						    } 
					},
					complete: function() {
						$("#moneyOut_wait").hide();
					}
				})
			},
			'Отмена': function() {
				$(this).dialog('close');
				$("#removeUploadFactura").hide();
				$("#uploadFactura").show();
				$('#factura_files').text('');
				$.getJSON("/private/removeUploadFactura?location=" + $("#moneyOut_facturaLocation").val());
			}
		}
	});
	
	
	$(".linkMoneyOut").click(function() {
		$("#moneyOut").dialog('open');
		
		
			 var val = $("#moneyOut_paymentType").val();
		switch (val) {
			case 'card':
				$("#moneyOut_card").show()
				$("#moneyOut_webmoney").hide();
				$("#moneyOut_factura").hide();
				$("#moneyOut_errorMessage").html('');
				$("#moneyOut_linkHelp").hide('');
				break;
			case 'webmoney_z':
				$("#moneyOut_webmoney").show();
				$("#moneyOut_card").hide();
				$("#moneyOut_factura").hide();
				$("#moneyOut_errorMessage").html('');
				$("#moneyOut_linkHelp").show('');
				break;
			case 'factura' :
			  $("#moneyOut_factura").show();
        $("#moneyOut_card").hide();
        $("#moneyOut_webmoney").hide();
        $("#moneyOut_errorMessage").html('');
        $("#moneyOut_linkHelp").hide('');
        break;
			default:
				$("#moneyOut_webmoney").show();
				$("#moneyOut_card").hide();
				$("#moneyOut_errorMessage").html('');
				$("#moneyOut_linkHelp").show('');
				break;
		}
	});
	
	
	$('.dialog').find('input').keypress(function(e) {
		if ((e.which && e.which == 13) || (e.keyCode && e.keyCode == 13)) {
			$(this).parent().parent().parent().parent().find('.ui-dialog-buttonpane').find('button:first').click(); /* Assuming the first one is the action button */
			return false;
		}
	});
	
	
	/**
	 * Диалог заявки на регистрацию нового домена
	 */
	$("#dialogRegisterDomain").dialog({
		modal: true,
		autoOpen: false,
		resizable: false,
		buttons: {
			'Отправить заявку': function() {
				$("#formRegisterDomain").ajaxSubmit({
					dataType: 'json',
					beforeSubmit: function() {
						$("#registerDomain_errorMessage").html('');
						$('#registerDomain_wait').show();
					},
					success: function(reply) {
						if (reply.error === false) {
							$('#dialogRegisterDomain').dialog('close');
							$("<p>Заявка успешно принята!</p>").dialog({
								modal: true,
								resizable: false,
								buttons: {OK: function() {
									$(this).dialog('close');
								}}
							});
							// перезагрузить таблицу
							$("#tableExistingInformers").trigger("reloadGrid");
//							reloadTableExistingInformers();
							return;
						}
						else if (reply.error) {
						  if (reply.error_type == "authorizedError")
						    window.location.replace("/main/index");
						  else {
						    if (reply.msg)
						      var message = reply.msg;
                else 
                  var message = 'Неизвестная ошибка подачи заявки. Попробуйте позже.'
                $("#registerDomain_errorMessage").html(message);    
						 }    
						}
					},
					complete: function() {
						$('#registerDomain_wait').hide();
					}
				});
			}
		}
	});
	
	/**
	 * Диалог отмены заявки на вывод средств
	 */
    $("#dialogCancelRequest").dialog({
        autoOpen: false,
        modal: true,
        buttons: {
            "Да": function(){
                var table = $("#tableAccountMoneyOut");
                var id = table.jqGrid('getGridParam', 'selrow');
                var token = document.getElementById('token').value;
                $.getJSON("/private/moneyOutRemove",
                          {id: id,
                           token: token},
                          function(result) {
                            if (result.error) { 
                              if (result.error_type == 'authorizedError') 
                                window.location.replace("/main/index");
                            }
                            else {
      						              reloadMoneyOutHistoryGrid();
                                $("#dialogCancelRequest").dialog("close");
                            }
                          }
                );
                $("#btnRejectMoneyOut").attr('disabled', true);
            },
            "Отмена": function(){
                $(this).dialog("close");
            }
        }
    });
//----------------------------------------
/* example4 */
  $("#moneyOut").dialog({ autoOpen: false });
  
  
  $('#open_dialog').click(function(){
    $("#moneyOut").dialog("open");
    return false; 
  }); 


//----------------------------------------
  

	prepareUi();
	$("#tabs").css("visibility", "visible");
	showRightMoneyOutBlock();
//если меньше 1!
	if(advertiseList.length<1){
		//$("#linkmain").css({display:'none'});
		//$("#linkaccount").css({display:'none'});
		$("#tableExistingInformers").css({display:'none'});	
		$("#tableInformers").css({display:'none'});		
		$("#startwork").css({display:'block'});
		//$('tableExistingInformers').jqGrid()	
		$("#linkinformers").click();		
	};

	
});	// end onDocumentReady
