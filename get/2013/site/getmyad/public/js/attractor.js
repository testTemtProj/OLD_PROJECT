var AttractorUI = function(){

    /**
     * Проверяет, не истекла ли текущая сессия пользователя.
     */
    function sessionCheck() {
        $.getJSON('/attractor/session_check', function(response) {
                try {
                    if (!response.ok)
                        window.location.replace('/');
                } catch (TypeError) {
                    window.location.replace('/');
                }
            }
        );
    }

	/** 
	 * Загружает таблицы данными для пользователя username
	 * @param {Object} username		Имя пользователя
	 */
	function loadDataTables(username) {
        sessionCheck();
        data_url = '/attractor/data?site=' + username +
        		   '&start_date=' + $('#calendar1').val() + 
        		   '&end_date=' + $('#calendar2').val();
        if ($("#relative").is(":checked")) {
            data_url = data_url + "&relative=true";
        }
        $('#table_stats_partner').jqGrid('setGridParam', {
            datatype: "json"
        }).clearGridData().jqGrid('setGridParam', {
            url: data_url + "&scope=partners"
        }).trigger("reloadGrid");
        $('#table_stats_other').jqGrid('setGridParam', {
            datatype: "json"
        }).clearGridData().jqGrid('setGridParam', {
            url: data_url + "&scope=others"
        }).trigger("reloadGrid");
	}
	
	/**
	 * Загружает таблицы с данными для текущего (выделеннего) пользователя
	 */
	function loadDataTablesForCurrentUser() {
		loadDataTables(selectedUser());
	}

    /**
    * Возвращает текущего (выделенного) пользователя
    */
    function selectedUser() {
		var tbl = $('#table_user');
		var id =  tbl.getGridParam('selrow');
        var user = tbl.getCell(id, 1);
        return user;
    }
	

    // --------------------------------------------
    // Таблица пользователей Attractor
    // -------------------------------------------- 
    $('#table_user').jqGrid({
        caption: 'Сайты рекламодателей',
        datatype: 'json',
        url: '/attractor/script_users',
        height: 576,
        colNames: ['Пользователь'],
        colModel: [{
            name: 'user',
            index: 'partner',
            width: 250
        }],
        onSelectRow: loadDataTablesForCurrentUser,
		toolbar: [true, 'top'],
        rownumbers: true,
        rowNum: 100
    });

	// Кнопка получения пользовательского кода
	var btnGetUserCode = $("<input type='button' value='Получить код' />");
	btnGetUserCode.click(function(){
		$("#dialogCreateUserScript").dialog('open');
	});
	
	var btnHideUser = $("<input type='button' value='Скрыть' />");
	btnHideUser.click(function(){
        $("#dialogHideUser").dialog('open');
	}); 
	$("#t_table_user").append(btnGetUserCode);
	$("#t_table_user").append(btnHideUser);
	
	// ------- Диалог создания пользователя
	$("#dialogCreateUserScript").dialog({
		autoOpen: false,
		modal: true,
		width: 450,
		buttons: {
			'Получить код': function() {
				$("#textCreateUserScript").val("...");
                $.ajax({
                    type: "get",
                    url: '/attractor/statcodeRequests',
                    data: {'url': $("#urlCreateUserScript").val() },
                    success: function(msg){
                        try {
                            $("#textCreateUserScript").val(msg);
                        } 
                        catch (E) {
                            $("#textCreateUserScript").val("Ошибка: " + E);
                        }
                    }
                });
			}
		}
	});

    // -------- Диалог сокрытия пользователя
    $("#dialogHideUser").dialog({
        autoOpen: false,
        modal: true,
        buttons: {
            'Да': function() {
                $.ajax({
                    type: 'get',
                    url: '/attractor/hideUser',
                    data: {'user': selectedUser()},
                    success: function() {
                        $("#table_user").trigger('reloadGrid');
                        loadDataTablesForCurrentUser();
                        $("#dialogHideUser").dialog('close');
                    }
                })
            },
            'Нет': function() {
                $("#dialogHideUser").dialog('close');
            }
        }
    });
	
	$("#textCreateUserScript").click(function(){
		this.select();
	});

    
    // -------------------------------------------------
    // Таблица с данными о переходах от сайтов-парнёров
    // -------------------------------------------------
    $('#table_stats_partner').jqGrid({
        datatype: 'local',
        colNames: ['Партнер', 'Всего', '< 3', '3-15', '15-30', '> 60',
                   '<acronym title="Глубина считается по людям, полностью загрузившим страницу, поэтому будет отличаться в большую сторону от глубины, которую увидит владелец сайта.">Глубина (?)</acronym>'],
        colModel: [{
            name: 'partner',
            index: 'partner',
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
            width: 50,
            sorttype: "int"
        }, {
            name: 'depth',
            index: 'depth',
            width: 80,
            sorttype: "int"
        }],
        rownumbers: true,
        footerrow: true,
        userDataOnFooter: true,
        caption: 'Переходы с сайтов партнеров GetMyAd',
        height: 240,
        rowNum: 100,
        pager: 'pager_stats_partner'
    });
    
    
    // -----------------------------------------------
    // Таблица с данными о переходах от прочих сайтов
    // -----------------------------------------------
    $('#table_stats_other').jqGrid({
        caption: 'Переходы с других сайтов',
        datatype: 'local',
        colNames: ['Сайт', 'Всего', '< 3', '3-15', '15-30', '> 60', 'Глубина'],
        colModel: [{
            name: 'partner',
            index: 'partner',
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
            width: 50,
            sorttype: "int"
        }, {
            name: 'depth',
            index: 'depth',
            width: 60,
            sorttype: "int"
        }],
        rownumbers: true,
        footerrow: true,
        userDataOnFooter: true,
        height: 240,
        rowNum: 100,
        pager: 'pager_stats_other'
    });
    
    // -----------------------------------------------
    // Фильтры по дате
    // -----------------------------------------------
    var datepickerOptions = {
        duration: 0,
        onSelect: loadDataTablesForCurrentUser
    };
    $("#calendar1").datepicker(datepickerOptions);
    $("#calendar2").datepicker(datepickerOptions);

    // Другие элементы интерфейса
    $("#relative").change(loadDataTablesForCurrentUser);
};

