Template = function(name, data){
    return TrimPath.processDOMTemplate(name, data);
}

String.prototype.getExtendedDate = function() {
    var value = this.toString();
        
    if(value) {
        var matches = value.match(/([0-9]+)/g);
        return {
            datetime:   value,
            timeago:    jQuery.timeago(value),
            year:       matches[0],
            month:      matches[1],
            day:        matches[2],
            hour:       matches[3],
            min:        matches[4],
            sec:        matches[5],
            micro:      matches[6]
        }   
    } else {
        return {datetime:false};
    }   
}


Ext.override(Ext.grid.GridView, {
    holdPosition: false,
    onLoad:function(){
        if (!this.holdPosition) this.scrollToTop();
        this.holdPosition = false;
    }
});

Ext.onReady(function() {
    campaigns = {
        id: 'campaigns',
        title: 'Рекламные кампании',
        onLoad: function() {
            //store.load();
            store.load({ params: { start: 0, limit: 20} });
            window.updateInterval = setInterval(function(){
                campaignGrid.getView().holdPosition = true;
                campaignGrid.getStore().reload();
            }, 5000);
        },
        items: [campaignGrid]
    }
})



	store = new Ext.data.JsonStore({
		url: '/campaign/list',
		root: 'data',
		remoteSort: true,
        autoDestroy: true,
		fields: [
			{
				name: 'id'
			}, {
				name: 'title'
			}, {
				name: 'user'
			}, {
				name: 'started'
			}, {
                name: 'finished'
			}, {
                name: 'last_update'
			}, {
                name: 'statistics'
			}, {
				name: 'state'
			}, {
				name: 'social'
			},{
				name: 'state_Adload'
			},{
				name: 'approved'
			}
		]
	});

	store.setDefaultSort('title', 'asc')

	function startCampaign(campaign_id){
		Ext.Ajax.request({
			url: '/campaign/start',
			success: function(res){
                //TODO убрать, сделать по нормальному
                campaignGrid.getView().holdPosition = true;
                campaignGrid.getStore().reload();
			},
			params: {campaign_id: campaign_id}
		});
	}

    function stopCampaign(campaign_id){
		Ext.Ajax.request({
			url: '/campaign/stop',
			success: function(res){
                //TODO убрать, сделать по нормальному
                campaignGrid.getView().holdPosition = true;
                campaignGrid.getStore().reload();
			},
			params: {campaign_id: campaign_id}
		});
    }

    function approveCampaign(campaign_id){
		Ext.Ajax.request({
			url: '/campaign/approve',
			success: function(res){
                //TODO убрать, сделать по нормальному
                campaignGrid.getView().holdPosition = true;
                campaignGrid.getStore().reload();
			},
			params: {campaign_id: campaign_id}
		});
    }

    function prohibitCampaign(campaign_id){
		Ext.Ajax.request({
			url: '/campaign/prohibit',
			success: function(res){
                //TODO убрать, сделать по нормальному
                campaignGrid.getView().holdPosition = true;
                campaignGrid.getStore().reload();
			},
			params: {campaign_id: campaign_id}
		});
    }

    function refreshCampaign(campaign_id){
		Ext.Ajax.request({
			url: '/campaign/update',
			success: function(res){
                //TODO убрать, сделать по нормальному
                campaignGrid.getView().holdPosition = true;
                campaignGrid.getStore().reload();
			},
			params: {campaign_id: campaign_id}
		});
    }

    // configure whether filter query is encoded or not (initially)
    var encode = true;

    // configure whether filtering is performed locally or remotely (initially)
    var local = false;

    var filters = new Ext.ux.grid.GridFilters({
        // encode and local configuration options defined previously for easier reuse
        encode: encode, // json encode the filter query
        local: local,   // defaults to false (remote filtering)
        filters: [
        {
            type: 'string',
            dataIndex: 'title'
        },
        {
            type: 'string',
            dataIndex: 'user'
        },
        /*
        {
            type: 'date',
            dataIndex: 'started'
        },
        {
            type: 'date',
            dataIndex: 'finished'
        },
        {
            type: 'date',
            dataIndex: 'last_update'
        },
        {
            type: 'string',
            dataIndex: 'statistics'
        },
        */
        {
            type: 'boolean',
            dataIndex: 'state'
        },
        {
            type: 'boolean',
            dataIndex: 'state_Adload'
        },
        {
            type: 'boolean',
            dataIndex: 'social'
        },
        {
            type: 'boolean',
            dataIndex: 'approved'
        }
        ]
    });

	campaignGrid = new Ext.grid.GridPanel({
        layout: 'fit',
		store: store,
        plugins: [filters],       
		listeners: {
			render: {
				fn: function() {
					 Ext.getBody().on("contextmenu", Ext.emptyFn,
						null, {preventDefault: true});
				}
			}
		},
        //TODO можно задавать класс для ячеек и ставить background
        //     в этом случае надо проверить как будет вести себя картинка при изменении количества
        //     ячеек на странице, т.е. фактически при изменении высоты ячеек
		colModel: new Ext.grid.ColumnModel({
			defaults: {
				width: 120,
				sortable: true
			},
			columns: [
				{
					header: 'Название',
                    width: 300,
					sortable: true,
					dataIndex: 'title',
					id: 'title'
				},{
					id: 'user',
					header: 'Логин',
					sortable: true,
					dataIndex: 'user'
				},{
					header: 'Запущена',
					width: 100,
					sortable: true,
					dataIndex: 'started',
                    renderer: function(value, metaData, record, rowINdex, colIndex, store){
                        if (value == 'None'){
                            return '';
                        }
                        return value;
                    }
				},{
					header: 'Остановлена',
					width: 100,
					sortable: true,
					dataIndex: 'finished',
                    renderer: function(value, metaData, record, rowINdex, colIndex, store){
                        if (value == 'None'){
                            return '';
                        }
                        return value;
                    }
				},{
					header: 'Обновлена',
					width: 100,
					sortable: true,
					dataIndex: 'last_update',
                    renderer: function(value, metaData, record, rowINdex, colIndex, store){
                        if (value == 'None'){
                            return '';
                        }
                        return value;
                    }
				},{
					header: 'Статистика',
					width: 130,
					sortable: true,
					dataIndex: 'statistics',
                    renderer: function(value, metaData, record, rowINdex, colIndex, store){
                        if (!value)
                            return ''
                        result = 'Соп. кат.: ' + value.compared_categories;   
                        result += '<br/>'
                        result += 'Несоп. кат.: ' + value.not_compared_categories;
                        result += '<br/>'
                        result += 'Получ. тов.: ' + value.total_offers;
                        result += '<br/>'
                        result += 'Загр. тов: ' + value.valid_offers;
                        result += '<br/>'
                        result += 'С ошиб.: ' + value.not_valid_offers;
                        return result;
                    }
				},{
					header: 'Статус',
					width: 80,
					sortable: true,
					dataIndex: 'state',
					id: 'state',
                    renderer: function(value, metaData, record, rowIndex, colIndex, store){
                        var campaign_status = value.status;
                        switch(campaign_status){
                            case 'started':
                                value = '<img src="/img/start.png"/>';
                                break;
                            case 'in_process':
                                value = '<img src="/img/update.png"/>';
                                break;
                            default:
                                value = '<img src="/img/stop.png"/>';
                        }
                        return value;
                    }
				},{
					header: 'AdLoad',
					width: 80,
					sortable: true,
					dataIndex: 'state_Adload',
					id: 'state_Adload',
                    renderer: function(value, metaData, record, rowIndex, colIndex, store){
                        if(value){
                            value = '<img src="/img/start.png"/>';
                        } else {
                            value = '<img src="/img/stop.png"/>';
                        }
                        return value;
                    }
				},{
					header: 'Cоциальная',
					width: 80,
					sortable: true,
					dataIndex: 'social',
					id: 'social',
                    renderer: function(value, metaData, record, rowIndex, colIndex, store){
                        if(value){
                            value = '<img src="/img/yes.png"/>';
                        } else {
                            value = '<img src="/img/no.png"/>';
                        }
                        return value;
                    }
				},{
					header: 'Одобрена',
					width: 80,
					sortable: true,
					dataIndex: 'approved',
					id: 'approved',
                    renderer: function(value, metaData, record, rowIndex, colIndex, store){
                        if(value){
                            value = '<img src="/img/yes.png"/>';
                        } else {
                            value = '<img src="/img/no.png"/>';
                        }
                        return value;
                    }
				}]
		}),
        contextMenu: new Ext.menu.Menu({
                items: [
                    {
                        id:   'start',
                        text: 'Запустить',
                        icon: '/img/start.png',
                        hidden: true
                    },
                    {
                        id:   'stop',
                        text: 'Остановить',
                        icon: '/img/stop.png',
                        hidden: true
                    },
                    {
                        id:   'refresh',
                        text: 'Обновить',
                        icon: '/img/update.png',
                        hidden: false
                    },
                    {
                        id:   'approve',
                        text: 'Одобрить',
                        icon: '/img/yes.png',
                        hidden: true
                    },
                    {
                        id:   'prohibit',
                        text: 'Запретить',
                        icon: '/img/no.png',
                        hidden: true
                    }
                ],
                listeners:{
                      itemclick: function(item){
                                 var currentRow = item.parentMenu.currentRow;
                                 if (!currentRow) {
                                     Ext.Msg.alert("Ошибка", "Ни одна строка не выбрана");
                                     return;
                                 }
                                 switch(item.id){
                                     case 'start':
                                         startCampaign(currentRow.data.id);
                                         break;
                                     case 'stop':
                                         stopCampaign(currentRow.data.id);
                                         break;
                                     case 'approve':
                                         approveCampaign(currentRow.data.id);
                                         break;
                                     case 'prohibit':
                                         prohibitCampaign(currentRow.data.id);
                                         break;
                                     case 'refresh':
                                         refreshCampaign(currentRow.data.id);
                                         break;
                                     default:
                                         return;
                                 }
                             }
                  }

        }),
		sm: new Ext.grid.RowSelectionModel({singleSelect:true}),
        region: 'center',
		autoWidth: true,
		title: 'Рекламные кампании',
		iconCls: 'icon-grid',
		loadMask: true,
		clicksToEdit:'1',
        tbar: new Ext.Toolbar({
            items: [
                {
                    text: 'Поиск магазина:',
                    xtype: 'label'
                },
                {
                    xtype:'tbseparator'
                },
                {
                    xtype:'textfield',
                    fieldLabel:'Search',
                    name: 'pattern',
                    id:'pattern',
                    listeners: {
                        'render': function(c) {
                            c.getEl().on('keypress', function(e) {
                                if(e.getKey() == e.ENTER) {
                                    store.baseParams.pattern = document.getElementById('pattern').value;                                    
                                    store.load();
                                }
                            });
                        }
                    }
                }
            ]
        }),
		bbar: new Ext.Toolbar({
            items: [
                new Ext.PagingToolbar({
                    id: 'paging-toolbar',
                    plugins: [filters],
                    pageSize: 20,
                    store: store,
                    displayInfo: true,
                    displayMsg: 'Показано {0} - {1} из {2}'
                }),
                {
                    text: 'Автообновление',
                    xtype: 'label'
                },
                {
                    id:'auto-update-time',
                    xtype: 'combo',
                    triggerAction: 'all',
                    autoSelect: true,
                    width: 100,
                    forceSelection: true,
                    editable: false,
                    lazyRender:true,
                    mode: 'local',
                    value: 0,
                    valueField: 'interval',
                    displayField: 'title',
                    store: new Ext.data.ArrayStore({
                        id: 1,
                        fields: [
                            'interval', 'title'
                        ],
                        data: [
                            [0, 'отключено'],
                            [5000, 'каждые 5 секунд'], 
                            [600000, 'раз в 10 минут'],
                            [1200000, 'раз в 20 минут'],
                            [36000000, 'раз в 1 час'],
                            [72000000, 'раз в 2 часа'],
                            [360000000, 'раз в 10 часов']
                        ]
                    }),
                    listeners:{
                         select: function(intervalSizeCombo){
                             if (window.updateInterval)
                                clearInterval(window.updateInterval);

                             if(intervalSizeCombo.value > 0)
                                window.updateInterval = setInterval(function(){
                                     campaignGrid.getView().holdPosition = true;
                                    campaignGrid.getStore().reload()
                                }, intervalSizeCombo.value);
                         }
                    }
                },{
                    text: 'Показать: ',
                    xtype: 'label'
                },{
                    xtype: 'combo',
                    triggerAction: 'all',
                    autoSelect: true,
                    width: 50,
                    forceSelection: true,
                    editable: false,
                    lazyRender:true,
                    mode: 'local',
                    value: 20,
                    valueField: 'pageSize',
                    displayField: 'pageSize',
                    store: new Ext.data.ArrayStore({
                        id: 1,
                        fields: [
                            'pageSize'
                        ],
                        data: [[20], [50], [100]]
                    }),
                    listeners:{
                         select: function(pageSizeCombo){
                             Ext.getCmp('paging-toolbar').pageSize = pageSizeCombo.value;
                             store.baseParams.limit = pageSizeCombo.value;
                             store.baseParams.start = 0
                             console.log(pageSizeCombo.value);
                             store.load();                             
                         }
                    }
                }
            ]}),
        viewConfig: {forceFit: true},
        loadMask: false,
        listeners: {
            rowcontextmenu: function(grid, index, e){
                                e.stopEvent();
                                this.getSelectionModel().selectRow(index);
                                // показываем элементы меню в зависимости от строки   
                                this.contextMenu.items.each(function(item){ 
                                    if(item.id != 'refresh')
                                        item.hide();
                                    item.enable();
                                });
                                var currentRow = this.getSelectionModel().getSelected();

                                switch(currentRow.data.state.status){
                                    case 'started':
                                        this.contextMenu.getComponent('stop').show();
                                        break;
                                    case 'stopped':
                                        var component = this.contextMenu.getComponent('start');
                                        component.show();
                                        if (!currentRow.data.state_Adload || !currentRow.data.approved)
                                            component.disable();
                                            this.contextMenu.getComponent('refresh').disable();
                                        break;
                                    default:
                                        this.contextMenu.getComponent('stop').show();
                                        this.contextMenu.getComponent('stop').disable();
                                        this.contextMenu.getComponent('refresh').disable();
                                        this.contextMenu.getComponent('prohibit').disable();
                                        break;
                                }
                                if(currentRow.data.approved){
                                    this.contextMenu.getComponent('prohibit').show();
                                } else {
                                    this.contextMenu.getComponent('approve').show();
                                }
                                this.contextMenu.currentRow = currentRow;
                                this.contextMenu.showAt(e.getXY());
                            }
        }

	});
    campaignGrid.on('headerclick',function(x, columnIndex,  e ){
        store.baseParams.start = 0
        store.load()
        });
    var update_select = Ext.getCmp('auto-update-time');
    update_select.setValue(5000);
