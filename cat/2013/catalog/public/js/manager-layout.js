//Ext.require(['*']);

Ext.onReady(function() {
	Ext.QuickTips.init();

	/////////////////////////////////////// HERE TRY TO GET THE CHECK COLUMN GET TO WORK /////////////////////////////
	Ext.ns('Ext.ux.grid');
	Ext.ux.grid.CheckColumn = Ext.extend(Ext.grid.Column, {

		/**
		 * @private
		 * Process and refire events routed from the GridView's processEvent method.
		 */
		processEvent : function(name, e, grid, rowIndex, colIndex){
		    e.stopEvent();
		    this.fireEvent('edit');
		    if (name == 'mousedown') {
			var record = grid.store.getAt(rowIndex);
			record.set(this.dataIndex, !record.data[this.dataIndex]);
			grid.fireEvent('afteredit', {
				grid : grid,
				    record : record,
				    field : this.name || this.dataIndex,
				    value : record.data[this.dataIndex],
				    originalValue : !record.data[this.dataIndex],
				    row : rowIndex,
				    column : colIndex
				    });
			return false; // Cancel row selection.
		    } else {
			return Ext.grid.ActionColumn.superclass.processEvent.apply(this, arguments);
		    }

		},

		renderer : function(v, p, record){
		    p.css += ' x-grid3-check-col-td'; 
		    return String.format('<div class="x-grid3-check-col{0}">&#160;</div>', v ? '-on' : '');
		},

		init: Ext.emptyFn
	    });

	Ext.preg('checkcolumn', Ext.ux.grid.CheckColumn);

	Ext.grid.CheckColumn = Ext.ux.grid.CheckColumn;

	// register Column xtype
	Ext.grid.Column.types.checkcolumn = Ext.ux.grid.CheckColumn; 
	///////////////////////////////////////// DO NOT KNOW HOW, BUT WORKED ///////////////////////////////////////////


	var Tree = Ext.tree;

	// var tree_store = new Ext.data.JsonStore({
		

	//     });


	var tree = new Tree.TreePanel({
		height: 850,
		useArrows: true,
		autoScroll: true,
		animate: true,
		enableDD: false,
		containerScroll: true,
		border: true,
		dataUrl: '/manager/tree',
		id: 'tree',
		autoDestroy: true,
		root: {
		    nodeType: 'async',
		    text: 'Категории',
		    draggable: false,
		    display: false,
		    id: '0'
		}
	    });

	tree.getRootNode().expand();

	var parent_category_tree = new Tree.TreePanel({
		bodyBorder: false,
		border: false,
		height: 100,
		useArrows: true,
		autoScroll: true,
		autoDestroy: true,
		animate: true,
		enableDD: false,
		border: true,
		dataUrl: '/manager/tree',
		id: 'parent-tree',
		root: {
		    nodeType: 'async',
		    text: 'Родительская категория',
		    display: false,
		    draggable: false,
		    id: '0'
		},
	    });
	parent_category_tree.root.expand();

	//init the store with sites in category
	var sites_store = new Ext.data.JsonStore({
		fields: ['id',
			 'category_id',
			 'name_ru',
			 'name_uk', 
			 'name_en', 
			 'date_add',
			 'description_ru',
			 'description_uk',
			 'description_en',
			 'avaible',
			 'checked',
			 'rate',
			 'owners_mail',
			 'reference',
			 'last_checked'],
		autoDestroy: false,
		pageSize: 40,
		root: 'sites',
		proxy: new Ext.data.HttpProxy({
			url: '/manager/sites/'}),
	    });

	//defining the columns of the grid and them editors
	var columns = new Ext.grid.ColumnModel({
		defaults: {sortable: true},
		columns: [
	{id: 'del_btn',
	 header: 'Отметить на удаление',
	 dataIndex: 'del_select',
	 xtype: 'checkcolumn',
	 editor: new Ext.form.Checkbox({})
	},
	{id: 'owners_mail',
	 header: 'Ел. почта',
	 dataIndex: 'owners_mail',
	 editor: new Ext.form.TextArea({allowBlank: false, vtype: 'email'})
	},
	{id: 'reference',
	 header: 'Ссылка на сайт',
	 dataIndex: 'reference',
	 editor: new Ext.form.TextArea({allowBlank: false, vtype: 'url'})
	},
	{id: 'name_uk',
	 header: 'Украинское имя',
	 dataIndex: 'name_uk',
	 editor: new Ext.form.TextArea({allowBlank: false})
	},
	{id: 'name_ru',
	 header: 'Русское имя',
	 dataIndex: 'name_ru',
	 editor: new Ext.form.TextArea({allowBlank: false})
	},
	{id: 'name_en',
	 header: 'Английское имя',
	 dataIndex: 'name_en',
	 width: 100,
	 editor: new Ext.form.TextArea({allowBlank: false})
	},
	{id: 'description_uk',
	 header: 'Украинское описание',
	 dataIndex: 'description_uk',
	 width: 200,
	 editor: new Ext.form.TextArea({allowBlank: false, width: 200})
	},
	{id: 'description_ru',
	 header: 'Русское описание',
	 dataIndex: 'description_ru',
	 width: 200,
	 editor: new Ext.form.TextArea({allowBlank: false, width: 250, height: 150})
	},
	{id: 'description_en',
	 header: 'Английское описание',
	 dataIndex: 'description_en',
	 width: 200,
	 editor: new Ext.form.TextArea({allowBlank: false})
	},
	{id: 'category_id',
	 header: 'Категория',
	 dataIndex: 'category_id',
	 width: 100,
	 editor: new Ext.form.ComboBox({store: new Ext.data.ArrayStore({
			 fields: ['id','title'],
			 root: 'leafs',
			 url: '/manager/get_leaf_categories',
			 autoLoad: true}),
					valueField: 'id',
					displayField: 'title',
					editable: false})},
	{id: 'avaible',
	 header: 'Доступен',
	 dataIndex: 'avaible',
	 width: 60,
	 xtype: 'checkcolumn',
	 editor: new Ext.form.Checkbox({allowBlank: false})
	},
	{id: 'checked',
	 header: 'Проверен',
	 dataIndex: 'checked',
	 width: 60,
	 xtype: 'checkcolumn',
	 editor: new Ext.form.Checkbox({allowBlank: false})
	},
	{id: 'date-add',
	 header: 'Дата добавления',
	 dataIndex: 'date_add',
	 xtype: 'datecolumn',
	 width: 60,
	 editable: false,
	 editor: new Ext.form.DateField({allowBlank: false, format: 'y-m-d'})
	},
	{id: 'last_checked',
	 header: 'Дата последней проверки',
	 dataIndex: 'last_checked',
	 width: 60,
	 xtype: 'datecolumn',
	 editable: false,
	 editor: new Ext.form.DateField({allowBlank: false, format: 'y-m-d'})
	}

			  ]
	    }
	    );

	//init the window with the user edition
	var usr_window = new Ext.Window({
		id: 'usr_wnd',
		name: 'usr_wnd',
		title: 'Редактирование пользователя',
		autoWidth: true,
		autoHeight: true,
		bodyBorder: true,
		closeAction: 'hide',
		layout: 'table',
		hidden: true, // for preloading components
		layoutConfig: {columns: 3},
		items: [{colspan: 3,
			 xtype: 'form',
			 id: 'usr_form',
			 items: [{xtype: 'textfield',
				  name: 'user_name',
				  fieldLabel: "Имя пользователя",
				  width: 150
			    },{xtype: 'textfield',
			       name: 'password',
			       width: 150,
			       fieldLabel: "Пароль"
			    },{xtype: 'checkbox',
			       name: 'is_adm',
			       fieldLabel: "Право редактирования пользователей",
			    }]},
	{xtype: 'button',
	 name: 'save_usr_btn',
	 text: 'Сохранить пользователя',
	 handler: function (){Ext.getCmp("usr_form").getForm().submit({url: '/manager/add_usr',
								       success: function(){Ext.getCmp("usr_form").getForm().reset();}})}},
	{xtype: 'button',
	 name: 'update_usr_btn',
	 text: 'Обновить пользователя',
	 handler: function (){Ext.getCmp("usr_form").getForm().submit({url: '/manager/upd_usr',
								       success: function(){Ext.getCmp("usr_form").getForm().reset();}})}},
	{xtype: 'button',
	 name: 'delete_usr_btn',
	 text: 'Удалить пользователя',
	 handler: function (){Ext.getCmp("usr_form").getForm().submit({url: '/manager/rem_usr',
								       success: function(){Ext.getCmp("usr_form").getForm().reset();}});
			      }}
		    ]

	    });

	//user edition toolbar
	var usr_toolbar = new Ext.Toolbar({
		// default is hidden for users with no privelegies
		items: [{xtype: 'button',
			 id: 'usr_wnd_btn',
			 hidden: true,
			 text: 'Редактировать пользователей',
			 name: 'usr_wnd_btn',
			 handler: function(){usr_window.show();}
		    },'->',{xtype: 'button',
			    id: 'logout_btn',
			    text: 'Выйти',
			    name: 'logout_btn',
			    handler: function(){window.location='/manager/logout';}
		    }]
	    });

	// getting rights
	Ext.Ajax.request({url: '/manager/get_rights', method: 'POST',
		    success: function (a){
		    if (JSON.parse(a.responseText).is_adm == true){
			Ext.getCmp('usr_wnd_btn').show();// show toolbar when user can edit other users
		    }
		}
	    });
	


	//the grid toolbar
	var filter_toolbar = new Ext.Toolbar({
		items: [{xtype: 'button',
			 id: 'filter_btn',
			 text: 'Установить фильтр',
			 name: 'filter_btn'},{
			xtype: 'button',
			id: 'add_site_btn',
			text: 'Добавить сайт',
			name: 'add_site_btn',
			handler: function(){
			    var row = Ext.data.Record.create(['id',
							      'category_id',
							      'name_ru',
							      'name_uk', 
							      'name_en', 
							      'date_add',
							      'description_ru',
							      'description_uk',
							      'description_en',
							      'avaible',
							      'checked',
							      'rate',
							      'owners_mail',
							      'reference',
							      'last_checked']);
			    Ext.Ajax.request({url: '/manager/new_site_id',
					success: function(a){
					grid.store.add(new row({id: JSON.parse(a.responseText).id, 
							category_id: 101, 
							reference: 'http://example.com', 
							date_add: new Date(), 
							last_checked: new Date(),
							name_ru:'',
							name_uk:'',
							name_en:'',
							description_ru:'',
							description_uk:'',
							description_en:'',
							avaible:false,
							checked:false,
							owners_mail: 'your@yottos.com',
							rate: 0
							}));
				    }	
				});
			}
		    },{
			xtype: 'button',
			id: 'del_site_btn',
			text: 'Удалить выбранные сайты',
			handler: function(){
			    grid.store.each(function(rec){
				    if(rec.data.del_select == true){
					Ext.Ajax.request({url: '/manager/del_site', method: 'POST', params: rec.data});
				    }
				    grid.store.reload();
				});
			}
		    }]
	    });


	//init window with filters form
	var filter_window = new Ext.Window({
		id: 'filter_wnd',
		name: 'filter_wnd',
		title: 'Установите фильтры',
		height: 300,
		width: 480,
		bodyBorder: true,
		closeAction: 'hide',
		html: '<div id="filter-div"></div>'
	    });

	//init form with current category info and the buttons for deletion and adding inner info as new category
	var category_form = new Ext.form.FormPanel({
		height: '100%',
		autoScroll: true,
		reader: new Ext.data.JsonReader({
			idProperty: 'id',
			root: 'category',
			bodyBorder: false,
			results: 1,
			fields: ['id','html_title','title','title_ru','title_en','title_uk','slug','parent_id','is_leaf','keywords','description','banner_script']
		    }),
		items: [
	{xtype: 'hidden',
	 name: 'id'},
	{xtype: 'textfield',
	 width: 300,
	 labelStyle: 'width: 200px;',
	 name: 'title',
	 hideLabel: false,
	 fieldLabel: 'Название по умолчанию'},
	{xtype: 'textfield',
	 labelStyle: 'width: 200px;',
	 width: 300,
	 name: 'html_title',
	 hideLabel: false,
	 fieldLabel: 'Заголовок категории'},
	{xtype: 'textfield',
	 labelStyle: 'width: 200px;',
	 width: 300,
	 name: 'title_ru',
	 hideLabel: false,
	 fieldLabel: 'Русское название'},
	{xtype: 'textfield',
	 labelStyle: 'width: 200px;',
	 width: 300,
	 name: 'title_en',
	 hideLabel: false,
	 fieldLabel: 'Английское название'},
	{xtype: 'textfield',
	 labelStyle: 'width: 200px;',
	 width: 300,
	 name: 'title_uk',
	 hideLabel: false,
	 fieldLabel: 'Украинское название'},
	{xtype: 'textfield',
	 labelStyle: 'width: 200px;',
	 name: 'slug',
	 width: 300,
	 hideLabel: false,
	 fieldLabel: 'Путь к категории'},
	{xtype: 'textarea',
	 labelStyle: 'width: 200px;',
	 width: 300,
	 name: 'keywords',
	 hideLabel: false,
	 fieldLabel: 'Ключевые слова'
	},
	{xtype: 'textarea',
	 labelStyle: 'width: 200px;',
	 width: 300,
	 name: 'description',
	 hideLabel: false,
	 fieldLabel: 'Описание'
	},
	{xtype: 'textarea',
	 labelStyle: 'width: 200px;',
	 width: 300,
	 name: 'banner_script',
	 hideLabel: false,
	 fieldLabel: 'Скрипт баннера'
	},
	{xtype: 'checkbox',
	 labelStyle: 'width: 200px;',
	 name: 'is_leaf',
	 hideLabel: false,
	 fieldLabel: 'Возможность добавления сайтов',
	 text: 'Add sites',
	 editable: false,
	},
	{xtype: 'hidden',
	 name: 'parent_id',
	},
	[{xtype: 'button',
	  text: 'Сохранить изменения',
	  handler: function(){
		    category_form.getForm().submit({url: '/manager/save_category', waitMsg: 'Saving changes...',
						    success: function(){
				tree.getRootNode().reload();
				parent_category_tree.getRootNode().reload();
				category_form.getForm().reset();
			    }
			});
		
		}
	    },
	{xtype: 'button',
	 text: 'Сохранить как новую категорию',
	 handler: function() {
		category_form.getForm().submit({url: '/manager/add_category', waitMsg: 'Adding category...',
						success: function(){
			    tree.getSelectionModel().getSelectedNode().reload();
			    tree.getRootNode().reload();
			    parent_category_tree.getRootNode().reload();
			    category_form.getForm().reset();
			}
		    });
	    }
	},
	{xtype: 'button',
	 text: 'Удалить категорию',
	 handler: function(){
		category_form.getForm().submit({url: '/manager/del_category', waitMsg: 'Removing category...',
						success: function(){
			    tree.getRootNode().reload();
			    parent_category_tree.getRootNode().reload();	
			    category_form.getForm().reset();		
			}
		    });
	    }
	}]]
	    });
	
	// init grid with sites in selected category
	var grid = new Ext.grid.EditorGridPanel({
		autoScroll: true,
		id: 'sites-grid',
		width: '100%',
		height: '70%',
		anchor: '100% 100%',
		view: new Ext.grid.GridView({
			forceFit: true,
		    }),
		resizeble: true,
		store: sites_store,
		cm: columns,
		title: 'Сайты в категории',
		frame: false,
		clicksToEdit: 1,
		tbar: filter_toolbar,
		bbar: new Ext.PagingToolbar({pageSize: 40,
					     store: sites_store,
					     displayInfo: true,
					     displayMsg: 'Показано {0} - {1} из {2}',
					     emptyMsg: 'No sites in category'
					     
		    })});
	

	// form with the filter elements
	var filter_form = new Ext.form.FormPanel({
		id: 'filter_form',
		name: 'filter_form',
		items: [{
			xtype: 'checkbox',
			name: 'checked',
			hideLabel: false,
			fieldLabel: 'Проверен',
			data: false
		    },{
			xtype: 'checkbox', 
			name: 'avaible',
			hideLabel: false,
			fieldLabel: 'Доступен',
			data: false
		    },{
			xtype: 'textfield',
			name: 'owners_mail',
			hideLabel: false,
			fieldLabel: 'Ел. почта',
			vtype: 'email'
		    },{
			xtype: 'textfield',
			name: 'reference',
			hideLabel: false,
			fieldLabel: 'Ссылка',
			vtype: 'url'
		    },{
			xtype: 'datefield',
			name: 'date_add_start',
			hideLabel: false,
			fieldLabel: 'Добавленые с',
			format: 'd-m-Y'
		    },{
			xtype: 'datefield',
			name: 'date_add_end',
			hideLabel: false,
			fieldLabel: 'по',
			format: 'd-m-Y'
		    },{
			xtype: 'button',
			text: 'Установить',
			handler: function(){
			    filter_form.getForm().submit({url: '/manager/set_filter_sites',
							  success: function(f,a){
					sites_store.proxy = new Ext.data.HttpProxy({
						url: '/manager/get_filter_sites'});
					sites_store.reload({params:{start:0,limit:40}});
				    }
				});
			}
		    }
		    ]
	    });

	
	// selecting the categorys parent from tree(as click event) 
	parent_category_tree.on('click', function(){
		category_form.getForm().findField('parent_id').setValue(Ext.getCmp('parent-tree').getSelectionModel().getSelectedNode().attributes.id);
	    });

	//auto updating the sites edited data
	grid.on('afteredit', function(object){
		var row_data = object.record.data;
		Ext.Ajax.request({
			url: '/manager/save_site',
			    method: 'POST',
			    params: row_data
			    });
	    });

	//click button to show the window with filters 
	Ext.getCmp('filter_btn').on('click', function(){
		filter_window.show();
		filter_form.render('filter-div');
	    });

	//setting up the layout
	var viewport = new Ext.Viewport({
		layout: {type: 'border',
			 padding: 5},
		defaults: {
		    split: true
		},
		items: [{region: 'center',
			 collapsible: false,
			 //title: 'Edit category',
			 split: true,
			 height: '50%',
			 width: '80%',
			 minHeight: 200,
			 minWidth: 200,
			 layout: {type: 'border',
				  padding: 5},
			 items: [{region: 'south',
				  collapsible: true,
				  split: true,
				  height: 580,
				  minHeight: 200,
				  minWidth: 200,
				  layout: 'fit',
				  items: [grid]
			    },
	{region: 'center',
	 zoom: 1,
	 collapsible: true,
	 title: 'Редактирование категории',
	 split: true,
	 height: 420,
	 minHeight: 200,
	 minWidth: 200,
	 layout: 'fit',
	 tbar: usr_toolbar,
	 items: [{layout: 'border',
		  autoScroll: true,
		  width: '100%',
		  height: '100%',
		  items:[{  region: 'west',
			    autoScroll: true,
			    width: '65%',
			    height: '100%',
			    split: false,
			    layout: 'fit',
			    items: [category_form]
			},{
			    region: 'center',
			    autoScroll: true,
			    width: '35%',
			    height: '100%',
			    split: false,
			    layout: 'fit',
			    items: [parent_category_tree]}]
		}]
	}]},
		    
	{region: 'west',
	 collapsible: true,
	 title: 'Дерево категорий',
	 split: true,
	 height: '100%',
	 width: '20%',
	 minHeight: 200,
	 minWidth: 200,
	 layout: 'fit',
	 items: [tree]
	}
		    ]});	

	//catching event for selecting the sites in clicked category and filling the category form
	tree.on('click', function(){
		tree.render();
		sites_store.proxy = new Ext.data.HttpProxy({url: '/manager/sites/' + Ext.getCmp('tree').getSelectionModel().getSelectedNode().attributes.id,
							    params:{start:0,limit:40}});

		grid.store = sites_store;
	 	sites_store.reload({params:{start:0,limit:40}});
		category_form.getForm().load({url:'/manager/get_category?id=' + Ext.getCmp('tree').getSelectionModel().getSelectedNode().attributes.id, 
			    waitMsg: 'Loading...',
			    success: function(){parent_category_tree.root.cascade(
										  function (node){
										      if(node.id == category_form.getForm().getValues().parent_id){node.select();node.expand();}
										      else{node.expand();}
										  });
			}});
		grid.doLayout();
	    });

	parent_category_tree.getRootNode().select();

    });