$(document).ready(function() {
	/**
	 * Проверка текстового поля на допустимое число
	 */
	function checkFloat(o) {
		return o && /^-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/.test(o.val());
	}
	
	
	/**
	 * Создание пользовательского интерфейса
	 */	
	function prepareUi() {
		$("#tabs").tabs();
		
		// Диалог установки цены за клик 
		$("#dialogSetCost").dialog({
			autoOpen: false,
			modal: true,
			buttons: {
				'Назначить': function() {
					if (!checkFloat($("#dialogSetCost_cost"))) {
						alert('Неправильный формат цены!');
						return;
					}
					$.get("/manager/setClickCost", {
						cost: $("#dialogSetCost_cost").val(),
						date: $("#dialogSetCost_date").val(),
						user: $("#dialogSetCost_user").html()
						}, function(data) {
							$.getJSON("/manager/currentClickCost", function(json) {
								currentClickCost = json;
								$('#dialogSetCost').dialog('close');
								$("#tableClickCost").trigger("reloadGrid");
							});
						})
				},
				'Отмена': function() {
					$(this).dialog('close');
				}
			}
		});
		
		
		// Диалог одобрения заявки
		$("#dialogMoneyOutApprove").dialog({
			autoOpen: false,
			modal: true,
			buttons: {
				'Да': function() {
					$.get("/manager/approveMoneyOut", {
						user: $("#dialogMoneyOutApprove_user").html(),
						date: $("#dialogMoneyOutApprove_date").html(),
						approved: 'true'
					}, function(data) {
						$.getJSON("/manager/dataMoneyOutRequests", function(json) {
							dataMoneyOutRequests = json;
							$('#dialogMoneyOutApprove').dialog('close');
							$('#tableMoneyOutRequest').trigger('reloadGrid');
						})
					})
				},
				'Нет': function() {
					$(this).dialog('close');
				}
			}
		});
		
		
		
		
		// Таблица цен за уникального посетителя
		$("#tableClickCost").jqGrid({
            datatype: function(postdata) {
				this.addJSONData(currentClickCost);
			},
            mtype: 'GET',
            colNames: ['Пользователь', 'Цена', 'Действует с'],
            colModel: [
              { name: 'user', index: 'user', width: 150, align: 'center', sortable: false },
              { name: 'cost', index: 'cost', width: 90, align: 'center', sortable: false },
              { name: 'date', index: 'date', width: 100, align: 'center', sortable: false }],
            viewrecords: true,
            caption: "Текущие цены за уникального посетителя",
			gridview: true,
			rownumbers: true,
			height: 'auto',
			rownumWidth: 40,
			rowNum: 100,
			forceFit: true,
			toolbar: [true, 'top'],
			beforeSelectRow: function(rowid, e) {
				if (rowid)
					setCostButton.attr('disabled', false);
				return true;
			}
        });
		$("#tableClickCost").jqGrid('navGrid', '#toolbarClickCost', {edit:false, add:false, del: false});
		var setCostButton = $("<input type='button' value='Назначить цену' style='height:20px;'/>");
		setCostButton.attr('disabled', true).click(function() {
			var id = $("#tableClickCost").jqGrid('getGridParam', 'selrow');
			if (!id) return;
			var row = $("#tableClickCost").jqGrid('getRowData', id);
			var date = new Date();
			date.setHours(date.getHours() + 1);
			date.setMinutes(0);
			date.setSeconds(0);
			date.setMilliseconds(0);
			var hours = date.getHours();
			var day   = date.getDate();
			var month = date.getMonth()+1;
			if (hours < 10) hours = "0" + hours;
			if (day   < 10) day   = "0" + day;
			if (month < 10) month = "0" + month;
			
			var dateString = day + "." + month + "." + date.getFullYear() + " "
								+ hours + ":00";
			$("#dialogSetCost_user").html(row.user);
			$('#dialogSetCost_cost').val(row.cost);
			$('#dialogSetCost_date').val(dateString);
			$("#dialogSetCost").dialog('open');
		});
		$("#t_tableClickCost").append(setCostButton);
		
		
		
		

		// Таблица заявок на вывод средств
		$("#tableMoneyOutRequest").jqGrid({
            datatype: function() {
				this.addJSONData(dataMoneyOutRequests);
			},
//            mtype: 'GET',
            colNames: ['Пользователь', 'Дата', 'Сумма', 'Одобрено', 'Телефон', 'Оплата', 'Примечания'],
            colModel: [
              { name: 'user', index: 'user', width: 70, align: 'center', sortable: false },
              { name: 'date', index: 'date', width: 100, align: 'center', sortable: false },
              { name: 'summ', index: 'summ', width: 90, align: 'center', sortable: false },
              { name: 'approved', index: 'approved', width: 90, align: 'center', sortable: false },
              { name: 'phone', index: 'phone', width: 90, align: 'center', sortable: false },
              { name: 'paymentType', index: 'paymentType', width: 90, align: 'center', sortable: false },
              { name: 'comments', index: 'comments', width: 400, align: 'left', sortable: false }
			  ],
//            viewrecords: true,
            caption: "Заявки на вывод средств",
//			gridview: true,
			rownumbers: true,
			height: 'auto',
			rownumWidth: 40,
			rowNum: 100,
//			forceFit: true,
			toolbar: [true, 'top'],
			beforeSelectRow: function(rowid, e) {
				if (rowid)
					buttonApproveMoneyOutRequest.attr('disabled', false);
				return true;
			}
        });
		$("#tableMoneyOutRequest").jqGrid('navGrid', '#toolbarMoneyOut', {edit:false, add:false, del: false});
		var buttonApproveMoneyOutRequest = $("<input type='button' value='Одобрить заявку' style='height:20px;'/>");
		buttonApproveMoneyOutRequest.attr('disabled', true).click(function() {
			var table = $("#tableMoneyOutRequest");
			var id = table.jqGrid('getGridParam', 'selrow');
			if (!id) return;
			var row = table.jqGrid('getRowData', id);
			$('#dialogMoneyOutApprove_summ').html(row.summ);
			$('#dialogMoneyOutApprove_user').html(row.user);
			$('#dialogMoneyOutApprove_date').html(row.date);
			$("#dialogMoneyOutApprove").dialog('open');
		});

		$("#t_tableMoneyOutRequest").append(buttonApproveMoneyOutRequest);		




		// Сводная таблица по пользователям
		$("#tableUsersSummary").jqGrid({
            datatype: function(postdata) {
				this.addJSONData(dataUsersSummary);
			},
            mtype: 'GET',
            colNames: ['Пользователь', 'Средний CTR, %', 'Сумма на счету', 'Сумма за сегодня', 'Сумма за вчера', 'Сумма за неделю', 'Сумма за месяц', 'Сумма за год'],
            colModel: [
              { name: 'user', index: 'user', width: 150, align: 'center', sortable: false },
			  { name: 'dayCTR', index: 'dayCTR', width: 150, align: 'center', sortable: false },
              { name: 'summ', index: 'summ', width: 150, align: 'center', sortable: false },
			  { name: 'summToday', index: 'summToday', width: 150, align: 'center', sortable: false },
			  { name: 'summYesterday', index: 'summYesterday', width: 150, align: 'center', sortable: false },
			  { name: 'summWeek', index: 'summWeek', width: 150, align: 'center', sortable: false },
			  { name: 'summMonth', index: 'summMonth', width: 150, align: 'center', sortable: false },
			  { name: 'summYear', index: 'summYear', width: 150, align: 'center', sortable: false }
			  ],
            viewrecords: false,
            caption: "Суммарная статистика пользователей GetMyAd",
			gridview: true,
			rownumbers: true,
			height: 'auto',
			rownumWidth: 40,
			rowNum: 100,
            footerrow: true,
            userDataOnFooter: true
//			forceFit: true,
//			toolbar: [true, 'top'],
        });


		
	}
	
	
	
	prepareUi();
	
	
});
