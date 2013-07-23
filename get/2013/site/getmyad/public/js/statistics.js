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
	$.each(account_data.chartData, function(index, one) {
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
        $(".spanAccountSumm").html(Math.round(account_data.accountSumm * 100, 2) / 100 + "$");
		// Сводный отчёт по всем рекламным выгрузкам
		// Форматирует дату для передачи серверу
		function formatDate(date) {
			if (!date.getMonth)
				return date;
			var m = date.getMonth()+1;
			var d = date.getDate();
			return (d<10? "0" + d : d) + '.' + (m<10? "0" + m : m) + "." + date.getFullYear() ;
		}
        var dayStart = new Date();
        var dayEnd = new Date();
        var today = new Date();
		dayStart.setDate(today.getDate() - 30);
		dayEnd = today;
		dayStart = formatDate(dayStart);
		dayEnd = formatDate(dayEnd);
		dateRangeParams = $.param({
			'dateStart': dayStart,
			'dateEnd': dayEnd
		});
        var surl = '/advertise/allAdvertises?'+ dateRangeParams;
		$("#tableAllAdvertise").jqGrid({
            datatype: "json",
            url: surl,
            mtype: 'GET',
            colNames: ['Рекламные блоки', 'Показы</br>объявления ', 'Клики по</br>обьявлениям',
            'CTR</br>объявлений', 'Средняя</br>цена</br>обьявлений', 'Сумма за</br>объявления','Показы</br>банеров',
            'Средняя</br>цена</br>банер', 'Сумма за</br>банеры', 'Клики по</br>банерам</br>за клики','Средняя цена</br>банеров</br>за клики',
            'Сумма за</br>банеры</br>по кликам', 'ИТОГО' ],
            colModel: [
              { name: 'Title', index: 'Площадка', width: 200, align: 'left', sortable: false },
              { name: 'Impressions', index: 'Показы', width: 80, align: 'center', sortable: false },
              { name: 'UniqueClicks', index: 'Клики', width: 80, align: 'center', sortable: false },
              { name: 'CTR_Unique', index: 'CTR', width: 90, align: 'center', sortable: false },
			  { name: 'Cost', index: 'Cost', width: 85, align: 'center', sortable: false},
			  { name: 'Summ', index: 'Summ', width: 80, align: 'center', sortable: false},
              { name: 'imp_bannerImpressions', index: 'imp_bannerImpressions', width: 65, align: 'center', sortable: false },
			  { name: 'imp_bannerCost', index: 'imp_bannerCost', width: 70, align: 'center', sortable: false},
			  { name: 'imp_bannerSumm', index: 'imp_bannerSumm', width: 80, align: 'center', sortable: false},
              { name: 'banUniqueClicks', index: 'banUniqueClicks', width: 90, align: 'center', sortable: false, hidden:true },
			  { name: 'bannerCost', index: 'bannerCost', width: 85, align: 'center', sortable: false, hidden:true},
			  { name: 'bannerSumm', index: 'bannerSumm', width: 80, align: 'center', sortable: false, hidden:true},
			  { name: 'allSumm', index: 'allSumm', width: 80, align: 'center', sortable: false},
			  ],
            caption: "Заработок по всем рекламным блокам",
            footerrow: true,
            userDataOnFooter: true,
			rownumbers: false,
			height: 'auto',
            autowidth: true,
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
                    colNames: ['Дата', 'Показы</br>объявления ', 'Клики по</br>обьявлениям',
                    'CTR</br>объявлений', 'Средняя</br>цена</br>обьявлений', 'Сумма за</br>объявления','Показы</br>банеров',
                    'Средняя</br>цена</br>банер', 'Сумма за</br>банеры', 'Клики по</br>банерам</br>за клики','Средняя цена</br>банеров</br>за клики',
                    'Сумма за</br>банеры</br>по кликам', 'ИТОГО' ],
                    colModel: [
                      { name: 'Title', index: 'Дата', width: 200, align: 'left', sortable: false, classes: 'subgrid_cell'},
                      { name: 'Impressions', index: 'Показы', width: 80, align: 'center', sortable: false, classes: 'subgrid_cell'},
                      { name: 'UniqueClicks', index: 'Клики', width: 80, align: 'center', sortable: false, classes: 'subgrid_cell'},
                      { name: 'CTR_Unique', index: 'CTR', width: 90, align: 'center', sortable: false, classes: 'subgrid_cell'},
                      { name: 'Cost', index: 'Cost', width: 85, align: 'center', sortable: false, classes: 'subgrid_cell'},
                      { name: 'Summ', index: 'Summ', width: 80, align: 'center', sortable: false, classes: 'subgrid_cell'},
                      { name: 'imp_bannerImpressions', index: 'imp_bannerImpressions', width: 65, align: 'center', sortable: false, classes: 'subgrid_cell'},
                      { name: 'imp_bannerCost', index: 'imp_bannerCost', width: 70, align: 'center', sortable: false, classes: 'subgrid_cell'},
                      { name: 'imp_bannerSumm', index: 'imp_bannerSumm', width: 80, align: 'center', sortable: false, classes: 'subgrid_cell'},
                      { name: 'banUniqueClicks', index: 'banUniqueClicks', width: 90, align: 'center', sortable: false, hidden:true, classes: 'subgrid_cell'},
                      { name: 'bannerCost', index: 'bannerCost', width: 85, align: 'center', sortable: false, hidden:true, classes: 'subgrid_cell'},
                      { name: 'bannerSumm', index: 'bannerSumm', width: 80, align: 'center', sortable: false, hidden:true, classes: 'subgrid_cell'},
                      { name: 'allSumm', index: 'allSumm', width: 80, align: 'center', sortable: false, classes: 'subgrid_cell'},
                      ],
					pager: pager_id,
                    rowNum:10,
                    autowidth: true,
			        forceFit: true,
                    height: 'auto',
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
            colNames: ['Дата', 'Показы</br>объявлений', 'Клики по</br>объявлениям', 'CTR</br>объявлений', '', '', 'Показы</br>банеров</br>по показам','','','Клики по</br>баннерам</br>по кликам'],
            colModel: [
              { name: 'Title', index: 'Дата', width: 100, align: 'center', sortable: false },
              { name: 'Impressions', index: 'Показы', width: 90, align: 'center', sortable: false },
              { name: 'UniqueClicks', index: 'Клики', width: 95, align: 'center', sortable: false },
              { name: 'CTR_Unique', index: 'CTR', width: 100, align: 'center', sortable: false},
              { name: 'Cost', index: 'Cost', width: 100, align: 'center', sortable: false, hidden:true},
              { name: 'Summ', index: 'Summ', width: 100, align: 'center', sortable: false, hidden:true},
              { name: 'bannerImpressions', index: 'bannerImpressions', width: 90, align: 'center', sortable: false },
              { name: '1Cost', index: '1Cost', width: 100, align: 'center', sortable: false, hidden:true},
              { name: '1Summ', index: '1Summ', width: 100, align: 'center', sortable: false, hidden:true},
              { name: 'banner_UniqueClicks', index: 'banner_UniqueClicks', width: 95, align: 'center', sortable: false, hidden:true },
              ],
            caption: "Статистика за каждый день по всем рекламным блокам",
      			gridview: true,
      			rownumbers: true,
      			rownumWidth: 40,
      			rowNum:10,
                height: 'auto',
      			forceFit: true,
      			hiddengrid: true,
      			pager: "#pagerStasByDays"
        });
		
		
		
		// Операции со счётом: приход
		$("#tableAccountIncome").jqGrid({
            url: '/private/accountIncome',
            datatype: 'json',
            mtype: 'GET',
            colNames: ['Дата', 'Клики по</br>объявлениям', 'Средняя цена</br>объявления', 'Сумма за</br>объявления',
            'Показы</br>банеров', 'Средняя цена</br>банера','Сумма за</br>банеры','Клики по</br>баннерам</br>по кликам','Сумма по</br>баннерам</br>по кликам','ИТОГО'],
            colModel: [
              { name: 'Date', index: 'Date', width: 120, align: 'center', sortable: false },
              { name: 'Unique', index: 'Unique', width: 120, align: 'center', sortable: false },
              { name: 'Cost', index: 'Cost', width: 120, align: 'center', sortable: false },
              { name: 'Summ', index: 'Summ', width: 120, align: 'center', sortable: false},
              { name: 'impbannerImpressions', index: 'impbannerImpressions', width: 120, align: 'center', sortable: false },
              { name: 'impbannerCost', index: 'impbannerCost', width: 120, align: 'center', sortable: false },
              { name: 'impbannerSumm', index: 'impbannerSumm', width: 120, align: 'center', sortable: false},
              { name: 'bannerUnique', index: 'bannerUnique', width: 120, align: 'center', sortable: false, hidden:true },
              { name: 'bannerSumm', index: 'bannerSumm', width: 120, align: 'center', sortable: false, hidden:true},
              { name: 'allSumm', index: 'allSumm', width: 120, align: 'center', sortable: false}
              ],
            caption: "Начисления на счёт",
      			gridview: true,
      			rownumbers: true,
      			rownumWidth: 40,
      			rowNum: 10,
      			forceFit: true,
                width: 'auto', 
                height: 'auto',
      			pager: "#pagerAccountIncome"
        });
		
		// Операции со счётом: вывод денег
		$("#tableAccountMoneyOut").jqGrid({
            url: '/private/moneyOutHistory',
            datatype: function(postdata) {
				this.addJSONData(account_data.moneyOutHistory);
			},
            mtype: 'GET',
            colNames: ['Дата', 'Тип платежа', 'Сумма', 'Код Протекции', 'Действителен до', 'Примечания'],
            colModel: [
              { name: 'Date', index: 'Date', width: 120, align: 'center', sortable: false },
              { name: 'PaymentType', index: 'PaymentType', width: 120, align: 'center', sortable: false },
              { name: 'Summ', index: 'Summ', width: 120, align: 'center', sortable: false},
              { name: 'protectionCode', index: 'protectionCode', width: 120, align: 'center', sortable: false},
              { name: 'protectionDate', index: 'protectionDate', width: 120, align: 'center', sortable: false},
			  { name: 'Comment', index: 'Comment', width: 300, align: 'center', sortable: false}],
            caption: "Вывод средств",
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
			caption: "Список существующих рекламных блоков",
			rownumbers: true,
			rowNum: 50,
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
					},
                    rowNum: 50,
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
				var y = item.datapoint[1].toFixed(2);
				var dt = new Date(item.datapoint[0]);
				var monthNames = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
				showTooltip(item.pageX, item.pageY,
					"<p style='text-align: center; font-weight: bold; margin: 0'>" + item.series.label + "</p>" +
					"Сумма заработка: " + y + "$<br />" +
					"Дата: " +  dt.getDate() + " " + monthNames[dt.getMonth()] + " " + dt.getFullYear() );
			}
			else {
				$("#tooltip").remove();
				prevPoint = null;
			}
		});


		$("#tabs").tabs({
			select: function(event, ui) {
				if(ui.index==3){
					document.title="YOTTOS | GetMyAd — Узнайте больше о GetMyAd!";
				}else
				document.title = "YOTTOS | GetMyAd — " + "бесплатная программа для заработка в Интернете. Заработай на своем сайте";
								
		}		
		});
		$("#tabs>ul>li:last-child").attr('style', 'position: absolute; right: 10px; top:5px');	// Отодвигаем вкладку "Помощь" вправо
		

		$("#showGrowingInfo, #showGrowingInfo2").click(function() {
			$("#tabs").tabs("select", 3);
			nextContents();
			return false;
		});
		
		$("#btnRegisterDomain").click(function() {
			$("#dialogRegisterDomain").dialog('open');
		});
		
        
        if (document.getElementById("moneyOut_factura")) {
            $("#removeUploadFactura").hide();
            $("#removeUploadFactura").click(function(){
                $.getJSON("/private/removeUploadFactura", function(data){
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
                });
            });
            
            new Ajax_upload('uploadButton', {
                action: "/private/uploadFactura",
                responseType: "json",
                onSubmit: function(file, ext){
                    $('#uploadButton').text('Загружается ' + file);
                    this.disable();
                },
                onComplete: function(file, response){
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
        }
 

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
                    $("#moneyOut_yandex").hide();
                    $("#moneyOut_card").show()
                    $("#moneyOut_webmoney").hide();
                    $("#moneyOut_factura").hide();
                    $("#moneyOut_errorMessage").html('');
                    $("#moneyOut_linkHelp").hide('');
                    break;
                  case 'webmoney_z':
                    $("#moneyOut_yandex").hide();
                    $("#moneyOut_webmoney").show();
                    $("#moneyOut_factura").hide();
                    $("#moneyOut_card").hide();
                    $("#moneyOut_errorMessage").html('');
                    $("#moneyOut_linkHelp").show('');
                    break;
                  case 'factura' :
                    $("#moneyOut_yandex").hide();
                    $("#moneyOut_factura").show();
                    $("#moneyOut_webmoney").hide();
                    $("#moneyOut_card").hide();
                    $("#moneyOut_errorMessage").html('');
                    $("#moneyOut_linkHelp").hide('');
                    break;  
                  case 'yandex' :
                    $("#moneyOut_errorMessage").html('');
                    $("#moneyOut_linkHelp").hide('');
                    $("#moneyOut_yandex").show();
                    $("#moneyOut_webmoney").hide();
                    $("#moneyOut_card").hide();
                    $("#moneyOut_factura").hide();
                    break;
                  default:
                    $("#moneyOut_yandex").hide();
                    $("#moneyOut_webmoney").show();
                    $("#moneyOut_banking").hide();
                    $("#moneyOut_card").hide();
                    $("#moneyOut_errorMessage").html('');
                    $("#moneyOut_linkHelp").show('');
                    break;
                }
    }  // end showRightMoneyOutBlock()
              
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
		
        var NowDate = new Date();
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
                var CurrentDay = NowDate.getDay();
                var LeftOffset = CurrentDay - 1;
                var RightOffset = 7 - CurrentDay;
                dayStart = new Date(NowDate.getFullYear(), NowDate.getMonth(), NowDate.getDate() - LeftOffset);
                dayEnd = new Date(NowDate.getFullYear(), NowDate.getMonth(), NowDate.getDate() + RightOffset)
				break;
			case 'lastweek':
				dayStart.setDate(today.getDate() - 7);
				dayEnd = today;
				break;
			case 'thismonth':
                dayStart = new Date(NowDate.getFullYear(), NowDate.getMonth(), 1);
                dayEnd = new Date(NowDate.getFullYear(), NowDate.getMonth(), NowDate.getDate())
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
                dayStart = dayEnd = '';
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
		// Форматирует дату для передачи серверу
		function formatDate(date) {
			if (!date.getMonth)
				return date;
			var m = date.getMonth()+1;
			var d = date.getDate();
			return (d<10? "0" + d : d) + '.' + (m<10? "0" + m : m) + "." + date.getFullYear() ;
		}
	$("#filterpreset").change(function () {
		var o = $("#filterpreset");
		var val = o.val();
		if (val == "range") {
			/*$("#filterByRangeOptions").show("slow");
			$("#filterByOneDayOptions").hide();*/
			$("#filterByRangeOptions").css('display', 'inline');
			$("#filterByOneDayOptions").css('display', 'none');
		}
		else if (val == "oneday") {
			/*$("#filterByOneDayOptions").show("slow");
			$("#filterByRangeOptions").hide();*/
			$("#filterByOneDayOptions").css('display', 'inline');
			$("#filterByRangeOptions").css('display', 'none');
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
            var summ = Math.round(account_data.accountSumm - 0.5).toString();
			$("#moneyOut_errorMessage").html('');
			$("#moneyOut_summ").val(summ).focus();
			$("#moneyOut_cardSumm").val(summ).focus();
			$("#moneyOut_facturaSumm").val(summ).focus();
			$("#moneyOut_comment").val('');
			$.getJSON('/private/lastMoneyOutDetails', function(data) {
				if (data.error)
					return;
				switch (data.paymentType) {
					case 'factura':
						$("#moneyOut_paymentType").val(data.paymentType);
						$("#moneyOut_facturaContact").val(data.contact);
						$("#moneyOut_facturaPhone").val(data.phone);
						break;
					case 'webmoney_z':
						$("#moneyOut_paymentType").val(data.paymentType);
						$("#moneyOut_webmoneyLogin").val(data.webmoneyLogin);
						$("#moneyOut_webmoneyAccountNumber").val(data.webmoneyAccount);
						$("#moneyOut_phone").val(data.phone);
						break;
					case 'card':
						$("#moneyOut_paymentType").val(data.paymentType);
						$("#moneyOut_cardBank").val(data.bank);
						$("#moneyOut_cardType").val(data.cardType);
						$("#moneyOut_cardCurrency").val(data.cardCurrency);
						$("#moneyOut_cardNumber").val(data.cardNumber);
						$("#moneyOut_cardName").val(data.cardName);
						$("#moneyOut_cardMonth").val(data.expire_month);
						$("#moneyOut_cardYear").val(data.expire_year);
						$("#moneyOut_cardBankMFO").val(data.bank_MFO);
						$("#moneyOut_cardBankOKPO").val(data.bank_OKPO);
						$("#moneyOut_cardBankTransitAccount").val(data.bank_TransitAccount);
						$("#moneyOut_cardPhone").val(data.phone);
						break;
					default:
						break; 	// unknown method
				}
				showRightMoneyOutBlock();
			});
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
						 "<p>На Ваш e-mail в течение нескольких часов поступит письмо со ссылкой подтверждения данной заявки. " + 
						 "Заявка должна быть одобрена в течение трёх дней.</p>"+
						 "<p>Внимание!"+ 
						 "Если в течение трех часов на Ваш e-mail не пришло письмо, посмотрите, пожалуйста, в спаме."+
						 "Если письмо не обнаружено ни во входящих письмах, ни в спаме, обратитесь, пожалуйста, к своему менеджеру.<p></div>").dialog({
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
                            if (result) { 
                              if (result.error_type == 'authorizedError'){ 
                                window.location.replace("/main/index");
                            }
                            else {
      						    reloadMoneyOutHistoryGrid();
                                $("#dialogCancelRequest").dialog("close");
                            }
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

    $.getJSON('/private/all_account_data', function(data) {
            if (data.error)
               window.location.replace("/");
            account_data = data;

            prepareUi();
            $("#tabs").css("visibility", "visible");
            showRightMoneyOutBlock();
            if(advertiseList.length<1){
                $("#tableExistingInformers").css({display:'none'});	
                $("#tableInformers").css({display:'none'});		
                $("#startwork").css({display:'block'});
                $("#linkinformers").click();		
            };
        
    }, function() {
        alert('failes');
    });


	
});	// end onDocumentReady
