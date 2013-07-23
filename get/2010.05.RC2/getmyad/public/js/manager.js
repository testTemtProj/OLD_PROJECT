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
		$("#tabs").tabs({
			add: function(event, ui) {
				$('#tabs').tabs('select', '#' + ui.panel.id);
//				console.log(ui);
				var match = ui.tab.hash.match('#user-details:(.+)');
				if (match && match[1]) {
					var login = match[1].replace(/_/g, '.');

                    var tabs = $.tabs();
					$(ui.panel).append(tabs);

//					$(ui.panel).append(UserDetails.UserDetails(login));
				}
			}
		});
		
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
		
		// Диалог установки процента для менеджера 
		$("#dialogSetPercent").dialog({
			autoOpen: false,
			modal: true,
			buttons: {
				'Назначить': function() {
					if (!checkFloat($("#dialogSetPercent_percent"))) {
						alert('Неправильный формат процента!');
						return;
					}
//					var date = new Date();
//					date.setHours(date.getHours() + 1);
//					date.setMinutes(0);
//					date.setSeconds(0);
//					date.setMilliseconds(0);
//					var hours = date.getHours();
//					var day   = date.getDate();
//					var month = date.getMonth()+1;
//					if (hours < 10) hours = "0" + hours;
//					if (day   < 10) day   = "0" + day;
//					if (month < 10) month = "0" + month;
//					
//					var dateString = day + "." + month + "." + date.getFullYear() + " "
//										+ hours + ":00";
//					var dateString = date +""

					$.get("/manager/setManagerPercent", {
						percent: $("#dialogSetPercent_percent").val(),
						manager: $("#dialogSetPercent_manager").html()
						
						}, function(data) {
							$.getJSON("/manager/managersSummary", function(json) {
								managersSummary = json;
								$('#dialogSetPercent').dialog('close');
								$("#managersSummary").trigger("reloadGrid");
							});
						})
				},
				'Отмена': function() {
					$(this).dialog('close');
				}
			}
		});
		// Таблица менеджеров
		$("#managersSummary").jqGrid({
			datatype: function(postdata) {
				this.addJSONData(managersSummary);
			},
            mtype: 'GET',
			colNames: ['Менеджер', 'Процент', 'Доход'],
            colModel: [
              { name: 'manager', index: 'manager', width: 150, align: 'center', sortable: false },
              { name: 'percent', index: 'percent', width: 90, align: 'center', sortable: false },
              { name: 'profit', index: 'profit', width: 100, align: 'center', sortable: false }],
			viewrecords: true,
            caption: "Сводная информация по менеджерам",
			gridview: true,
			rownumbers: true,
			height: 'auto',
			toolbar: [true, 'top'],
			beforeSelectRow: function(rowid, e) {
				if (rowid)
					setPercentButton.attr('disabled', false);
				return true;
			}
		});
		
		$("#managersSummary").jqGrid('navGrid', '#toolbarManagersSummary', {edit:false, add:false, del: false});
		var setPercentButton = $("<input type='button' value='Назначить процент' style='height:20px;'/>");
		setPercentButton.attr('disabled', true).click(function() {
			var id = $("#managersSummary").jqGrid('getGridParam', 'selrow');
			if (!id) return;
			var row = $("#managersSummary").jqGrid('getRowData', id);
			$("#dialogSetPercent_manager").html(row.manager);
			$('#dialogSetPercent_percent').val(row.percent);
			$("#dialogSetPercent").dialog('open');
		});
		$("#t_managersSummary").append(setPercentButton);
		
		
		// Таблица цен за уникального посетителя
		$("#tableClickCost").jqGrid({
            datatype: function(postdata) {
				this.addJSONData(currentClickCost);
			},
            mtype: 'GET',
            colNames: ['Пользователь', 'Цена', 'Действует с'],
            colModel: [
              { name: 'user', index: 'user', width: 180, align: 'center', sortable: false },
              { name: 'cost', index: 'cost', width: 90, align: 'center', sortable: false },
              { name: 'date', index: 'date', width: 120, align: 'center', sortable: false }],
            viewrecords: true,
            caption: "Текущие цены за уникального посетителя",
			gridview: true,
			rownumbers: true,
			height: 'auto',
			rownumWidth: 40,
			rowNum: 100,
			forceFit: true,
			toolbar: [permissionSetClickCost, 'top'],
			footerrow: true,
            userDataOnFooter: true,
			beforeSelectRow: function(rowid, e) {
				if (rowid)
					setCostButton.attr('disabled', false);
				return true;
			},
			onSelectRow: function(){
				if (!permissionSetClickCost)
					setCostButton.attr('disabled', false);
				return true;
			}
        });
		
		var setCostButton = $("<input type='button' value='Назначить цену' style='height:20px;'/>");
		$("#tableClickCost").jqGrid('navGrid', '#toolbarClickCost', {edit:false, add:false, del: false});
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
		if (permissionSetClickCost) 
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
				if (!rowid) return false;
				var row = $("#tableMoneyOutRequest").jqGrid('getRowData', rowid);
				if (row.approved == 'Да') 
					buttonApproveMoneyOutRequest.attr('disabled', true)
				else 
					buttonApproveMoneyOutRequest.attr('disabled', false)
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
		function openUserDetails() {
			var login = this.text;
			var url = "/manager/userDetails?login=" + encodeURIComponent(login);
			$("#tabs").tabs('add', url, login);
		}
		
		$("#tableUsersSummary").jqGrid({
            datatype: function(postdata) {
				for (var i=0; i<dataUsersSummary.rows.length; i++) {
					var cell = dataUsersSummary.rows[i].cell;
					var login = cell[0];
					cell[0] = '<a href="javascript:;" class="actionLink">' + login + '</a>';
				}
				this.addJSONData(dataUsersSummary);
//				$('#tableUsersSummary .actionLink').click(openUserDetails);
			},
            mtype: 'GET',
            colNames: ['Пользователь', 'Средний CTR, %', 'Сумма на счету', 'Сегодня', 'Вчера', 'Позавчера', 'За неделю', 'За месяц', 'За год'],
            colModel: [
              { name: 'user', index: 'user', width: 150, align: 'center', sortable: false },
			  { name: 'dayCTR', index: 'dayCTR', width: 150, align: 'center', sortable: false },
              { name: 'summ', index: 'summ', width: 150, align: 'center', sortable: false },
			  { name: 'summToday', index: 'summToday', width: 120, align: 'center', sortable: false },
			  { name: 'summYesterday', index: 'summYesterday', width: 120, align: 'center', sortable: false },
			  { name: 'summBeforeYesterday', index: 'summBeforeYesterday', width: 120, align: 'center', sortable: false },
			  { name: 'summWeek', index: 'summWeek', width: 120, align: 'center', sortable: false },
			  { name: 'summMonth', index: 'summMonth', width: 120, align: 'center', sortable: false },
			  { name: 'summYear', index: 'summYear', width: 120, align: 'center', sortable: false }
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


		// Таблица заявок на добавление домена
		$("#tableDomainRegistration").jqGrid({
            datatype: function() {
				var data = dataDomainRequests;
				for (var i=0; i<data.rows.length; i++) {
					data.rows[i].cell.push('<a href="javascript:;" class="actionLink">Одобрить</a>');
				}
				this.addJSONData(data);
				$("#tableDomainRegistration .actionLink").click(function() {
					var grid = $("#tableDomainRegistration");
					var rowId = grid.getGridParam('selrow');
					if (rowId == null)
						return;
					var row = grid.jqGrid('getRowData', rowId);
					var message = "<p>Одобрить домен <b>" + row.domain + 
								  "</b> для пользователя " + row.user + "?</p>"; 
					var dialog = $(message).dialog({
						modal: true,
						buttons: {
							'Да': function() {
								$.get("/manager/approveDomain", {
									user: row.user,
									domain: row.domain,
									approved: 'true'
								}, function(data) {
									$.getJSON("/manager/domainsRequests", function(json) {
										dataDomainRequests = json;
										dialog.dialog('close');
										$('#tableDomainRegistration').trigger('reloadGrid');
									})
								})
							},
							'Нет': function() {
								dialog.dialog('close');
							}
						}				
					});
				});

				
				
			},
            colNames: ['Пользователь', 'Дата', 'Домен', 'Примечания', ''],
            colModel: [
              { name: 'user', index: 'user', width: 90, align: 'center', sortable: false },
              { name: 'date', index: 'date', width: 100, align: 'center', sortable: false },
              { name: 'domain', index: 'domain', width: 180, align: 'center', sortable: false },
              { name: 'comments', index: 'comments', width: 400, align: 'left', sortable: false },
              { name: 'actions', index: 'actions', width: 80, align: 'center', sortable: false }
			  ],
            caption: "Заявки на добавление домена",
			rownumbers: true,
			height: 'auto',
			rownumWidth: 40,
			rowNum: 100
//			toolbar: [true, 'top'],
//			beforeSelectRow: function(rowid, e) {
//				if (rowid)
//					buttonApproveMoneyOutRequest.attr('disabled', false);
//				return true;
//			}
        });

		
	}
	
	
	
	prepareUi();
	
	
});
