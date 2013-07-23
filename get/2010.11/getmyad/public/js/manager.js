var ManagerUI = function(){
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
		$("#dialogSetCost").dialog({
			autoOpen: false,
			modal: true,
			buttons: {
				'Назначить': function(){
					if (!checkFloat($("#dialogSetCost_cost"))) {
						alert('Неправильный формат цены!');
						return;
					}
					$.getJSON("/manager/setClickCost", {
						cost: $("#dialogSetCost_cost").val(),
						date: $("#dialogSetCost_date").val(),
						user: $("#dialogSetCost_user").html(),
						token: token
					}, function(data){
						  if (data.error) {
							if (data.error_type == "authorizedError") 
						      window.location.replace("/main/index");
							else 
								if (data.msg) {
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
				if (rowid) 
					setPercentButton.attr('disabled', false);
				return true;
			}
		});
		$("#managersSummary").jqGrid('navGrid', '#toolbarManagersSummary', {
			edit: false,
			add: false,
			del: false
		});
		var setPercentButton = $("<div style=><input type='button' value='Назначить процент'/></div>");
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
		
		
		// Таблица цен за уникального посетителя
		$("#tableClickCost").jqGrid({
			datatype: function(postdata){
				this.addJSONData(currentClickCost);
			},
      mtype: 'GET',
      colNames: ['Пользователь', 'Цена', 'Действует с'],
			colModel: [{
				name: 'user',
				index: 'user',
				width: 180,
				align: 'center'
			}, {
				name: 'cost',
				index: 'cost',
				width: 90,
				align: 'center'
			}, {
				name: 'date',
				index: 'date',
				width: 120,
				align: 'center'
			}],
      viewrecords: true,
      caption: "Текущие цены за уникального посетителя",
			gridview: true,
			rownumbers: true,
			height: 420,
			rownumWidth: 40,
			rowNum: 200,
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
			},
			onSortCol: function(index, iCol, sortorder){
				
				
				if (sortorder == 'desc') 
					sortorder = 'True';
				else 
					sortorder = 'False';
				function reloadClickCostGrid(){
                $('#tableClickCost').jqGrid('setGridParam', {
                    datatype: "json"
                }).jqGrid('setGridParam', {
                    url: "/manager/currentClickCost?sortCol=" + iCol + "&sortRevers=" + sortorder
                }).trigger("reloadGrid");
            }
			reloadClickCostGrid();
			}
        });
		
		var setCostButton = $("<input type='button' value='Назначить цену' />");
		$("#tableClickCost").jqGrid('navGrid', '#toolbarClickCost', {
			edit: false,
			add: false,
			del: false
		});
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
			
			var dateString = day + "." + month + "." + date.getFullYear() + " " +
			hours +
			":00";
			$("#dialogSetCost_user").html(row.user);
			$('#dialogSetCost_cost').val(row.cost);
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
				for (var i = 0; i < dataMoneyOutRequests.rows.length; i++) {
              var cell = dataMoneyOutRequests.rows[i].cell;
              var login = cell[0];
              cell[0] = '<a href="javascript:;" class="actionLink">' + login + '</a>';
              }
            this.addJSONData(dataMoneyOutRequests);
				$('#tableMoneyOutRequest .actionLink').click(openUserDetails);
			},
      colNames: ['Пользователь', 'Дата', 'Сумма', 'Подтверждено', 'Одобрено', 'Телефон', 'Оплата', 'Примечания'],
			colModel: [{
				name: 'user',
				index: 'user',
				width: 110,
				align: 'center',
				sortable: true
			}, {
				name: 'date',
				index: 'date',
				width: 130,
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
				width: 140,
				align: 'center',
				sortable: true
			}, {
				name: 'paymentType',
				index: 'paymentType',
				width: 100,
				align: 'center',
				sortable: true
			}, {
				name: 'comments',
				index: 'comments',
				width: 400,
				align: 'left',
				sortable: true
			}],
      caption: "Заявки на вывод средств",
			rownumbers: true,
			height: '600',
			rownumWidth: 40,
			rowNum: 200,
			pager: "#pagerMoneyOutRequest",
			forceFit: true,
			toolbar: [true, 'top'],
			beforeSelectRow: function(rowid, e){
				if (!rowid) 
					return false;
				var row = $("#tableMoneyOutRequest").jqGrid('getRowData', rowid);
				if (row.approved == 'Да' || row.user_confirmed == 'Нет') 
					buttonApproveMoneyOutRequest.attr('disabled', true)
				else 
					buttonApproveMoneyOutRequest.attr('disabled', false)
				return true;
			}
        });
		
		$("#tableMoneyOutRequest").jqGrid('navGrid', '#toolbarMoneyOut', {
			edit: false,
			add: false,
			del: false
		});
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
		});
		
		$("#t_tableMoneyOutRequest").append(buttonApproveMoneyOutRequest);
		
		
		// Таблица о сводной статистике по дням
        $("#tableOverallSummary").jqGrid({
            datatype: function(postdata){				
                this.addJSONData(dataOverallSummary);
            },
            mtype: 'GET',
            colNames: ['Дата', 'Показы', 'Клики', 'Доход', 'CTR', 'Цена'],
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
            footerrow: true,
            userDataOnFooter: false
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
        colNames: ['Пользователь', 'Сегодня', 'Вчера', 'Позавчера', 'За неделю', 'За месяц', 'За год', 'CTR за 7 дней, %', 'Сумма на счету'],
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
			rowNum: 200,
      footerrow: true,
      userDataOnFooter: true,
	  onSortCol: function(index, iCol, sortorder){
          $('#tableUsersSummary').jqGrid('setGridParam', {
              datatype: "json"
          }).jqGrid('setGridParam', {
              url: "/manager/dataUsersSummary?sortCol=" + iCol + "&sortRevers=" + sortorder
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
      rowNum: 200,
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
		$("#tableAccountMoneyOut").jqGrid('navGrid', '#toolbarAccountMoneyOut', {
			edit: false,
			add: false,
			del: false
		});
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
			rowNum: 200
        });
		
		
	}
	
	
	
	// Сводная таблица по пользователям
	function openUserDetails(){
		var login = this.innerText || this.text;
		var div = "userDetails";
//		alert(login);
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
  //    $("#tabs").tabs('remove', $("#tabs").tabs('length'));
        $("#tabs").tabs('remove', 4);
        $("#tabs").tabs('add', url, login);
                              
      }
    }
	
	
	prepareUi();
	$("#loading").hide();
	$("#tabs").css("visibility", "visible");
	checkDataUpdate();
	
	/*
	 * Получение кода статистики
	 *
	 */
	$("#btnCodeGen").click(function(){
		var url = $("#site_url").val();
		$("#StatCode").val("Подождите...");
        $.ajax({
		        type: "get",
		        url: '/manager/statcodeRequests',
			data: 'url=' + url,
			success: function(msg){
					try {
						$("#StatCode").val(msg);
				} 
				catch (E) {
					$("#StatCode").val("Ошибка: " + E);
					}
		           }
		});
		
	});
	
	
	$.getJSON('/manager/statcodeDomains', {}, function(json){
		for (var i = 0; i < json.length; i++) {
		//$('#domain_with_script').append('<option>' + json[i] + '</option>');	
			$('#domain_with_script').append('<option value="' + json[i].url + '">' + json[i].date + ':' + json[i].url + '</option>');
	}
	});
	$("#domain_with_script").click(function(){
	var url = $("#domain_with_script :selected").val();
		$("#site_url").val(url);
	$("#StatCode").val("Подождите...");
        $.ajax({
		        type: "get",
		        url: '/manager/statcodeRequests',
			data: 'url=' + url,
			success: function(msg){
					try {
						$("#StatCode").val(msg);
				} 
				catch (E) {
					$("#StatCode").val("Ошибка: " + E);
					}
		           }
		});
	});
	
	var x;
	var gid = 0;
	var all;
	
    function data_src(){
		 var id = gid;
		var page=0;
		
        var domain_url = $('#table_user').getCell(id, 1);
        var domain = '/stat/get_data?site=' + domain_url +
        '&start_date=' +
        $('#calendar1').val() +
        '&end_date=' +
        $('#calendar2').val() +
        '&p=' +
        page;
        return domain;
    }
	function prc(){
    var id = gid;
    i = 0;
	var page = $('#le_pager2').reccount;
	//$("#le_table_all").getGridParam("rowNum");	
    domain_url = $('#table_user').getCell(id, 1);
    domain = '/stat/get_data?site=' + domain_url +
    '&start_date=' +
    $('#calendar1').val() +
    '&end_date=' +
    $('#calendar2').val()+
	'&page=' + page; 	   
    $.getJSON(domain, {}, function(json){
        all = json;
        var time3 = 0;
        var time15 = 0;
        var time30 = 0;
        var time60 = 0;
        var timeall = 0;
        var gtime3 = 0;
        var gtime15 = 0;
        var gtime30 = 0;
        var gtime60 = 0;
        var gtimeall = 0;
        var p3 = 0;
        var p15 = 0;
        var p30 = 0;
        var p60 = 0;
		var percent_depth1 = 0;
		var percent_depth2 = 0;
		var percent_depth3 = 0;
		var percent_depth4 = 0;
		var dtotal = 0;
		$('#le_table').clearGridData();
        $('#le_table_all').clearGridData();
        if (document.getElementById('check_percent').checked) {
            for (i = 0; i < json.length; i++) {
                 if (json[i].site == "None" || json[i].site == "") {
				 	json[i].site = "Unknown";
				 }
                total = json[i].time3 +
                json[i].time15 +
                json[i].time30 +
                json[i].time60;
                time3 += json[i].time3;
                time15 += json[i].time15;
                time30 += json[i].time30;
                time60 += json[i].time60;
                timeall += total;
				
                dtotal = json[i].depth1 + json[i].depth2 + json[i].depth3 +json[i].depth4; 
                
                
                if (json[i].time3 == 0) 
                    p3 = "0";
                else 
                    p3 = Math.floor(json[i].time3 / total * 100);
                if (json[i].time15 == 0) 
                    p15 = "0";
                else 
                    p15 = Math.floor(json[i].time15 / total * 100);
                if (json[i].time30 == 0) 
                    p30 = "0";
                else 
                    p30 = Math.floor(json[i].time30 / total * 100);
                if (json[i].time60 == 0) 
                    p60 = "0";
                else 
                    p60 = Math.floor(json[i].time60 / total * 100);
                
                if (json[i].depth1 == 0) 
                    percent_depth1 = 0;
                else 
                    percent_depth1 = Math.floor(json[i].depth1 / dtotal * 100);
                
                if (json[i].depth2 == 0) 
                    percent_depth2 = 0;
                else 
                    percent_depth2 = Math.floor(json[i].depth2 / dtotal * 100);
                if (json[i].depth3 == 0) 
                    percent_depth3 = 0;
                else 
                    percent_depth3 = Math.floor(json[i].depth3 / dtotal * 100);
                if (json[i].depth4 == 0) 
                    percent_depth4 = 0;
                else 
                    percent_depth4 = Math.floor(json[i].depth4 / dtotal * 100);			
                if (json[i].from_getmyad == true) {
                
                
                    $('#le_table').addRowData(i, {
							'id': i + 1,
                    'parther': json[i].site.replace(/_/g, "."),
                    'time_percent_3': (p3 + ' %'),
                    'time_percent_15': (p15 + ' %'),
                    'time_percent_30': (p30 + ' %'),
                    'time_percent_60': (p60 + '%'),
                    'time_all': ("100 %"),
					'depth1':percent_depth1,
					'depth2':percent_depth2,
					'depth3':percent_depth3,
					'depth4':percent_depth4,
                    });
                }
					else 
				$('#le_table_all').addRowData(i, {
                    'id': i + 1,
                    'parther': json[i].site.replace(/_/g, "."),
                    'time_percent_3': (p3 + ' %'),
                    'time_percent_15': (p15 + ' %'),
                    'time_percent_30': (p30 + ' %'),
                    'time_percent_60': (p60 + '%'),
                    'time_all': ("100 %")
                });
                
            }
        }
        else {
            for (i = 0; i < json.length; i++) {
                total = json[i].time3 +
                json[i].time15 +
                json[i].time30 +
                json[i].time60;
                time3 += json[i].time3;
                time15 += json[i].time15;
                time30 += json[i].time30;
                time60 += json[i].time60;
                timeall += total;
                 if (json[i].site == "None" || json[i].site == "") {
				 	json[i].site = "Unknown";
				 }
               
                
                if (json[i].from_getmyad == true) {
                    gtime3 += json[i].time3;
                    gtime15 += json[i].time15;
                    gtime30 += json[i].time30;
                    gtime60 += json[i].time60;
                    gtimeall += total;
                    $('#le_table').addRowData(i, {
                        'id': i + 1,
                        'parther': json[i].site.replace(/_/g, "."),
                        'time_percent_3': json[i].time3,
                        'time_percent_15': json[i].time15,
                        'time_percent_30': json[i].time30,
                        'time_percent_60': json[i].time60,
                        'time_all': total,
						'depth1':json[i].depth1,
						'depth2':json[i].depth2,
						'depth3':json[i].depth3,
						'depth4':json[i].depth4,
                    });
                }
					else 
				 $('#le_table_all').addRowData(i, {
                    'id': i + 1,
                    'parther': json[i].site.replace(/_/g, "."),
                    'time_percent_3': json[i].time3,
                    'time_percent_15': json[i].time15,
                    'time_percent_30': json[i].time30,
                    'time_percent_60': json[i].time60,
                    'time_all': total
                });
            }
        }
        $("#le_table_all").footerData('set', {
            'parther': "ИТОГО:",
            'time_percent_3': time3,
            'time_percent_15': time15,
            'time_percent_30': time30,
            'time_percent_60': time60,
            'time_all': timeall
        }, true);
        $("#le_table").footerData('set', {
            'parther': "ИТОГО:",
            'time_percent_3': gtime3,
            'time_percent_15': gtime15,
            'time_percent_30': gtime30,
            'time_percent_60': gtime60,
            'time_all': gtimeall
        }, true);
		});
	};
	$(function(){
    var domain_url;
    var i = 0;
    var currentTime = new Date()
    var month = currentTime.getMonth() + 1
    var month1 = currentTime.getMonth()
    var day = currentTime.getDate()
    var year = currentTime.getFullYear()
    $("#calendar1").attr("value", day + "." + month1 + "." + year);
    $("#calendar2").attr("value", day + "." + month + "." + year);
    $("#calendar1").datepicker();
    $("#calendar2").datepicker();
    $('#le_table').jqGrid({
        datatype: 'local',
        colNames: ['ID', 'Партнер', 'Всего', '<3', '3-15', '15-30', 'Больше минуты', '1 стр.', '2 стр.', '3 стр.', 'Больше'],
        colModel: [{
            name: 'id',
            index: 'id',
            width: 50
        }, {
            name: 'parther',
            index: 'parther',
            width: 250
        }, {
            name: 'time_all',
            index: 'time_all',
            width: 100,
            sorttype: "int"
			}, {
            name: 'time_percent_3',
            index: 'time_percent_3',
            width: 50,
            sorttype: "int"
        }, {
            name: 'time_percent_15',
            index: 'time_percent_15',
            width: 50,
            sorttype: "int"
        }, {
            name: 'time_percent_30',
            index: 'time_percent_30',
            width: 50,
            sorttype: "int"
        }, {
            name: 'time_percent_60',
            index: 'time_percent_60',
            width: 110,
            sorttype: "int"
		}, {
			name: 'depth_1',
            index: 'depth__1',
            width: 50,
            sorttype: "int"
		}, {
			name: 'depth_2',
            index: 'depth__2',
            width: 50,
            sorttype: "int"
		}
		, {
			name: 'depth_3',
            index: 'depth__3',
            width: 50,
            sorttype: "int"
		}
		, {
			name: 'depth_4',
            index: 'depth__4',
            width: 110,
            sorttype: "int"
		}
			],
        footerrow: true,
        userDataOnFooter: true,		
        caption: 'Количество переходов с сайтов партнеров GetMyAd',
			height: 340
    });
    $('#table_user').jqGrid({
        datatype: 'local',
			height: 340,
        colNames: ['ID', 'Пользователи'],
        colModel: [{
            name: 'id',
            index: 'id',
            width: 20
        }, {
            name: 'user',
            index: 'parther',
            width: 250
        }],
        caption: 'Сайты рекламодателей',
        onSelectRow: function(id){
            gid = id;
            prc();
        }
    });
    $('#le_table_all').jqGrid({
        url:data_src(),
		datatype: "json",
        colNames: ['ID', 'Сайт',  'Всего', '<3', '3-15', '15-30', 'Больше минуты', "1 стр", "2 стр", "3 стр", "Больше"],
        colModel: [{
            name: 'id',
            index: 'id',
            width: 50,
			sorttype: "int"
        }, {
            name: 'parther',
            index: 'parther',
            width: 250
        }, {
            name: 'time_all',
            index: 'time_all',
            width: 160,
            sorttype: "int"
			}, {
            name: 'time_percent_3',
            index: 'time_percent_3',
            width: 60,
            sorttype: "int"
        }, {
            name: 'time_percent_15',
            index: 'time_percent_15',
            width: 60,
            sorttype: "int"
        }, {
            name: 'time_percent_30',
            index: 'time_percent_30',
            width: 60,
            sorttype: "int"
        }, {
            name: 'time_percent_60',
            index: 'time_percent_60',
            width: 120,
            sorttype: "int"
        }, {
			name: 'depth_1',
            index: 'depth__1',
            width: 50,
            sorttype: "int"
		}, {
			name: 'depth_2',
            index: 'depth__2',
            width: 50,
            sorttype: "int"
		}
		, {
			name: 'depth_3',
            index: 'depth__3',
            width: 50,
            sorttype: "int"
		}
		, {
			name: 'depth_4',
            index: 'depth__4',
            width: 110,
            sorttype: "int"
		}],
        footerrow: true,
        userDataOnFooter: true,
		rowNum:50,
   		rowList:[50,100,200],
		pager: '#le_pager2',
        caption: 'Количество трафика с всех сайтов на рекламодателя',
			height: 500
    });
	$("#le_table_all").jqGrid('navGrid','#le_pager2',{edit:false,add:false,del:false});
    $.getJSON('/stat/domains', {}, function(json){
    
        for (i = 0; i < json.length; i++) {
				$('#selectsite').append('<option value=' + json[i].url + '>' + json[i].date + ':' + json[i].url + '</option>');
            $('#table_user').addRowData(i, {
                'id': i + 1,
                'user': json[i],
            });
        }
    });
    $('#check_percent').click(function(){
        prc();
    });
	});
});

function checkDataUpdate(){
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
      
	$.getJSON("/manager/checkCurrentUser?token=" + token, function(result){
		if (result.error) 
                    window.location.replace("/main/index");
	});
      setTimeout("checkDataUpdate()", 60000);
	
}
}
