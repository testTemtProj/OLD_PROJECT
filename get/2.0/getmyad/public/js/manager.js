var ManagerUI = function(){
CheckUser();
$(document).ready(function(){
	/**
	 * Проверка текстового поля на допустимое число
	 */
	function checkFloat(o){
		return o && /^-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/.test(o.val());
	}
	
	
	
	/**
	 * Создание пользовательского интерфейса
	 */
	function prepareUi(){
		$("#tabs").tabs({
			add: function(event, ui){
				$('#tabs').tabs('select', '#' + ui.panel.id);
				var match = ui.tab.hash.match('#user-details:(.+)');
				if (match && match[1]) {
					var login = match[1].replace(/_/g, '.');
					
                    var tabs = $.tabs();
					$(ui.panel).append(tabs);
					
					//					$(ui.panel).append(UserDetails.UserDetails(login));
				}
			}
		});
		
   /**
		 * Форма заявки на вывод денежных средств.
   */
  $("#moneyOut").dialog({
    autoOpen: false,
    modal: true,
    width: 450,
    height: 'auto',
    resizable: false,
    title: 'Заявка на вывод средств',
			open: function(event, ui){
      $("#moneyOut_summ").val(Math.round(0).toString()).focus();
      $("#moneyOut_comment").val('');
    },
    buttons: {
				'Отмена': function(){
        $(this).dialog('close');
      },
				'Отправить заявку': function(){
        $('#moneyOut_form').ajaxSubmit({
          dataType: 'json',
						beforeSubmit: function(){
            $("#moneyOut_wait").show();
          },
						success: function(reply){
            if (reply.error) {
								if (reply.error_type == "authorizedError") 
                  window.location.replace("/main/index");
								else 
									if (reply.msg) {
                  $("#moneyOut_errorMessage").html(reply.msg);
                }
									else 
										$("#moneyOut_errorMessage").html("Неизвестная ошибка.");
							}
            else {
              $("#moneyOut").dialog('close');
              $("<p>Заявка успешно принята!</p>").dialog({
                modal: true,
                resizable: false,
									buttons: {
										OK: function(){
                  reloadMoneyOutHistoryGrid();
                  $(this).dialog('close');
										}
									}
              })
            }
          },
						complete: function(){
            $("#moneyOut_wait").hide();
          }
      });
    }
    }
  });
        
		$(".linkMoneyOut").click(function(){
 		 	  $("#moneyOut").dialog('open');
		});
 		 		
		// Диалог установки цены за клик 
		$("#costType1").click(function() {
			$("#fieldsSetCost_FixedCost").show();
			$("#fieldsSetCost_Percent").hide();
		});
		$("#costType2").click(function() {
			$("#fieldsSetCost_FixedCost").hide();
			$("#fieldsSetCost_Percent").show();
		});
		$("#dialogSetCost").dialog({
			autoOpen: false,
			modal: true,
			buttons: {
				'Назначить': function(){
					var costType;
					if ($("#costType1")[0].checked) {
						// Фиксированная цена за клик
						if (!checkFloat($("#dialogSetCost_cost"))) {
							alert('Неправильный формат цены!');
							return;
						}
						costType = 'fixed_cost';
					} else {
						// Процент от цены рекламодателя
						if (!checkFloat($("#dialogSetCost_percent"))) {
							alert('Неправильный формат процента!');
							return;
						}
						if (!checkFloat($("#dialogSetCost_min"))) {
							alert('Неправильный формат минимальной цены!');
							return;
						}
						if (!checkFloat($("#dialogSetCost_max"))) {
							alert('Неправильный формат максимальной цены!');
							return;
						}
						costType = 'percent';
					}

					$.getJSON("/manager/setClickCost", {
						type: costType,
						cost: $("#dialogSetCost_cost").val(),
						date: $("#dialogSetCost_date").val(),
						user: $("#dialogSetCost_user").html(),
						percent: $("#dialogSetCost_percent").val(),
						min: $("#dialogSetCost_min").val(),
						max: $("#dialogSetCost_max").val(),
						token: token
					}, function(data){
						  if (data.error) {
							if (data.error_type == "authorizedError") 
						     		window.location.replace("/main/index");
							else if (data.msg) {
                  						alert(data.msg);
								return;
							}
               						else {
					                  alert("Неизвестная ошибка.")
							return;
							  }
						  }
						  else {
							$.getJSON("/manager/currentClickCost", function(json){
								currentClickCost = json;
  								$('#dialogSetCost').dialog('close');
  								$("#tableClickCost").trigger("reloadGrid");
  							});
						}
					})
				},
				'Отмена': function(){
					$(this).dialog('close');
				}
			}
		});
		
		// Диалог одобрения заявки
		$("#dialogMoneyOutApprove").dialog({
			autoOpen: false,
			modal: true,
			buttons: {
				'Да': function(){
					$.getJSON("/manager/approveMoneyOut", {
						user: $("#dialogMoneyOutApprove_user").html(),
						date: $("#dialogMoneyOutApprove_date").html(),
                        protectionCode: $('#dialogMoneyOutApprove > input[name="protectionCode"]')[0].value,
                        protectionPeriod: $('#dialogMoneyOutApprove > input[name="protectionPeriod"]')[0].value,
						approved: 'true',
						token: token
					}, function(data){
					  if (data.error) {
							if (data.error_type == "authorizedError") 
					       window.location.replace("/main/index");
							else 
								if (data.msg) {
					       alert(msg);
					       return;
					    }
					    else {
					       alert("Неизвестная ошибка.")
					       return;
					    }
						}
						else {
							$.getJSON("/manager/dataMoneyOutRequests", function(json){
    							 dataMoneyOutRequests = json;
    							 $('#dialogMoneyOutApprove').dialog('close');
    							 $('#tableMoneyOutRequest').trigger('reloadGrid');
    						 })
						}
					})
				},
				'Нет': function(){
					$(this).dialog('close');
				}
			}
		});

		// Диалог разрешения заявки
		$("#dialogMoneyOutAgree").dialog({
			autoOpen: false,
			modal: true,
			buttons: {
				'Да': function(){
					$.getJSON("/manager/agreeMoneyOut", {
						user: $("#dialogMoneyOutAgree_user").html(),
						date: $("#dialogMoneyOutAgree_date").html(),
						approved: 'true',
						token: token
					}, function(data){
					  if (data.error) {
							if (data.error_type == "authorizedError") 
					       window.location.replace("/main/index");
							else 
								if (data.msg) {
					       alert(msg);
					       return;
					    }
					    else {
					       alert("Неизвестная ошибка.")
					       return;
					    }
						}
						else {
							$.getJSON("/manager/dataMoneyOutRequests", function(json){
    							 dataMoneyOutRequests = json;
    							 $('#dialogMoneyOutAgree').dialog('close');
    							 $('#tableMoneyOutRequest').trigger('reloadGrid');
    						 })
						}
					})
				},
				'Нет': function(){
					$(this).dialog('close');
				}
			}
		});

		$("#dialogMoneyOutUpdateProtectionCode").dialog({
			autoOpen: false,
			modal: true,
			buttons: {
				'OK': function(){
					$.getJSON("/manager/updateProtection", {
						user: $("#dialogMoneyOutUpdateProtectionCode_user").html(),
						date: $("#dialogMoneyOutUpdateProtectionCode_date").html(),
                        protectionCode: $('#dialogMoneyOutUpdateProtectionCode > input[name="protectionCode"]')[0].value,
                        protectionPeriod: $('#dialogMoneyOutUpdateProtectionCode > input[name="protectionPeriod"]')[0].value,
						token: token
					}, function(data){
					  if (data.error) {
							if (data.error_type == "authorizedError") 
					       window.location.replace("/main/index");
							else 
								if (data.msg) {
					       alert(msg);
					       return;
					    }
					    else {
					       alert("Неизвестная ошибка.")
					       return;
					    }
						}
						else {
							$.getJSON("/manager/dataMoneyOutRequests", function(json){
    							 dataMoneyOutRequests = json;
    							 $('#dialogMoneyOutUpdateProtectionCode').dialog('close');
    							 $('#tableMoneyOutRequest').trigger('reloadGrid');
    						 })
						}
					})
				},
				'Нет': function(){
					$(this).dialog('close');
				}
			}
		});

		// Диалог блокировки менеджера
		$('#dialogBlockManager').dialog({
			autoOpen: false,
			modal: true,
			buttons: {
				'Да': function() {
					$.getJSON("/manager/block", {
						manager: $("#dialogBlockManager_manager").html(),
						token: token
					}, function(data) {
					      $("#managersSummary").trigger("reloadGrid");
					      $('#dialogBlockManager').dialog('close');
					});
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
				'Назначить': function(){
					if (!checkFloat($("#dialogSetPercent_percent"))) {
						alert('Неправильный формат процента!');
						return;
					}
					
					$.getJSON("/manager/setManagerPercent", {
						percent: $("#dialogSetPercent_percent").val(),
						manager: $("#dialogSetPercent_manager").html(),
						token: token
						
					}, function(data){
						  if (data.error) {
							if (data.error_type == "authorizedError") 
						        window.location.replace("/main/index");
							else 
								if (data.msg) {
						        alert(msg);
						        return;
						    }
						    else {
						          alert("Неизвестная ошибка");
						          return;
						    }
						  }
						else {
							$.getJSON("/manager/managersSummary", function(json){
								      managersSummary = json;
								      $('#dialogSetPercent').dialog('close');
								      $("#managersSummary").trigger("reloadGrid");
							   });
							}
						})
				},
				'Отмена': function(){
					$(this).dialog('close');
				}
			}
		});
		
		// Таблица менеджеров
		$("#managersSummary").jqGrid({
			datatype: function(postdata){
				this.addJSONData(managersSummary);
			},
      mtype: 'GET',
			colNames: ['Менеджер', 'Процент', 'Доход'],
			colModel: [{
				name: 'manager',
				index: 'manager',
				width: 150,
				align: 'center',
				sortable: false
			}, {
				name: 'percent',
				index: 'percent',
				width: 90,
				align: 'center',
				sortable: false
			}, {
				name: 'profit',
				index: 'profit',
				width: 100,
				align: 'center',
				sortable: false
			}],
			viewrecords: true,
      caption: "Сводная информация по менеджерам",
			gridview: true,
			rownumbers: true,
			height: 'auto',
			toolbar: [true, 'top'],
			hiddengrid: true,
			beforeSelectRow: function(rowid, e){
				if (rowid) {
					setPercentButton.attr('disabled', false);
					blockManagerButton.attr('disabled', false);
				}
				return true;
			}
		});

		var setPercentButton = $("<input type='button' value='Назначить процент'/>");
		setPercentButton.attr('disabled', true).click(function(){
			var id = $("#managersSummary").jqGrid('getGridParam', 'selrow');
			if (!id) 
				return;
			var row = $("#managersSummary").jqGrid('getRowData', id);
			$("#dialogSetPercent_manager").html(row.manager);
			$('#dialogSetPercent_percent').val(row.percent);
			$("#dialogSetPercent").dialog('open');
		});
		$("#t_managersSummary").append(setPercentButton);

		var blockManagerButton = $('<input type="button" value="Блокировать" />');
		blockManagerButton.attr('disabled', true).click(function() {
			var id = $("#managersSummary").jqGrid('getGridParam', 'selrow');
			if (!id)
				return;
			var row = $("#managersSummary").jqGrid('getRowData', id);
			$("#dialogBlockManager_manager").html(row.manager);
			$("#dialogBlockManager").dialog('open');
		});
		$("#t_managersSummary").append(blockManagerButton);
		
		
		// Таблица цен за уникального посетителя
		$("#tableClickCost").jqGrid({
			url: '/manager/currentClickCost',
			datatype: 'json',
      			mtype: 'GET',
      			colNames: ['Пользователь', 'Цена', 'Действует с', 'percent', 'cost_min', 'cost_max'],
			colModel: [{
				name: 'user',
				index: 'user',
				width: 180,
				align: 'center'
			}, {
				name: 'cost',
				index: 'cost',
				width: 140,
				align: 'center'
			}, {
				name: 'date',
				index: 'date',
				width: 120,
				align: 'center'
			}, {
				name: 'percent',
				index: 'percent',
				hidden: true
			}, {
				name: 'cost_min',
				index: 'cost_min',
				hidden: true
			}, {
				name: 'cost_max',
				index: 'cost_max',
				hidden: true
			}],
      			viewrecords: true,
      			caption: "Текущие цены за уникального посетителя",
			gridview: true,
			rownumbers: true,
			height: 420,
			rownumWidth: 40,
			rowNum: 900,
			pager: "#pagerClickCost",
			forceFit: true,
			toolbar: [permissionSetClickCost, 'top'],
			footerrow: true,
			hiddengrid: true,
			userDataOnFooter: true,
			beforeSelectRow: function(rowid, e){
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
		
		var setCostButton = $("<input type='button' value='Назначить цену' />");
		setCostButton.attr('disabled', true).click(function(){
			var id = $("#tableClickCost").jqGrid('getGridParam', 'selrow');
			if (!id) 
				return;
			var row = $("#tableClickCost").jqGrid('getRowData', id);
			var date = new Date();
			date.setHours(date.getHours() + 1);
			date.setMinutes(0);
			date.setSeconds(0);
			date.setMilliseconds(0);
			var hours = date.getHours();
			var day   = date.getDate();
			var month = date.getMonth() + 1;
			if (hours < 10) 
				hours = "0" + hours;
			if (day < 10) 
				day = "0" + day;
			if (month < 10) 
				month = "0" + month;
			
			var dateString = day + "." + month + "." + date.getFullYear() + " " + hours + ":00";
			$("#dialogSetCost_user").html(row.user);
			if (row.percent) {
				$('#costType2').click();
				$('#dialogSetCost_percent').val(row.percent);
				$('#dialogSetCost_min').val(row.cost_min);
				$('#dialogSetCost_max').val(row.cost_max);
				$('#dialogSetCost_cost').val('0.00');
			} else {
				$('#costType1').click();
				$('#dialogSetCost_cost').val(row.cost);
				$('#dialogSetCost_percent').val('50');
				$('#dialogSetCost_min').val('0.01');
				$('#dialogSetCost_max').val('1.00');
			}
			$('#dialogSetCost_date').val(dateString);
			$("#dialogSetCost").dialog('open');
		});
		if (permissionSetClickCost) 
			$("#t_tableClickCost").append(setCostButton);
			
		// Фильтр, скрывающий неактивные аккаунты из таблицы цен
		var filterOnlyActiveCost = $('<input type="checkbox" value="filterOnlyActiveCost">Только активные</input>');
		filterOnlyActiveCost.click(function(){
            function reloadClickCostGrid(){
                $('#tableClickCost').jqGrid('setGridParam', {
                    datatype: "json"
                }).jqGrid('setGridParam', {
                    url: "/manager/currentClickCost?onlyActive=" + filterOnlyActiveCost.is(":checked")
                }).trigger("reloadGrid");
            }
			reloadClickCostGrid();
			
		});
		$("#t_tableClickCost").append(filterOnlyActiveCost);
		
		
		// Таблица заявок на вывод средств
		$("#tableMoneyOutRequest").jqGrid({
			datatype: function(){
                this.addJSONData(dataMoneyOutRequests);
				$('#tableMoneyOutRequest .actionLink').click(openUserDetails);
                $("#tableMoneyOutRequest").jqGrid('setGridParam', 
                        {'url': '/manager/dataMoneyOutRequests',
                        'datatype': 'json'});
			},
            loadComplete: function() {
				$('#tableMoneyOutRequest .actionLink').click(openUserDetails);
            },
      colNames: ['Пользователь', 'Дата', 'Сумма', 'Подтверждено', 'Разрешено', 'Оплачено', 'Телефон', 'Оплата', 'Код протекции', 'Истекает',  'Примечания'],
			colModel: [{
				name: 'user',
				index: 'user',
				width: 115,
				align: 'center',
				sortable: true,
                classes: 'actionLink pseudoLink'
			}, {
				name: 'date',
				index: 'date',
				width: 70,
				align: 'center',
				sortable: true
			}, {
				name: 'summ',
				index: 'summ',
				width: 70,
				align: 'center',
				sortable: true
			}, {
				name: 'user_confirmed',
				index: 'user_confirmed',
				width: 100,
				align: 'center',
				sortable: true
			}, {
				name: 'manager_agreed',
				index: 'manager_agreed',
				width: 80,
				align: 'center',
				sortable: true
			}, {
				name: 'approved',
				index: 'approved',
				width: 80,
				align: 'center',
				sortable: true
			}, {
				name: 'phone',
				index: 'phone',
				width: 100,
				align: 'center',
				sortable: true
			}, {
				name: 'paymentType',
				index: 'paymentType',
				width: 90,
				align: 'center',
				sortable: true
			}, {
                name: 'protectionCode',
                index: 'protectionCode',
                width: 100,
                align: 'center',
                sortable: false
			}, {
                name: 'protectionDate',
                index: 'protectionDate',
                width: 100,
                align: 'center',
                sortable: false
			}, {
				name: 'comments',
				index: 'comments',
				width: 400,
				align: 'left',
				sortable: true
			}],
      caption: "Заявки на вывод средств",
			rownumbers: true,
    		height: '500',
			rownumWidth: 20,
			rowNum: 10,
			pager: "#pagerMoneyOutRequest",
			forceFit: true,
			toolbar: [true, 'top'],
			beforeSelectRow: function(rowid, e){
				if (!rowid) 
					return false;
				var row = $("#tableMoneyOutRequest").jqGrid('getRowData', rowid);
				buttonApproveMoneyOutRequest.attr('disabled', row.approved       == 'Да' ||
                                                              row.user_confirmed != 'Да' ||
                                                              row.manager_agreed != 'Да');
                buttonAgreeMoneyOutRequest.attr('disabled', row.approved       == 'Да' ||
                                                            row.manager_agreed == 'Да'); 

                buttonUpdateProtectionCodeMoneyOutRequest.attr('disabled', ((row.approved != 'Да') ||
                                                                            (row.user_confirmed != 'Да') ||
                                                                            (row.manager_agreed != 'Да')) ||
                                                                            ((row.paymentType != 'webmoney_z') &&
                                                                            (row.paymentType != 'yandex')));
				return true;
			}
        });

        var toolbar = $("#t_tableMoneyOutRequest");
		
		var buttonApproveMoneyOutRequest = $("<input type='button' value='Одобрить заявку' />");
		buttonApproveMoneyOutRequest.attr('disabled', true).click(function(){
			var table = $("#tableMoneyOutRequest");
			var id = table.jqGrid('getGridParam', 'selrow');
			if (!id) 
				return;
			var row = table.jqGrid('getRowData', id);
			$('#dialogMoneyOutApprove_summ').html(row.summ);
			$('#dialogMoneyOutApprove_user').html(row.user);
			$('#dialogMoneyOutApprove_date').html(row.date);
			$("#dialogMoneyOutApprove").dialog('open');
		}).appendTo(toolbar);
		
		var buttonAgreeMoneyOutRequest = $("<input type='button' value='Разрешить' />");
		buttonAgreeMoneyOutRequest.attr('disabled', true).click(function(){
			var table = $("#tableMoneyOutRequest");
			var id = table.jqGrid('getGridParam', 'selrow');
			if (!id) 
				return;
			var row = table.jqGrid('getRowData', id);
			$('#dialogMoneyOutAgree_summ').html(row.summ);
			$('#dialogMoneyOutAgree_user').html(row.user);
			$('#dialogMoneyOutAgree_date').html(row.date);
			$("#dialogMoneyOutAgree").dialog('open');
		}).appendTo(toolbar);

        var buttonUpdateProtectionCodeMoneyOutRequest = $("<input type='button' value='Обновить код протекции' />");
        buttonUpdateProtectionCodeMoneyOutRequest.attr('disabled', true).click(function(){
			var table = $("#tableMoneyOutRequest");
			var id = table.jqGrid('getGridParam', 'selrow');
			if (!id) 
				return;
			var row = table.jqGrid('getRowData', id);
			$('#dialogMoneyOutUpdateProtectionCode_summ').html(row.summ);
			$('#dialogMoneyOutUpdateProtectionCode_user').html(row.user);
			$('#dialogMoneyOutUpdateProtectionCode_date').html(row.date);
			$("#dialogMoneyOutUpdateProtectionCode").dialog('open');
        }).appendTo(toolbar);

		
		// Таблица о сводной статистике по дням
        $("#tableOverallSummary").jqGrid({
			datatype: 'local',
            data: dataOverallSummary,
            mtype: 'GET',
            colNames: ['Дата', 'Показы', 'Клики', 'Клики уник.', 'Сумма', 'CTR', 'Цена'],
			colModel: [{
				name: 'date',
				index: 'date',
				width: 140,
				align: 'center',
				sortable: false
			}, {
				name: 'impressions',
				index: 'impressions',
				width: 100,
				align: 'center',
				sortable: false
			}, {
				name: 'clicks',
				index: 'clicks',
				width: 100,
				align: 'center',
				sortable: false
			}, {
				name: 'clicksUnique',
				index: 'clicksUnique',
				width: 100,
				align: 'center',
				sortable: false
			}, {
				name: 'profit',
				index: 'profit',
				width: 100,
				align: 'center',
				sortable: false
			}, {
				name: 'ctr',
				index: 'ctr',
				width: 100,
				align: 'center',
				sortable: false
			}, {
				name: 'click_cost',
				index: 'click_cost',
				width: 100,
				align: 'center',
				sortable: false
			}],
            caption: "Общая статистика",
            gridview: true,
            rowNum: 30,
            rownumbers: false,
            height: 300,
            footerrow: false,
            userDataOnFooter: false,
            pager: 'pagerOverallSummary'
        });
		
		// Таблица с данными о доходе пользователей GetMyAd
		$("#tableUsersSummary").jqGrid({
		datatype: function(postdata){
				for (var i = 0; i < dataUsersSummary.rows.length; i++) {
        					var cell = dataUsersSummary.rows[i].cell;
        					var login = cell[0];
        					var flag = cell[9]
        					if(cell[0] != '<a href="javascript:;" class="actionLink ' + flag + '">' + login + '</a>')
								cell[0] = '<a href="javascript:;" class="actionLink ' + flag + '">' + login + '</a>';
							else
				  				cell[0] = login;
        			}
  				this.addJSONData(dataUsersSummary);
  				
  				$('#tableUsersSummary .actionLink').click(openUserDetails);
			  },
		loadComplete: function() {
			$('#tableUsersSummary .actionLink').click(openUserDetails);
		},
        mtype: 'GET',
        colNames: ['Пользователь', 'Сегодня', 'Вчера', 'Позавчера', 'За неделю', 'За месяц', 'За год', 'CTR за 1 день', 'CTR за 7 дней', 'Сумма на счету'],
			colModel: [{
				name: 'user',
				index: 'user',
				width: 150,
				align: 'center',
				sortable: true
			}, {
				name: 'summToday',
				index: 'summToday',
				width: 120,
				align: 'center',
				sortable: true
			}, {
				name: 'summYesterday',
				index: 'summYesterday',
				width: 120,
				align: 'center',
				sortable: true
			}, {
				name: 'summBeforeYesterday',
				index: 'summBeforeYesterday',
				width: 120,
				align: 'center',
				sortable: true
			}, {
				name: 'summWeek',
				index: 'summWeek',
				width: 120,
				align: 'center',
				sortable: true,
				hidden: !permissionViewAllUserStats
			}, {
				name: 'summMonth',
				index: 'summMonth',
				width: 120,
				align: 'center',
				sortable: true,
				hidden: !permissionViewAllUserStats
			}, {
				name: 'summYear',
				index: 'summYear',
				width: 120,
				align: 'center',
				sortable: true,
				hidden: !permissionViewAllUserStats
			}, {
				name: 'dayCTR',
				index: 'dayCTR',
				width: 130,
				align: 'center',
				sortable: true
			}, {
				name: 'weekCTR',
				index: 'weekCTR',
				width: 130,
				align: 'center',
				sortable: true
			}, {
				name: 'summ',
				index: 'summ',
				width: 150,
				align: 'center',
				sortable: true,
				hidden: !permissionViewAllUserStats
			}],
      viewrecords: false,
      caption: "Суммарная статистика пользователей GetMyAd",
			gridview: true,
			rownumbers: true,
			height: 420,
			rownumWidth: 40,
			rowNum: 900,
      footerrow: true,
      userDataOnFooter: true,
	  onSortCol: function(index, iCol, sortorder){
          $('#tableUsersSummary').jqGrid('setGridParam', {
              datatype: "json"
          }).jqGrid('setGridParam', {
              url: "/manager/dataUsersSummary?sortcol=" + iCol + "&sortreverse=" + sortorder
          });
	  }
    });
    
	// Таблица с данными о количестве показов
    $("#tableUsersImpressions").jqGrid({
			datatype: function(postdata){
				for (var i = 0; i < dataUsersImpressions.rows.length; i++) {
                  var cell = dataUsersImpressions.rows[i].cell;
                  var login = cell[0];
                  var flag = cell[7];
				  if(cell[0]!='<a href="javascript:;" class="actionLink ' + flag + '">' + login + '</a>')
				  	cell[0] = '<a href="javascript:;" class="actionLink ' + flag + '">' + login + '</a>';
				  else
				  	cell[0] = login;
              }
          this.addJSONData(dataUsersImpressions);
          
          $('#tableUsersImpressions .actionLink').click(openUserDetails);
        },
		loadComplete: function() {
			$('#tableUsersImpressions .actionLink').click(openUserDetails);
		},
        mtype: 'GET',
        colNames: ['Пользователь', 'Сегодня', 'Вчера', 'Позавчера', 'За неделю', 'За месяц', 'За год'],
			colModel: [{
				name: 'user',
				index: 'user',
				width: 150,
				align: 'center',
				sortable: true
			}, {
				name: 'impToday',
				index: 'impToday',
				width: 120,
				align: 'center',
				sortable: true
			}, {
				name: 'impYesterday',
				index: 'impYesterday',
				width: 120,
				align: 'center',
				sortable: true
			}, {
				name: 'impBeforeYesterday',
				index: 'impBeforeYesterday',
				width: 120,
				align: 'center',
				sortable: true
			}, {
				name: 'impWeek',
				index: 'impWeek',
				width: 120,
				align: 'center',
				sortable: true
			}, {
				name: 'impMonth',
				index: 'impMonth',
				width: 120,
				align: 'center',
				sortable: true
			}, {
				name: 'impYear',
				index: 'impYear',
				width: 120,
				align: 'center',
				sortable: true
			}],
      viewrecords: false,
      caption: "Статистика пользователей GetMyAd по количеству показов",
      gridview: true,
			rownumbers: true,
      height: 420,
      rownumWidth: 40,
      rowNum: 900,
      footerrow: true,
      userDataOnFooter: true,
			onSortCol: function(index, iCol, sortorder){
				if (sortorder == 'desc') 
					sortorder = 'True';
				else 
					sortorder = 'False';
				function reloadClickCostGrid(){
                $('#tableUsersImpressions').jqGrid('setGridParam', {
                    datatype: "json"
                }).jqGrid('setGridParam', {
                    url: "/manager/dataUsersImpressions?sortCol=" + iCol + "&sortRevers=" + sortorder
                }).trigger("reloadGrid");
            }
			reloadClickCostGrid();
			}
    });
		
		// Таблица дохода менеджера за 30 дней по дням 
    $("#tableAccountProfit").jqGrid({
            datatype: function(postdata){
        this.addJSONData(monthProfitPerDate);
  },
      mtype: 'GET',
      colNames: ['Дата', 'Доход'],
			colModel: [{
				name: 'date',
				index: 'date',
				width: 140,
				align: 'center'
			}, {
				name: 'sum',
				index: 'sum',
				width: 140,
				align: 'center'
			}],
      caption: "Доход за 30 дней по дням",
      gridview: true,
      rowNum: 30,
      rownumbers: false,
      height: 300,
      footerrow: true,
			userDataOnFooter: true
    });
		
	// Операции со счётом: вывод денег
    $("#tableAccountMoneyOut").jqGrid({
        url: '/manager/moneyOutHistory',
			datatype: function(postdata){
          this.addJSONData(moneyOutHistory);
         },
        mtype: 'GET',
        colNames: ['Дата', 'Сумма', 'Примечания'],
			colModel: [{
				name: 'Date',
				index: 'Date',
				width: 140,
				align: 'center',
				sortable: true
			}, {
				name: 'Summ',
				index: 'Summ',
				width: 140,
				align: 'center',
				sortable: true
			}, {
				name: 'Comment',
				index: 'Comment',
				width: 440,
				align: 'center',
				sortable: true
			}],
        caption: "Вывод денег",
      gridview: true,
      rownumbers: false,
			rowNum: 30,
      forceFit: true,
      toolbar: [true, 'top'],
      pager: "#pagerAccountMoneyOut",
			beforeSelectRow: function(rowid, e){
				if (rowid) {
					if ($("#tableAccountMoneyOut").getRowData(rowid)['Comment'] == "заявка обрабатывается...") 
		  	buttonCancelMoneyOutRequest.attr('disabled', false);
					else 
          	buttonCancelMoneyOutRequest.attr('disabled', true);
		}
        return true;
      }
    });
	
	var buttonCancelMoneyOutRequest = $("<input type='button' value='Отозвать заявку' />");
		buttonCancelMoneyOutRequest.attr('disabled', true).click(function(){
	  $("#dialogCancelRequest").dialog('open');
		});
		$("#t_tableAccountMoneyOut").append(buttonCancelMoneyOutRequest);
	 
    
		
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
                $.ajax({
						url: "/manager/moneyOutRemove?id=" + id + "&token=" + token,
                    dataType: 'json',
                    success: function(result){
                        if (result.error) {
								if (result.error_type == "authorizedError") 
                              window.location.replace("/")
								else 
									if (result.msg) {
                             alert(msg);
                           }
                           else {
                             alert("Неизвестная ошибка.");
                           }
                        }
							else 
                          reloadMoneyOutHistoryGrid();
                    },
                    error: function(error, ajaxOptions, thrownError){
                        alert(error.responseText);
                    }
                });
                buttonApproveMoneyOutRequest.attr('disabled', true);
                $(this).dialog("close");
            },
            "Отмена": function(){
                $(this).dialog("close");
            }
        }
    });
	
		
		/** Перезагружает таблицу истории вывода денежных средств */
		function reloadMoneyOutHistoryGrid(){
			$('#tableAccountMoneyOut').jqGrid('setGridParam', {
				datatype: "json"
			}).jqGrid('setGridParam', {
				url: "/manager/moneyOutHistory"
			}).trigger("reloadGrid");
  }
		
		
		// Таблица заявок на добавление домена
		$("#tableDomainRegistration").jqGrid({
			datatype: function(){
				var data = dataDomainRequests;
				for (var i = 0; i < data.rows.length; i++) {
					data.rows[i].cell.push('<a href="javascript:;" class="actionLink">Одобрить</a>');
					data.rows[i].cell.push('<a href="javascript:;" class="actionLink2">Отклонить</a>');
				}
				this.addJSONData(data);
				$("#tableDomainRegistration .actionLink").click(function(){
					var grid = $("#tableDomainRegistration");
					var rowId = grid.getGridParam('selrow');
					if (rowId == null) 
						return;
					var row = grid.jqGrid('getRowData', rowId);
					var message = "<p>Одобрить домен <b>" + row.domain +
					"</b> для пользователя " +
					row.user +
					"?</p>";
					var dialog = $(message).dialog({
						modal: true,
						buttons: {
							'Да': function(){
								$.getJSON("/manager/approveDomain", {
									user: row.user,
									domain: row.domain,
									approved: 'true',
									token: token
								}, function(data){
								  if (data.error) {
										if (data.error_type == "authorizedError") 
								      window.location.replace("/main/index")
										else 
											if (data.msg) {
								      alert(msg);
								      return;
								    }
								    else {
								      alert("Неизвестная ошибка.");
								      return;
								  }
									}
								  else {
										$.getJSON("/manager/domainsRequests", function(json){
  										dataDomainRequests = json;
  										dialog.dialog('close');
  										login = row.user;
  										$('#tableDomainRegistration').trigger('reloadGrid');
  										openUserDetailsByLogin(login, "edit_domain_categories");
									  });
									}
								})
							},
							'Нет': function(){
								dialog.dialog('close');
							}
						}
					});
				});
				
				
				$("#tableDomainRegistration .actionLink2").click(function(){
					var grid = $("#tableDomainRegistration");
					var rowId = grid.getGridParam('selrow');
					if (rowId == null) 
						return;
					var row = grid.jqGrid('getRowData', rowId);
					var message = "<p>Отклонить заявку на добавление домена <b>" + row.domain +
					"</b> пользователя " +
					row.user +
					"?</p>";
					var dialog = $(message).dialog({
						modal: true,
						buttons: {
							'Да': function(){
								$.getJSON("/manager/rejectDomain", {
									user: row.user,
									domain: row.domain,
									approved: 'true',
									token: token
								}, function(data){
                  if (data.error) {
										if (data.error_type == "authorizedError") 
                      window.location.replace("/main/index")
										else 
											if (data.msg) {
                      alert(msg);
                      return;
                    }
                    else {
                      alert("Неизвестная ошибка.");
                      return;
                  }
									}
                  else {
										$.getJSON("/manager/domainsRequests", function(json){
  										dataDomainRequests = json;
  										dialog.dialog('close');
  										$('#tableDomainRegistration').trigger('reloadGrid');
  									})
  								}
								})
							},
							'Нет': function(){
								dialog.dialog('close');
							}
						}
					});
				});
				
				
				
			},
            colNames: ['Пользователь', 'Дата', 'Домен', 'Примечания', '', ''],
			colModel: [{
				name: 'user',
				index: 'user',
				width: 90,
				align: 'center',
				sortable: true
			}, {
				name: 'date',
				index: 'date',
				width: 100,
				align: 'center',
				sortable: true
			}, {
				name: 'domain',
				index: 'domain',
				width: 180,
				align: 'center',
				sortable: true
			}, {
				name: 'comments',
				index: 'comments',
				width: 400,
				align: 'left',
				sortable: true
			}, {
				name: 'actions',
				index: 'actions',
				width: 80,
				align: 'center',
				sortable: true
			}, {
				name: 'actions',
				index: 'actions',
				width: 80,
				align: 'center',
				sortable: true
			}],
            caption: "Заявки на добавление домена",
			rownumbers: true,
			height: 'auto',
			rownumWidth: 40,
			rowNum: 900
        });
		
		
	}
	
	
	
	// Сводная таблица по пользователям
	function openUserDetails(){
		var login = this.innerText || this.text || this.textContent;
		var div = "userDetails";
      openUserDetailsByLogin(login, div);
    };
    
	function openUserDetailsByLogin(login, div){
      if (permissionRegisterUserAccount) {
			$.getJSON("/manager/checkCurrentUser?token=" + token, function(result){
				if (result.error) 
              window.location.replace("/main/index");
			});
			var url = "/manager/userDetails?login=" + encodeURIComponent(login) +
			"&token=" +
			token +
			"&div=" +
			div;
//      $("#tabs").tabs('remove', $("#tabs").tabs('length') - 1);
        $("#tabs").tabs('remove', 3);
        $("#tabs").tabs('add', url, login);
      }
    }
	
	
	prepareUi();
    $.getJSON("/manager/checkCurrentUser?token=" + token, function(result){
        if (result.error) 
            window.location.replace("/main/index");
	    $("#loading").hide();
	    $("#tabs").css("visibility", "visible");
	    checkDataUpdate();
    });
});

}



function checkDataUpdate(){
    CheckUser();
    $.getJSON("/manager/checkCurrentUser?token=" + token, function(result){
        if (result.error) 
            window.location.replace("/main/index");
    });

    if (permissionViewMoneyOut) {
        var new_notApprovedRequests = 0;
        $.get("/manager/notApprovedActiveMoneyOutRequests", function(res){
            new_notApprovedRequests = res;
            if (Number(new_notApprovedRequests) > 0) {
                $("#href_moneyOutRequests").html('Вывод средств <font color="red"><b> ! </b></font>');
            }
            else {
                $("#href_moneyOutRequests").html("Вывод средств");
            }
            if (notApprovedRequests != new_notApprovedRequests) {
                notApprovedRequests = new_notApprovedRequests
                $("#notApprovedRequests").html(notApprovedRequests);
                $.getJSON("/manager/dataMoneyOutRequests", function(json){
                    dataMoneyOutRequests = json;
                    $('#tableMoneyOutRequest').trigger('reloadGrid');
                });
                
            }
        });
    }
    
    var new_dataDomainRequests;
    $.getJSON("/manager/domainsRequests", function(json){
        new_dataDomainRequests = json
        if (new_dataDomainRequests['records'] > 0) {
            $("#href_moderation").html('Модерация <font color="red"><b> ! </b></font>');
            // Поменять заголовок когда разобрались со всеми заявками!!!
        }
        else {
            $("#href_moderation").html('Модерация');
        }
        if (new_dataDomainRequests != dataDomainRequests) {
            dataDomainRequests = new_dataDomainRequests;
            $("#tableDomainRegistration").trigger('reloadGrid');
        }
    });

    
    setTimeout("checkDataUpdate()", 60000);
    
} // end checkDataUpdate()
