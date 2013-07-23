Ext.EventManager.onDocumentReady(function(){
	
	var paramsArray = {}
	
	var store = new Ext.data.JsonStore({
		url: '/parser_settins/get_markets',
		root: 'data',
		fields: [
			{
				name: 'id'
			},{
				name: 'title'
			}, {
				name: 'urlMarket'
			}, {
				name: 'urlExport'
			},{
				name: 'last_update'
			},{
				name: 'interval'
			}
		]
	
	});
	store.load()
	
	var isSpKey = false
	
	var shopUrlEditor = new Ext.form.TextField({
		allowBlank: false
	})
	
	shopUrlEditor.on('beforerender',function(){
		this.shop_id = grid.getSelectionModel().getSelected().id
	})
	
	shopUrlEditor.on('specialkey',function(){
		isSpKey = true
		shopUrlEditor.shopUrl = this.getValue()
	})
	
	shopUrlEditor.on('change',function(obg, newValue, oldValue){
		id = this.shop_id
		if(isSpKey == true)
		{
			var newValue = shopUrlEditor.shopUrl
			isSpKey = false
		}
		Ext.Ajax.request({
			url: '/parser_settins/set_shop_url',
			params: { market_id: id, value: newValue}
		}); 
	})
	
	var isSKey = false
	
	var shopExportUrlEditor = new Ext.form.TextField({
		allowBlank: false
	})
	
	shopExportUrlEditor.on('beforerender',function(){
		this.shop_id = grid.getSelectionModel().getSelected().id
	})
	
	shopExportUrlEditor.on('specialkey',function(){
		isSKey = true
		shopUrlEditor.shopUrl = this.getValue()
	})
	
	shopExportUrlEditor.on('change',function(obg, newValue, oldValue){
		id = this.shop_id
		if(isSKey == true)
		{
			var newValue = shopUrlEditor.shopUrl
			isSKey = false
		}
		Ext.Ajax.request({
			url: '/parser_settins/set_shop_export_url',
			params: { market_id: id, value: newValue}
		}); 
	})
	
	var grid = new Ext.grid.EditorGridPanel({
		store: store,
		colModel: new Ext.grid.ColumnModel({
			defaults: {
				width: 120,
				sortable: true
			},
			columns: [
				{
					header: 'ID',
					width: 30, 
					sortable: true,  
					dataIndex: 'id'	
				},{
					id: 'title',
					header: 'Название магазина', 
					width: 120,
					sortable: true, 
					dataIndex: 'title'
				},{
					header: 'URL магазина',
					width: 250, 
					sortable: true,  
					dataIndex: 'urlMarket',
					editor: shopUrlEditor
				},{
					header: 'URL файла выгрузки', 
					width: 330, 
					sortable: true, 
					dataIndex: 'urlExport',
					editor: shopExportUrlEditor
				},{
					header: 'Последнее обновление', 
					width: 150, 
					sortable: true, 
					dataIndex: 'last_update'
				},{
                xtype: 'actioncolumn',
                id: 'date',
                width: 50,
                items: [{
						icon   : '/img/date.png',
						handler: function(grid, rowIndex, colIndex) {
							var rec = store.getAt(rowIndex)
							window.market_id = rec.get('id')
							win.show()
						}
					}]
				}, {
                xtype: 'actioncolumn',
                id: 'action',
                width: 50,
                items: [{
						icon   : '/img/reload.png',
						handler: function(grid, rowIndex, colIndex) {
							var rec = store.getAt(rowIndex)
							id = rec.get('id')
							rec.set('status','<p style="color: red">Идет парсинг</p>')
							Ext.Ajax.request({
								url: '/parser_settins/start_parsing_market',
								timeout: 500000,
								success: function(res){
									data = eval( "(" + res.responseText + ")" )
									if(data['error'])
									{
										rec.set('status','<p style="color: red">Не верный формат файла выгрузки</p>')
									}
									else
									{
										rec.set('status','<p style="color: green">Добавлено товаров: '+data['add']+'</p><p style="color:red"> Удалено товаров: '+data['deleted']+'</p><p style = "color: blue"> Добавлено категорий: '+data['cat']+'</p>')
										//rec.set('action','')
									}
								},
								params: { market_id: id, ololo: 0 }
							}); 
						}
					}]
				},{
					header: 'Состояние', 
					width: 330, 
					sortable: true, 
					id: 'status',
					dataIndex: 'status'
				},
			],
		}),
		sm: new Ext.grid.RowSelectionModel({singleSelect:true}),
		height: 660,
		frame: true,
		title: 'Магазины',
		iconCls: 'icon-grid',
		loadMask: true,
		clicksToEdit:'1',
		bbar: new Ext.PagingToolbar({
            pageSize: 20,
            store: store,
            displayInfo: true,
            displayMsg: 'Показано {0} - {1} из {2}',
        })
	});
	grid.render('markets');
	
	var cbMain = new Ext.form.ComboBox({
		fieldLabel: 'Раз в',
		store: ['год', 'месяц', 'неделю', 'день', 'час'],
		value: 'год',
		editable: true,
		mode: 'remote',
		forceSelection: true,
		triggerAction: 'all',
		selectOnFocus: true,
	})
	
	cbMain.on('select',function(obg, x, r){
		var value = cbMain.getValue()
		if (value == 'год')
		{
			nfMain.setDisabled(false)
		}
		else if(value == 'месяц')
		{
			nfMain.setMaxValue(30)
			nfMain.setDisabled(false)
		}
		else if(value == 'неделю')
		{
			nfMain.setMaxValue(6)
			nfMain.setDisabled(false)
		}
		else if(value == 'день')
		{
			nfMain.setMaxValue(23)
			nfMain.setDisabled(false)
		}
		else if(value = 'час')
		{
			nfMain.setDisabled(true)
			win.buttons[0].setVisible(false)
			win.buttons[1].setVisible(true)
			paramsArray['interval'] = 'час'
			paramsArray['interval_count'] = 1
		}
		
		// месяц 30
		// неделя 6
		// день 23
	})
	
	var nfMain = new Ext.form.NumberField({
		fieldLabel: 'Кол-во раз',
		value: 1,
        minValue: 1
	})
	
	nfMain.on('change',function(){
		if(nfMain.isValid())
		{
			win.buttons[0].setDisabled(false)
			lMain.setVisible(false)
		}
		else
		{
			win.buttons[0].setDisabled(true)
			lMain.setVisible(true)
		}
	})
	
	var lMain = new Ext.form.Label({
		html: "<p style = 'color: red'>Oh Fuck! Oh my Fucking GOD it's some error here!!! Open your fucking eyes!!!</p>",
		
	})
	lMain.setVisible(false)
	
	var form = new Ext.FormPanel({
        labelWidth: 100,
        frame:false,
        bodyStyle:'padding:5px 5px 0',
        defaultType: 'textfield',
		labelAlign: 'left',
        items: [cbMain, nfMain, lMain],
    });
	
	var win = new Ext.Window({
	layout:'fit',
	width:500,
	height:217,
	closeAction:'hide',
	plain: true,
	items: [form],
	buttons: [{
		text:'Далее',
		name: 'next',
		handler: function(){
			var cbMainValue = cbMain.getValue()
			var nfMainValue = nfMain.getValue()
			
			paramsArray['interval'] = cbMainValue
			paramsArray['interval_count'] = nfMainValue
			
			var items = []
			if (cbMainValue == 'год')
			{
				for(var i = 0; i < nfMainValue; i++)
				{
					var label = lMain = new Ext.form.Label({
						html: "<p style = 'color: green'>Параметр №" + (i + 1) + '</p>',
						type: 'Label'
					})
					var cbDay = new Ext.form.DateField({
						fieldLabel: 'Число',
						type: 'DateField'
					})
					var cbTime = new Ext.form.TimeField({
						fieldLabel: 'Время',
						type: 'TimeField'
					})
					items.push(label)
					items.push(cbDay)
					items.push(cbTime)
				}
			}
			else if(cbMainValue == 'месяц')
			{
				for(var i = 0; i < nfMainValue; i++)
				{
					var label = lMain = new Ext.form.Label({
						html: "<p style = 'color: green'>Параметр №" + (i + 1) + '</p>',
						type: 'Label'
					})
					var cbDay = new Ext.form.NumberField({
						fieldLabel: 'Число',
						value: 1,
						maxValue: 31,
						minValue: 1,
						type: 'NumberField'
					})
					var cbTime = new Ext.form.TimeField({
						fieldLabel: 'Время',
						type: 'TimeField'
					})
					items.push(label)
					items.push(cbDay)
					items.push(cbTime)
				}
			}
			else if(cbMainValue == 'неделю')
			{
				for(var i = 0; i < nfMainValue; i++)
				{
					var label = lMain = new Ext.form.Label({
						html: "<p style = 'color: green'>Параметр №" + (i + 1) + '</p>',
						type: 'Label'
					})
					var cbWeakDay = new Ext.form.ComboBox({
						fieldLabel: 'День недели',
						store: ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'],
						editable: true,
						mode: 'remote',
						forceSelection: true,
						triggerAction: 'all',
						selectOnFocus: true,
						type: 'ComboBox'
					})
					var cbTime = new Ext.form.TimeField({
						fieldLabel: 'Время',
						type: 'TimeField'
					})
					items.push(label)
					items.push(cbWeakDay)
					items.push(cbTime)
				}
			}
			else if(cbMainValue == 'день')
			{
				for(var i = 0; i < nfMainValue; i++)
				{
					var label = lMain = new Ext.form.Label({
						html: "<p style = 'color: green'>Параметр №" + (i + 1) + '</p>',
						type: 'Label'
					})
					var cbTime = new Ext.form.TimeField({
						fieldLabel: 'Время',
						type: 'TimeField'
					})
					items.push(label)
					items.push(cbTime)
				}
			}
			window.form2Items = items
			
			var form2 = new Ext.FormPanel({
				labelWidth: 100,
				name: 'form2',
				frame:false,
				bodyStyle:'padding:5px 5px 0',
				labelAlign: 'left',
				items: items
			});
			
			form.setVisible(false)
			
			win.add(form2)
			
			win.hide()
			win.show()
			
			win.buttons[0].setVisible(false)
			win.buttons[1].setVisible(true)
		}
	},{
		text: 'Готово',
		hidden: true,
		handler: function()
		{
			var id = window.market_id
			var tmp = {}
			var params = []
			if(paramsArray['interval']!='час')
			{
				for(var i=0;i<window.form2Items.length;i++)
				{
					if(window.form2Items[i].type == 'Label' && i!=0)
					{
						params.push(tmp)
						tmp = {}
						continue
					}
					else if(window.form2Items[i].type == 'DateField')
					{
						tmp['date'] = window.form2Items[i].getValue()
						continue
					}
					else if(window.form2Items[i].type == 'TimeField')
					{
						tmp['time'] = window.form2Items[i].getValue()
						continue
					}
					else if(window.form2Items[i].type == 'NumberField')
					{
						tmp['day'] = window.form2Items[i].getValue()
						continue
					}
					else if(window.form2Items[i].type == 'ComboBox')
					{
						tmp['dayOfWeak'] = window.form2Items[i].getValue()
						continue
					}
				}
				params.push(tmp)
				tmp = {}
			}
			paramsArray['Params'] = params
			form.setVisible(true)
			win.remove(win.items.items[1])
			win.hide()
			win.buttons[0].setVisible(true)
			win.buttons[1].setVisible(false)
			
			Ext.Ajax.request({
				url: '/parser_settins/set_time_settings',
				params: { params: Ext.util.JSON.encode(paramsArray), market_id: id}
			}); 
		}
	},{
		text: 'Отменить',
		handler: function()
		{
			form.setVisible(true)
			win.remove(win.items.items[1])
			win.hide()
			win.buttons[0].setVisible(true)
			win.buttons[1].setVisible(false)
		}
	}]
});
win.setAutoScroll(true)
});
